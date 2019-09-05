import keras
from keras.models import load_model

from data_resources import fileToObjects, singleTile
from map_based_resources import point
import numpy as np


class ConvolutionalHandler:
    def __init__(self):
        self.model = load_model(fileToObjects.check_path('image_ava_infra_size_2_steps_10_epochs_10000.h5'))
        self.configuration = fileToObjects.get_configuration()

    def get_image(self, longitude, latitude, epsg):
        coordinate = point.DataPoint(latitude, longitude,
                                     epsg,
                                     15)
        coordinate_tile = singleTile.get_image_and_plot(coordinate, self.configuration, show=False, specific=3)
        image = coordinate_tile.get_cropped_image_single(2, 0)
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        return np.array([np.array(image)])

    def predict_points(self, points, crs):
        print(crs, points[0].x, points[0].y)
        predict = self.model.predict_generator((self.get_image(point_.x, point_.y, crs) for point_ in points),
                                            steps=len(points), use_multiprocessing=True)
        print('done predicting')
        return predict

    def predict_point(self,point_,crs):
        return self.model.predict(self.get_image(point_.x,point_.y,crs))