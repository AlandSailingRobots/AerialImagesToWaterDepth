from time import sleep

from backend.ConvolutionalNeuralNetworkHandler import ConvolutionalHandler
from backend.PostGisHandler import PostGisHandler

cnn = ConvolutionalHandler(2)
postGis = PostGisHandler()


def calculate_per_single_point_update_database(crs, df):
    for index, item in df.iterrows():
        depths = cnn.predict_point(item.geom, crs)
        splitted = crs.split(':')[-1]
        postGis.update_point_height(postGis.points_table, item.geom, splitted, depths.flatten()[0], item.zoom_level)


while True:
    df = postGis.select_from_table(postGis.points_table, where="depth is NULL")
    if len(df) > 0:
        calculate_per_single_point_update_database(df.crs['init'], df)
    else:
        print('No empty points')
        sleep(30)
