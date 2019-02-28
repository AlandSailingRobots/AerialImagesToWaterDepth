import json

import pandas as pd
from data_resources import transformObjects

from map_based_resources import mapResources


def open_json_file(filename):
    with open('./' + filename) as f:
        data = json.load(f)
    return data


def get_coordinates_from_file():
    return transformObjects.get_datapoints_from_json(open_json_file('coordinates.json'))


def get_config_from_json():
    return open_json_file('config.json')


def get_data_sources():
    return open_json_file('data/data_sources.json')


def get_configuration():
    return mapResources.MapResources(get_config_from_json())


def open_xyz_file_as_panda(file):
    return pd.read_csv('./data/{0}.xyz'.format(file), delim_whitespace=True, names=['longitude', 'latitude', 'height'])
