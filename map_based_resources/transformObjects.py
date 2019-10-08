import math

from map_based_resources import LocationInImage, ImagePoint, DataPoint


def get_image_point(image_tile, point_width, point_height, web_map, layer):
    data_point_in_image = LocationInImage(point_width, point_height)
    image_point = ImagePoint(data_point_in_image, image_tile, web_map, layer)
    return image_point


def get_datapoints_from_json(json_file):
    coordinates = list()
    for coordinate in json_file:
        coordinates.append(
            DataPoint(coordinate["latitude"],
                      coordinate["longitude"],
                      coordinate["type"],
                      coordinate["level"]))
    return coordinates


def get_data_point_from_row(row, coordinate_systems, level):
    info_point = DataPoint(row["latitude"],
                           row["longitude"],
                           coordinate_systems,
                           level)
    info_point.height = row["height"]
    return info_point


def split_part_and_whole(value):
    part, whole = math.modf(value)
    part = round(part, 4)
    whole = int(whole)
    return whole, part


def limit_data_set(df, sample_size, max_depth=None, latitude_range=None, longitude_range=None, no_sample=False):
    if latitude_range is not None:
        df = df[(latitude_range[0] <= df.latitude)
                & (df.latitude <= latitude_range[1])]
    if longitude_range is not None:
        df = df[(longitude_range[0] <= df.longitude)
                & (df.longitude <= longitude_range[1])]
    if max_depth is not None:
        df = df[df.height >= max_depth]
    if df.shape[0] < sample_size:
        sample_size = df.shape[0]
    if no_sample:
        return df
    else:
        return df.sample(sample_size)


def create_info_object_from_panda_row(row, coordinate_systems, level):
    return get_data_point_from_row(row, coordinate_systems, level)
