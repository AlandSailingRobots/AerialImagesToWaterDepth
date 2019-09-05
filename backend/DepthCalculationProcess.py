from time import sleep

from backend.ConvolutionalNeuralNetworkHandler import ConvolutionalHandler
from backend.PostGisHandler import PostGisHandler

cnn = ConvolutionalHandler()
postGis = PostGisHandler()


def calculate_per_single_point_update_database(crs, geo_list):
    for geo_ in geo_list:
        depths = cnn.predict_point(geo_, crs)
        splitted = crs.split(':')[-1]
        postGis.update_point_height(postGis.points_table, geo_, splitted, depths.flatten()[0])


while True:
    df = postGis.select_from_table(postGis.points_table, where="depth is NULL")
    if len(df) > 0:
        calculate_per_single_point_update_database(df.crs['init'], df.geometry)
    else:
        print('No empty points')
        sleep(30)
