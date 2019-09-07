from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.sql import text

from sqlalchemy.orm import sessionmaker
from geoalchemy2 import WKTElement, Geometry
import geopandas as gpd

from data_resources import fileToObjects

# Referenced from: https://automating-gis-processes.github.io/CSC/notebooks/L2/data_io.html


server_settings = fileToObjects.open_json_file('backend/server_settings.json')["PostGis"]
db_url = URL(drivername=server_settings["driver_name"],
             host=server_settings["host"],
             database=server_settings["db"],
             username=server_settings["user"],
             port=server_settings["port"])


class PostGisHandler:

    def __init__(self) -> None:
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

    def select_from_table(self, table_name, where=None):
        if table_name not in self.engine.table_names(schema=self.schema):
            print('No table name', table_name, "in", self.engine.table_names(schema=self.schema))
        session = self.Session()
        sql = "SELECT * FROM {0}.{1}".format(self.schema, table_name)
        if where is not None:
            sql += " WHERE " + where
        sql += ";"
        # Pull the data
        data = gpd.read_postgis(sql=sql, con=self.engine)
        session.close()
        return data

    def st_MakeEnvelope(self, bounds, crs, index):
        return "ST_MakeEnvelope ({0}, {1},{2}, {3}, {4})".format(bounds["minx"][index],
                                                                 bounds["miny"][index],
                                                                 bounds["maxx"][index],
                                                                 bounds["maxy"][index],
                                                                 crs)

    def get_envelope(self, table_name, bounds, crs, zoom_level, all_higher_levels=False,
                     type_of_intersection="intersects", has_depth=False):
        if table_name not in self.engine.table_names(schema=self.schema):
            print('No table name', table_name, "in", self.engine.table_names(schema=self.schema))
            return None
        type_of_intersect = {"intersects": "&&", "contained": "@", "contains": "~"}
        if all_higher_levels:
            comp_operator = '>='
        else:
            comp_operator = '='
        select_from = "SELECT * FROM {0}.{1} ".format(self.schema, table_name)
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
        sql = select_from + where_zoom_level + bounds_query
        print('get_envelope')
        if has_depth:
            sql += "AND depth is NOT NULL"
        session = self.Session()

        print(sql)
        # Pull the data
        data = gpd.read_postgis(sql=sql, con=self.engine)
        session.close()
        print('session close')
        return data

    def update_point_height(self, table_name, point, crs, depth):
        if table_name not in self.engine.table_names(schema=self.schema):
            print('No table name', table_name, "in", self.engine.table_names(schema=self.schema))
            return None
        wkt_point = WKTElement(point.wkt, srid=crs)
        update = f"UPDATE {self.schema}.{table_name} " \
                 f"SET depth = {depth} " \
                 f"WHERE geom = 'SRID={crs};{wkt_point}'::geometry;"
        print(update)
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
