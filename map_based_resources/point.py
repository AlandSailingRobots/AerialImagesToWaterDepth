import matplotlib.pyplot as plt
import pyproj
from geopy.distance import great_circle

from map_based_resources import mapResources


class DataPoint:
    def __init__(self, latitude, longitude, coordinate_type, level):
        self.latitude = latitude
        self.longitude = longitude
        self.coordinate_type = coordinate_type
        self.level = level

    def __str__(self) -> str:
        return str(self.__class__) + ": " + str(self.__dict__)

    def __repr__(self):
        return repr(vars(self))

    def convert_coordinate_systems(self, inverse=False, destination='epsg:3067'):
        """Converts Coordinate System to a different System.
        Default From WGS84 to Finnish System(ETRS-TM35FIN). If inverse is passed then they are swapped around.
        returns tuple with 0 being E/Longitude, and 1 begin N/Latitude
        """
        src = self.coordinate_type
        if inverse:
            src, destination = destination, src
        proj_src = pyproj.Proj(init=src)
        proj_dest = pyproj.Proj(init=destination)
        transformed = pyproj.transform(proj_src, proj_dest, self.longitude, self.latitude)
        return transformed

    def calculate_distance_to_point(self, other_point):
        correct_coordinate_system = 'epsg:4326'
        if other_point.coordinate_type != correct_coordinate_system:
            point_other = other_point.convert_coordinate_systems(destination=correct_coordinate_system)
        else:
            point_other = (other_point.latitude, other_point.longitude)
        if self.coordinate_type != correct_coordinate_system:
            point_self = self.convert_coordinate_systems(destination=correct_coordinate_system)
        else:
            point_self = (self.latitude, self.longitude)
        return great_circle(point_self, point_other)


class LocationInImage:

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def __str__(self) -> str:
        return str(self.__class__) + ": " + str(self.__dict__)

    def __repr__(self):
        return repr(vars(self))


class ImagePoint:

    def __init__(self, data_point_in_image: LocationInImage, image_tile: mapResources.ImageTile, web_map, layer):
        self.image_tile = image_tile
        self.web_map = web_map
        self.layer = layer
        self.name = '{0} {1} {2}'.format(web_map.name, layer.name, layer.level)
        self.data_point_in_image = data_point_in_image

    def __str__(self) -> str:
        return str(self.__class__) + ": " + str(self.__dict__)

    def __repr__(self):
        return repr(vars(self))

    def show_image_with_point(self):
        fig = plt.figure()
        a = fig.add_subplot(1, 2, 1)
        plt.imshow(self.image_tile.image)
        plt.plot(self.data_point_in_image.width, self.data_point_in_image.height, color='yellow', marker='+')
        a.set_title(self.name)


class MeasurementPoint:
    def __init__(self, data_point: DataPoint):
        self.data_point = data_point
        self.image_points = list()

    def __str__(self) -> str:
        return str(self.__class__) + ": " + str(self.__dict__)

    def __repr__(self):
        return repr(vars(self))

    def add_image_point(self, image_point: ImagePoint):
        self.image_points.append(image_point)
