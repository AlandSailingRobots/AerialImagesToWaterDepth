from keras.models import load_model

from data_resources import fileToObjects
from map_based_resources import point, singleTile, mapResources
import numpy as np


class ConvolutionalHandler:
    def __init__(self, model_config_index):
        self.models = fileToObjects.get_available_cnn_models()
        self.model_config = self.models[model_config_index]
        self.model = load_model(fileToObjects.check_path(self.model_config["model_path"]))
        self.configuration = mapResources.MapResources()

    def get_image(self, longitude, latitude, epsg):
        coordinate = point.DataPoint(latitude, longitude,
                                     epsg,
                                     self.model_config["level"])
        coordinate_tile = singleTile.get_image_and_plot(coordinate, self.configuration, show=False,
                                                        specific=self.model_config)
        image = coordinate_tile.get_cropped_image_single(self.model_config["size_in_meters"])
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        return np.array([np.array(image)])

    def predict_points(self, points, crs):
        print(crs, points[0].x, points[0].y)
        predict = self.model.predict_generator((self.get_image(point_.x, point_.y, crs) for point_ in points),
                                               steps=len(points), use_multiprocessing=True)
        print('done predicting')
        return predict

    def predict_point(self, point_, crs):
        return self.model.predict(self.get_image(point_.x, point_.y, crs))
