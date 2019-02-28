#!/usr/bin/env python
# coding: utf-8

import json
import math

import pandas as pd

from mapBasedResoures import mapResource


def split_part_and_whole(value):
    part, whole = math.modf(value)
    part = round(part, 4)
    whole = int(whole)
    return whole, part


def open_json_file(filename):
    with open(filename) as f:
        data = json.load(f)
    return data


def get_coordinates_from_file():
    return mapResource.get_datapoints_from_json(open_json_file('coordinates.json'))


def get_config_from_json():
    return open_json_file('config.json')


def get_data_sources():
    return open_json_file('data/data_sources.json')


def get_configuration():
    return mapResource.MapResources(get_config_from_json())


def get_image_point(tile, data_point, point_width, point_height, web_map, layer):
    return mapResource.get_image_point(tile, data_point, point_width, point_height, web_map, layer)


def open_xyz_file_as_panda(file):
    return pd.read_csv('data/{0}.xyz'.format(file), delim_whitespace=True, names=['longitude', 'latitude', 'height'])


def create_info_object_from_panda_row(row, coordinate_systems, level):
    return mapResource.get_data_point_from_row(row, coordinate_systems, level)
