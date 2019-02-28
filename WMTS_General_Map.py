#!/usr/bin/env python
# coding: utf-8

import io
import json
import math
import pandas as pd
import pyproj
import matplotlib.pyplot as plt
from PIL import Image
from geopy.distance import great_circle


def split_part_and_whole(value):
    part, whole = math.modf(value)
    part = round(part, 4)
    whole = int(whole)
    return whole, part


def calculate_distance(lat, lon, lat1, lon1):
    lat_lon = (lat, lon)
    lat_lon1 = (lat1, lon1)
    return great_circle(lat_lon, lat_lon1)


def distance_meter(lat, lon, lat1, lon1):
    return calculate_distance(lat, lon, lat1, lon1).m


def distance_kilometer(lat, lon, lat1, lon1):
    return calculate_distance(lat, lon, lat1, lon1).km


def calculate_distance_finnish(lat, lon, lat1, lon1, distance_type='km'):
    get_ = convert_coordinate_systems(lat, lon,inverse=True)
    get_1 = convert_coordinate_systems(lat1, lon1,inverse=True)
    if distance_type == 'm':
        distance_func = distance_meter
    else:
        distance_func = distance_kilometer
    return distance_func(get_[1], get_[0], get_1[1], get_1[0])


def get_width_height_covered_by_matrix(matrix, standardized_rendering_pixel_size, distance_type=None):
    delta_width = matrix.tilewidth * standardized_rendering_pixel_size * matrix.scaledenominator
    delta_height = matrix.tileheight * standardized_rendering_pixel_size * matrix.scaledenominator
    lon1 = matrix.topleftcorner[0] + delta_width
    lat1 = matrix.topleftcorner[1] - delta_height
    distance = calculate_distance_finnish(lon=matrix.topleftcorner[0],
                                          lat=matrix.topleftcorner[1],
                                          lon1=lon1,
                                          lat1=lat1, distance_type=distance_type)
    return distance


def get_info_wmts(wmts, map_layer, tile_matrix_set_name):
    print('possible maps:', list(wmts.contents.keys()))
    print('possible coordinate system:', list(wmts.tilematrixsets.keys()))
    print('possible formats :', list(wmts.contents[map_layer].formats))
    print('length of the formats', len(wmts.tilematrixsets[tile_matrix_set_name].tilematrix))
    print('length of the formats', wmts.tilematrixsets[tile_matrix_set_name].tilematrix)


def plot_image(image, pos_image_height, pos_image_width, name):
    fig = plt.figure()
    a = fig.add_subplot(1, 2, 1)
    plt.imshow(image)
    plt.plot(pos_image_width, pos_image_height, color='yellow', marker='+')
    a.set_title(name)


def get_image_from_tile(tile):
    image_stream = io.BytesIO(tile.read())
    image = Image.open(image_stream)
    return image


def convert_coordinate_systems(lat, lon, inverse=False, destination='epsg:3067', src='epsg:4326'):
    """Converts Coordinate System to a different System.
    Default From WGS84 to Finnish System(ETRS-TM35FIN). If inverse is passed then they are swapped around.
    returns tuple with 0 being E/Longitude, and 1 begin N/Latitude
    """
    if inverse:
        src, destination = destination, src
    proj_src = pyproj.Proj(init=src)
    proj_dest = pyproj.Proj(init=destination)
    transformed = pyproj.transform(proj_src, proj_dest, lon, lat)
    return transformed


def open_json_file(filename):
    with open(filename) as f:
        data = json.load(f)
    return data


def get_coordinates_from_file():
    return open_json_file('coordinates.json')


def get_config_from_json():
    return open_json_file('config.json')


def get_data_sources():
    return open_json_file('data/data_sources.json')


def open_xyz_file_as_panda(file):
    return pd.read_csv('data/{0}.xyz'.format(file), delim_whitespace=True, names=['longitude', 'latitude', 'height'])


def create_info_object_from_panda_row(row, coordinate_systems, level):
    row['type'] = coordinate_systems
    row['level'] = level
    return row
