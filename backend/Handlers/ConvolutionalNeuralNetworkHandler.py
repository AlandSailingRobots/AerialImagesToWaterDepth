from typing import Any

from keras.models import load_model
from tensorflow.python.util import deprecation
from data_resources import fileToObjects
from map_based_resources.point import DataPoint
from map_based_resources.mapResources import MapResources
import numpy as np

deprecation._PRINT_DEPRECATION_WARNINGS = False


class ConvolutionalHandler:
    map_resource: MapResources
    model: Any
    model_config: dict

    def __init__(self, model_config_index):
        super().__init__()
        self.model_config = fileToObjects.get_available_cnn_models()[model_config_index]
        if "model_path" in self.model_config:
            path = fileToObjects.check_path(self.model_config["model_path"])
        else:
            path = fileToObjects.get_model_path(self.model_config, overwrite_backup=True)
        self.model = load_model(path, custom_objects=fileToObjects.get_custom_objects_cnn_model())
        self.map_resource = MapResources()
        self.coordinate_system = self.map_resource.get_coordinate_system(self.model_config["webmap_name"])

    def get_image(self, longitude, latitude, epsg):
        coordinate = DataPoint(latitude, longitude,
                               epsg,
                               self.model_config["level"])
        image = self.map_resource.get_image(coordinate, specific=self.model_config)
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        return np.array([np.array(image)])

    def predict_points(self, points, crs):
        print(crs, points[0].x, points[0].y)
        generator = (self.get_image(point_.x, point_.y, crs) for point_ in points)
        predict = self.model.predict_generator(generator,
                                               steps=len(points), use_multiprocessing=True)
        print('done predicting')
        return predict

    def predict_point(self, point_, crs):
        return self.model.predict(self.get_image(point_.x, point_.y, crs))
