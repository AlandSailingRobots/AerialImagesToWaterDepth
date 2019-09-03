import keras
from keras.models import load_model

from data_resources import fileToObjects, singleTile
from map_based_resources import point
import numpy as np


class ConvolutionalHandler:
    def __init__(self):
        self.model = load_model('image_ava_infra_size_2_steps_10_epochs_10000.h5')
        self.configuration = fileToObjects.get_configuration()

    def get_image(self, longitude, latitude, epsg):
        coordinate = point.DataPoint(latitude, longitude,
                                     epsg,
                                     15)
        coordinate_tile = singleTile.get_image_and_plot(coordinate, self.configuration, show=False, specific=3)
        return np.array(coordinate_tile.get_cropped_image_single(2, 0))

    def predict_points(self, points, crs):
        print(crs, points[0].x, points[0].y)
        predicted = self.model.predict(np.array([self.get_image(point_.x, point_.y, crs) for point_ in points]))
        print('len', (len(predicted)))
        return predicted
