from time import sleep

from backend.ConvolutionalNeuralNetworkHandler import ConvolutionalHandler
from backend.PostGisHandler import PostGisHandler

cnn = ConvolutionalHandler(2)
postGis = PostGisHandler()


def calculate_per_frame(crs, data):
    splitted = crs.split(':')[-1]
    depths = cnn.predict_points(data.geom, crs)
    data['depths'] = depths.flatten()
    print(data.columns)
    data['sql'] = data.apply(
        lambda row: postGis.update_point_height(postGis.points_table, row.geom, splitted, row.depths,
                                                row.zoom_level, return_query=True), axis=1)
    query = "\n".join(list(data['sql']))
    postGis.send_to_db(query)


def calculate_per_single_point_update_database(crs, data):
    for index, item in data.iterrows():
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
