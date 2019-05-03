import matplotlib.pyplot as plt
import pyproj
from PIL import Image
from geopy.distance import great_circle
from map_based_resources import mapResources
from data_resources import singleTile


class DataPoint:
    def __init__(self, latitude, longitude, coordinate_type, level):
        self.latitude = latitude
        self.longitude = longitude
        self.coordinate_type = coordinate_type
        self.level = level

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

    def get_cropped_image(self, size, square_size=3,lock=None):
        if size not in self.cropped_images:
            self.cropped_images[size] = self.get_image_bounding_box(size, square_size,lock)
        return self.cropped_images[size]

    def get_image_bounding_box(self, size, square_size,lock=None):
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
            image = self.make_image_bigger(data_point_image, new_image_size, floor_square_size,lock)

        return image.crop(self.get_box_around(size, data_point=data_point_image))

    def make_image_bigger(self, data_point_image, new_image_size, floor_square_size,lock=None):
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
                image_ = singleTile.get_pillow_image_from_tile(self.web_map, self.layer, row_item, column_item,lock)
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

    def get_cropped_images(self, size):
        return list(point.get_cropped_image(size) for point in self.image_points)

    def retrieve_all_images(self):
        for point in self.image_points:
            point.image_tile.get_image_from_tile().close()
