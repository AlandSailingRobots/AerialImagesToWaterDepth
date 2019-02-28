import io

from PIL import Image

from mapBasedResoures import point, webMap


class MapResources:
    def __init__(self, config):
        self.standardized_rendering_pixel_size = config["standardized_rendering_pixel_size"]
        self.web_maps = list()
        for wmts in config["wmts"]:
            self.web_maps.append(webMap.WebMap(wmts))


def get_image_from_tile(tile):
    image_stream = io.BytesIO(tile.read())
    image = Image.open(image_stream)
    return image


def get_image_point(tile, data_point, point_width, point_height, web_map, layer):
    image = get_image_from_tile(tile)
    data_point_in_image = point.LocationInImage(point_width, point_height)
    image_point = point.ImagePoint(data_point, data_point_in_image, image, web_map, layer)
    return image_point


def get_datapoints_from_json(json_file):
    coordinates = list()
    for coordinate in json_file:
        coordinates.append(
            point.DataPoint(coordinate["latitude"],
                            coordinate["longitude"],
                            coordinate["type"],
                            coordinate["level"]))
    return coordinates


def get_data_point_from_row(row, coordinate_systems, level):
    info_point = point.DataPoint(row["latitude"],
                                 row["longitude"],
                                 coordinate_systems,
                                 level)
    info_point.height = row["height"]
    return info_point
