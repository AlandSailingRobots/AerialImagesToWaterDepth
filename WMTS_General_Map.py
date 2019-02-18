#!/usr/bin/env python
# coding: utf-8

from geopy.distance import great_circle
import matplotlib.pyplot as plt
import pyproj
import json
import math


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
    get_ = convert_coordinate_systems(lat, lon)
    get_1 = convert_coordinate_systems(lat1, lon1)
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


def plot_rectangles(df):
    fig, ax = plt.subplots(1, 1)
    color_items = ['blue', 'yellow', 'red', 'green']
    count = 0
    for x in df.values:
        if count == len(color_items):
            count = 0
        rect = plt.Rectangle((x[0], x[1]), x[2] - x[0], x[3] - x[1], color=color_items[count])
        count += 1
        ax.add_patch(rect)
    ax.autoscale_view()


def get_info_wmts(wmts, map_layer, tile_matrix_set_name):
    print('possible maps:', list(wmts.contents.keys()))
    print('possible coordinate system:', list(wmts.tilematrixsets.keys()))
    print('possible formats :', list(wmts.contents[map_layer].formats))
    print('length of the formats', len(wmts.tilematrixsets[tile_matrix_set_name].tilematrix))
    print('length of the formats', wmts.tilematrixsets[tile_matrix_set_name].tilematrix)


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
