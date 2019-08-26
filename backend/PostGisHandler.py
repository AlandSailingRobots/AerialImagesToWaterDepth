from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine
from sqlalchemy import MetaData

from sqlalchemy.orm import sessionmaker
from geoalchemy2 import WKTElement, Geometry
import geopandas as gpd

from data_resources import fileToObjects

# Source: https://automating-gis-processes.github.io/CSC/notebooks/L2/data_io.html


server_settings = fileToObjects.open_json_file('backend/server_settings.json')["PostGis"]
db_url = URL(drivername=server_settings["driver_name"], host=server_settings["host"], database=server_settings["db"],
             username=server_settings["user"], port=server_settings["port"])


class PostGisHandler:

    def __init__(self) -> None:
        self.engine = create_engine(db_url)

        # Init Metadata
        meta = MetaData()

        # Load table definitions from db
        meta.reflect(self.engine)

        # Create session
        self.Session = sessionmaker(bind=self.engine)

    def select_all_from_table(self, table_name):
        if table_name not in self.engine.table_names():
            print('No table name', table_name, "in", self.engine.table_names())
        session = self.Session()
        sql = "SELECT * FROM {0};".format(table_name)

        # Pull the data
        data = gpd.read_postgis(sql=sql, con=self.engine)
        session.close()
        return data

    def get_envelope(self, table_name, bounds, crs, type_of_intersection="intersects"):
        if table_name not in self.engine.table_names():
            print('No table name', table_name, "in", self.engine.table_names())
        type_of_intersect = {"intersects": "&&", "contained": "@", "contains": "`~"}
        session = self.Session()
        sql = "SELECT * FROM   my_table WHERE  coordinates {0} ST_MakeEnvelope ( {1}, {2},{3}, {4}, {5})".format(
            type_of_intersect[type_of_intersection], bounds["xmin"], bounds["ymin"], bounds["xmax"], bounds["ymax"],
            crs)

        # Pull the data
        data = gpd.read_postgis(sql=sql, con=self.engine)
        session.close()
        return data

    def put_into_table(self, data, geometry_type, table_name, crs=None):
        if table_name not in self.engine.table_names():
            print('No table name', table_name, "in", self.engine.table_names())
        if crs is None:
            crs = int(data.crs['init'].split(':')[1])
        # Convert Shapely geometries to WKTElements into column 'geom' (default in PostGIS)
        data['geom'] = data['geometry'].apply(lambda row: WKTElement(row.wkt, srid=crs))

        # Drop Shapely geometries
        data = data.drop('geometry', axis=1)

        # Write to PostGIS (overwrite if table exists, be careful with this! )
        # Possible behavior: 'replace', 'append', 'fail'
        session = self.Session()
        data.to_sql(table_name, self.engine, if_exists='replace', index=False,
                    dtype={'geom': Geometry(geometry_type=geometry_type, srid=crs)})
        session.close()
