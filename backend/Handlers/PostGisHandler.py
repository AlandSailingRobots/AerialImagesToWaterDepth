import json

import pandas as pd
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.sql import text

from sqlalchemy.orm import sessionmaker
from geoalchemy2 import WKTElement, Geometry
import geopandas as gpd

from data_resources import fileToObjects

# Referenced from: https://automating-gis-processes.github.io/CSC/notebooks/L2/data_io.html


server_settings = fileToObjects.open_json_file('server_settings.json')["PostGis"]
db_url = URL(drivername=server_settings["driver_name"],
             host=server_settings["host"],
             database=server_settings["db"],
             username=server_settings["user"],
             port=server_settings["port"])


class PostGisHandler(object):

    calculation_table: str
    points_table: str
    polygon_table: str
    schema: str
    Session: sessionmaker

    def __init__(self) -> None:
        super().__init__()
        self.engine = create_engine(db_url)
        try:
            self.engine.connect()
        except:
            print("No Connection To Database")
            raise
        # Init Metadata
        meta = MetaData()

        # Load table definitions from db
        meta.reflect(self.engine)

        # Create session
        self.Session = sessionmaker(bind=self.engine)
        self.schema = server_settings['schema']
        self.polygon_table = server_settings['polygon']
        self.points_table = server_settings['point']
        self.calculation_table = server_settings['calculation']

    def select_from_table(self, table_name, where=None,limit=None, panda=False):
        if table_name not in self.engine.table_names(schema=self.schema):
            print('No table name', table_name, "in", self.engine.table_names(schema=self.schema))
        session = self.Session()
        sql = "SELECT * FROM {0}.{1}".format(self.schema, table_name)
        if where is not None:
            sql += " WHERE " + where
        if limit is not None:
            sql += " limit {0}".format(limit)
        sql += ";"
        # Pull the data
        if not panda:
            data = gpd.read_postgis(sql=sql, con=self.engine)
        else:
            data = pd.read_sql_query(sql=sql, con=self.engine)
        session.close()
        return data

    def put_into_calculation(self, jsonData):
        insert = """INSERT INTO {0}.{1} (payload) VALUES ('{2}')""".format(self.schema, self.calculation_table,
                                                                           json.dumps(jsonData))
        print(insert)
        self.send_to_db(insert)

    def st_MakeEnvelope(self, bounds, crs, index):
        return "ST_MakeEnvelope ({0}, {1},{2}, {3}, {4})".format(bounds["minx"][index],
                                                                 bounds["miny"][index],
                                                                 bounds["maxx"][index],
                                                                 bounds["maxy"][index],
                                                                 crs)

    def get_envelope(self, table_name, bounds, crs, zoom_level, all_higher_levels=False,
                     type_of_intersection="intersects", has_depth=False, as_buffer=None, extra=None):
        if table_name not in self.engine.table_names(schema=self.schema):
            print('No table name', table_name, "in", self.engine.table_names(schema=self.schema))
            return None
        type_of_intersect = {"intersects": "&&", "contained": "@", "contains": "~"}
        if all_higher_levels:
            comp_operator = '>='
        else:
            comp_operator = '='

        operator = "*" if as_buffer is None else as_buffer
        select_from = f"SELECT {operator} FROM {self.schema}.{table_name} "
        where_zoom_level = "WHERE zoom_level {0} {1} ".format(comp_operator, zoom_level)
        bounds.reset_index(inplace=True)
        bounds_query = ""
        if len(bounds) is 0:
            print('Something wrong')
        else:
            bounds_query = "AND ("

        bounds_list_query = []
        for index in range(len(bounds)):
            geom = "geom {0} ".format(type_of_intersect[type_of_intersection])
            envelope = self.st_MakeEnvelope(bounds, crs, index)
            bounds_list_query.append(geom + envelope)
        if len(bounds_list_query) > 1:
            temp_string = " OR ".join(bounds_list_query)
            bounds_query += (temp_string + ")")
        else:
            bounds_query += bounds_list_query[0] + ")"
        sql = select_from + where_zoom_level
        print('get_envelope')
        if has_depth:
            sql += "AND depth is NOT NULL "
        if extra is not None:
            sql += extra
        sql += "AND ST_IsValid(geom) "
        sql += bounds_query
        print(sql)
        session = self.Session()

        # Pull the data
        data = gpd.read_postgis(sql=sql, con=self.engine)
        session.close()
        print('session close')
        return data

    def update_calculation(self, index):
        update = f"UPDATE {self.schema}.{self.calculation_table} " \
                 f"SET calculated = TRUE " \
                 f"WHERE index_key = {index}"
        self.send_to_db(update)

    def update_point_height(self, table_name, id, depth, return_query=False):
        if table_name not in self.engine.table_names(schema=self.schema):
            print('No table name', table_name, "in", self.engine.table_names(schema=self.schema))
            return None
        update = f"UPDATE {self.schema}.{table_name} " \
                 f"SET depth = {depth} " \
                 f"WHERE identifier = {id}"
        if return_query:
            return update
        self.send_to_db(update)

    def send_to_db(self, update):
        session = self.Session()
        session.execute(text(update))
        session.commit()
        session.close()

    def put_into_table(self, data, geometry_type, table_name, crs=None, create_table=False, if_exists_action='replace'):
        if table_name not in self.engine.table_names(schema=self.schema) and create_table is not False:
            print('No table name', table_name, "in", self.engine.table_names(schema=self.schema))
        if crs is None:
            if type(data.crs) is dict:
                crs = int(data.crs['init'].split(':')[1])
            else:
                crs = int(data.crs.split(':')[1])
            # Convert Shapely geometries to WKTElements into column 'geom' (default in PostGIS)
        print(data.columns)
        checking_name = 'geometry'
        applied_name = 'geom'
        if checking_name not in list(data.columns):
            checking_name = list(data.columns)[-1]
        data[applied_name] = data[checking_name].apply(lambda row: WKTElement(row.wkt, srid=crs))

        if checking_name != applied_name:
            # Drop Shapely geometries
            data = data.drop(checking_name, axis=1)

        # Write to PostGIS (overwrite if table exists, be careful with this! )
        # Possible behavior: 'replace', 'append', 'fail'
        session = self.Session()
        data.to_sql(table_name, self.engine, schema=self.schema, if_exists=if_exists_action, index=False,
                    dtype={'geom': Geometry(geometry_type=geometry_type, srid=crs)})
        session.close()
        print('Session Closed')
