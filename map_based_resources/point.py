import matplotlib.pyplot as plt
import matplotlib.patches as patches
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
        if src != destination:
            project_src = pyproj.Proj(init=src)
            project_dest = pyproj.Proj(init=destination)
            transformed = pyproj.transform(project_src, project_dest, self.longitude, self.latitude)
            return transformed
        else:
            return self.longitude, self.latitude

    def calculate_distance_to_point(self, other_point):
        correct_coordinate_system = 'epsg:4326'  # This is the only coordinate system in which it can be calculated.
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

    def __init__(self, data_point_in_image: LocationInImage, image_tile: mapResources.ImageTile,
                 web_map: mapResources.MapService, layer: mapResources.MapLayer):
        self.image_tile = image_tile
        self.web_map = web_map
        self.layer = layer
        self.name = '{0} {1}'.format(web_map.name, layer.name)
        self.data_point_in_image = data_point_in_image

    def __str__(self) -> str:
        return str(self.__class__) + ": " + str(self.__dict__)

    def __repr__(self):
        return repr(vars(self))

    def get_box_around(self, size):
        distance_in_pixels = size / self.layer.pixel_size
        left_lower_coordinates = (self.data_point_in_image.width - distance_in_pixels,
                                  self.data_point_in_image.height - distance_in_pixels)
        width = 2 * distance_in_pixels
        height = 2 * distance_in_pixels

        return left_lower_coordinates, width, height

    def show_image_with_point(self,box_size):
        fig = plt.figure()
        a = fig.add_subplot(1, 2, 1)
        plt.imshow(self.image_tile.get_image_from_tile())

        plt.plot(self.data_point_in_image.width, self.data_point_in_image.height, color='yellow', marker='+')
        coord, w, h = self.get_box_around(box_size)
        box = patches.Rectangle(coord, w, h,fill=False, color='White')
        a.add_patch(box)
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
