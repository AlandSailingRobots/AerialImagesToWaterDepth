import sys
from time import sleep

import geopandas as gpd

from backend.ConvolutionalNeuralNetworkHandler import ConvolutionalHandler
from backend.PostGisHandler import PostGisHandler

cnn = ConvolutionalHandler()
postGis = PostGisHandler()


# update single
# WHERE name = 'Point' and geom = 'SRID=4326;POINT(0 0)'::geometry;

def calculate_per_single_point_update_database(crs, geo_list):
    for geo_ in geo_list:
        depths = cnn.predict_point(geo_, crs)
        splitted = crs.split(':')[-1]
        postGis.update_point_height(postGis.points_table, geo_, splitted, depths.flatten()[0])
        # post_points(depths, crs, [geo_])


def post_points(self, depths, crs, geo_):
    points_df = gpd.GeoDataFrame(
        {'zoom_level': [self.jsonData["zoom"]] * len(geo_), 'depth': depths.flatten(),
         'geometry': geo_})
    points_df.crs = crs
    postGis.put_into_table(points_df, "Point", 'test.points', create_table=True,
                           if_exists_action='append')


while True:
    df = postGis.select_from_table(postGis.points_table, where="depth is NULL")
    if len(df) > 0:
        calculate_per_single_point_update_database(df.crs['init'], df.geometry)
    else:
        print('No empty points')
        sleep(10)
