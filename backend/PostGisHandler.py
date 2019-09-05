from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine
from sqlalchemy import MetaData

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

    def select_all_from_table(self, table_name):
        if table_name not in self.engine.table_names(schema=self.schema):
            print('No table name', table_name, "in", self.engine.table_names(schema=self.schema))
        session = self.Session()
        sql = "SELECT * FROM {0}.{1};".format(self.schema,table_name)

        # Pull the data
        data = gpd.read_postgis(sql=sql, con=self.engine)
        session.close()
        return data

    def get_envelope(self, table_name, bounds, crs, zoom_level, all_higher_levels=False,
                     type_of_intersection="intersects"):
        if table_name not in self.engine.table_names(schema=self.schema):
            print('No table name', table_name, "in", self.engine.table_names(schema=self.schema))
            return None
        type_of_intersect = {"intersects": "&&", "contained": "@", "contains": "~"}
        if all_higher_levels:
            comp_operator = '>='
        else:
            comp_operator = '='
        select_from = "SELECT * FROM {0}.{1} ".format(self.schema,table_name)
        where_zoom_level = "WHERE zoom_level {0} {1} ".format(comp_operator, zoom_level)
        and_geom = "AND geom {0} ".format(type_of_intersect[type_of_intersection])
        envelope = "ST_MakeEnvelope ({0}, {1},{2}, {3}, {4})".format(bounds["minx"][0],
                                                                     bounds["miny"][0],
                                                                     bounds["maxx"][0],
                                                                     bounds["maxy"][0],
                                                                     crs)
        session = self.Session()
        sql = select_from + where_zoom_level + and_geom + envelope
        print(sql)
        # Pull the data
        data = gpd.read_postgis(sql=sql, con=self.engine)
        session.close()
        print('session close')
        return data

    def put_into_table(self, data, geometry_type, table_name, crs=None, create_table=False, if_exists_action='replace'):
        if table_name not in self.engine.table_names(schema=self.schema) and create_table is not False:
            print('No table name', table_name, "in", self.engine.table_names(schema=self.schema))
        if crs is None:
            if type(data.crs) is dict:
                crs = int(data.crs['init'].split(':')[1])
            else:
                crs = int(data.crs.split(':')[1])
            # Convert Shapely geometries to WKTElements into column 'geom' (default in PostGIS)
        data['geom'] = data['geometry'].apply(lambda row: WKTElement(row.wkt, srid=crs))

        # Drop Shapely geometries
        data = data.drop('geometry', axis=1)

        # Write to PostGIS (overwrite if table exists, be careful with this! )
        # Possible behavior: 'replace', 'append', 'fail'
        session = self.Session()
        data.to_sql(table_name, self.engine,schema=self.schema, if_exists=if_exists_action, index=False,
                    dtype={'geom': Geometry(geometry_type=geometry_type, srid=crs)})
        session.close()
        print('Session Closed')
