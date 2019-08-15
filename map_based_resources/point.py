import matplotlib.pyplot as plt
import pyproj
from PIL import Image
import geopy
from geopy.distance import great_circle
from map_based_resources import mapResources
from data_resources import singleTile
from shapely.geometry import Point


class DataPoint(Point):
    FinnishSystem = 'epsg:3067'
    MeasurableSystem = 'epsg:4326'
    decimals_in_point = 5

    def __init__(self, latitude, longitude, coordinate_type, level, *args):
        super().__init__(longitude, latitude)
        self.coordinate_type = coordinate_type
        self.level = level

    def convert_coordinate_systems(self, inverse=False, destination=FinnishSystem, save_in_point=False,
                                   return_point=False):
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
            transformed = pyproj.transform(project_src, project_dest, self.x, self.y)
            if save_in_point:
                super().__init__(transformed)
                self.coordinate_type = destination
            if return_point:
                super().__init__(transformed)
                self.coordinate_type = destination
                return self
            return transformed
        else:
            if return_point:
                return self
            return self.x, self.y

    def convert_to_correct_coordinate_system(self, initial_point, correct_coordinate_system=MeasurableSystem):
        return initial_point.convert_coordinate_systems(destination=correct_coordinate_system)

    def calculate_distance_to_point(self, other_point):
        point_other = self.convert_to_correct_coordinate_system(other_point)
        point_self = self.convert_to_correct_coordinate_system(self)
        return great_circle(point_self, point_other)

    def circle_distance(self, distance):
        return geopy.distance.great_circle(kilometers=distance)

    def create_neighbouring_point(self, distance, heading):
        # point_begin = self.convert_to_correct_coordinate_system(self)
        new_point = distance.destination(geopy.Point(self.y, self.x), bearing=heading)
        data = DataPoint(new_point.latitude, new_point.longitude, self.MeasurableSystem, self.level)
        return data

    def __str__(self):
        return "latitude: {0}, longitude :{1}, level: {2}, coordinate type {3}".format(self.y,
                                                                                       self.x,
                                                                                       self.level,
                                                                                       self.coordinate_type)

    def __repr__(self) -> str:
        return "latitude: {0}, longitude :{1}, level: {2}, coordinate type {3}".format(self.y,
                                                                                       self.x,
                                                                                       self.level,
                                                                                       self.coordinate_type)


class LocationInImage:

    def __init__(self, width, height):
        self.width = width
        self.height = height


class ImagePoint:

    def __init__(self, data_point_in_image: LocationInImage, image_tile: mapResources.ImageTile,
                 web_map: mapResources.MapService, layer: mapResources.MapLayer):
        self.image_tile = image_tile
        self.web_map = web_map
        self.layer = layer
        self.name = '{0} {1}'.format(web_map.name, layer.name)
        self.data_point_in_image = data_point_in_image
        self.cropped_images = dict()

    def get_box_around(self, size, data_point=None):
        if data_point is None:
            data_point = self.data_point_in_image
        distance_in_pixels = size / self.layer.pixel_size

        left_lower_coordinates = (data_point.width - distance_in_pixels,
                                  data_point.height - distance_in_pixels)

        width = 2 * distance_in_pixels
        height = 2 * distance_in_pixels
        return left_lower_coordinates + (left_lower_coordinates[0] + width, left_lower_coordinates[1] + height)

    def get_cropped_image(self, size, square_size=3, lock=None):
        return self.get_image_bounding_box(size, square_size, lock)

    def get_image_bounding_box(self, size, square_size, lock=None):
        distance_in_pixels = size / self.layer.pixel_size
        image = self.image_tile.get_image_from_tile(lock)
        data_point_image = self.data_point_in_image
        make_bigger = False
        if (data_point_image.height - distance_in_pixels < 0 or
                data_point_image.width - distance_in_pixels < 0 or
                data_point_image.height + distance_in_pixels > image.height or
                data_point_image.width + distance_in_pixels > image.width):
            make_bigger = True

        if make_bigger:
            min_square_size = (size * 2) / (image.width * self.layer.pixel_size)
            while min_square_size > square_size:
                square_size += 2
            new_image_size = (image.width * square_size, image.height * square_size)
            floor_square_size = square_size // 2
            image = self.make_image_bigger(data_point_image, new_image_size, floor_square_size, lock)

        return image.crop(self.get_box_around(size, data_point=data_point_image))

    def make_image_bigger(self, data_point_image, new_image_size, floor_square_size, lock=None):
        new_im = Image.new('RGB', new_image_size)
        column = self.image_tile.column
        row = self.image_tile.row
        column_offset = 0
        begin = -floor_square_size
        end = floor_square_size + 1
        image_ = None
        for column_item in range(column + begin, column + end):
            row_offset = 0
            for row_item in range(row + begin, row + end):
                image_ = singleTile.get_pillow_image_from_tile(self.web_map, self.layer, row_item, column_item,
                                                               lock)
                new_im.paste(image_, (column_offset, row_offset))
                row_offset += image_.width
            column_offset += image_.height

        data_point_image.width += (image_.width * floor_square_size)
        data_point_image.height += (image_.height * floor_square_size)
        return new_im

    def show_image_with_point(self):
        fig = plt.figure()
        a = fig.add_subplot(1, 2, 1)
        plt.imshow(self.image_tile.get_image_from_tile())
        plt.plot(self.data_point_in_image.width, self.data_point_in_image.height, color='yellow', marker='+')
        a.set_title(self.name)


class MeasurementPoint:
    def __init__(self, data_point: DataPoint):
        self.data_point = data_point
        self.image_points = list()

    def add_image_point(self, image_point: ImagePoint):
        self.image_points.append(image_point)

    def get_cropped_images(self, size, lock=None):
        return list(point.get_cropped_image(size, lock=lock) for point in self.image_points)

    def get_cropped_image_single(self, size, position):
        return self.image_points[position].get_cropped_image(size)

    def retrieve_all_images(self):
        for point in self.image_points:
            point.image_tile.get_image_from_tile().close()
