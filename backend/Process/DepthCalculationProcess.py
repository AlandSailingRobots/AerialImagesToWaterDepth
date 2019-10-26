from time import sleep

from backend.Handlers import ConvolutionalNeuralNetworkHandler, PostGisHandler
from data_resources import fileToObjects

handler_settings = fileToObjects.open_json_file('server_settings.json')["ProcessHandler"]

cnn = ConvolutionalNeuralNetworkHandler.ConvolutionalHandler(handler_settings["cnn_model_index"])
postGis = PostGisHandler.PostGisHandler()


def calculate_per_frame(crs, data):
    if crs != cnn.coordinate_system:
        data = data.to_crs(cnn.coordinate_system)
        crs = cnn.coordinate_system
    depths = cnn.predict_points(data.geometry, crs)
    data['depths'] = depths.flatten()
    data['sql'] = data.apply(
        lambda row: postGis.update_point_height(postGis.points_table, row.identifier, row.depths,
                                                return_query=True), axis=1)
    query = ";\n".join(list(data['sql']))
    postGis.send_to_db(query)


def calculate_per_single_point_update_database(crs, data):
    for index, item in data.iterrows():
        depths = cnn.predict_point(item.geom, crs)
        postGis.update_point_height(postGis.points_table, item.identifier, depths.flatten()[0])


def run_process():
    while True:
        df = postGis.select_from_table(postGis.points_table, where="depth is NULL", limit=1000)
        if 0 < len(df) < 50:
            print("single")
            calculate_per_single_point_update_database(df.crs['init'], df)
        elif len(df) > 50:
            print("calculate per frame")
            calculate_per_frame(df.crs['init'], df)
        else:
            print('No empty points')
            sleep(30)


if __name__ == '__main__':
    run_process()
