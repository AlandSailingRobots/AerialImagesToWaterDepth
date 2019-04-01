import json
import pandas as pd
import os
from data_resources import transformObjects


from map_based_resources import mapResources


def open_json_file(filename):
    if not os.path.isfile(filename):
        if not os.path.isfile('../'+filename):
            raise FileNotFoundError(filename)
        else:
            filename = '../'+filename
    with open(filename) as f:
        data = json.load(f)
    return data


def get_coordinates_from_file():
    return transformObjects.get_datapoints_from_json(open_json_file('resources/coordinates.json'))


def get_config_from_json():
    return open_json_file('resources/config.json')


def get_data_sources():
    return open_json_file('data/data_sources.json')


def get_open_data_sources():
    return open_json_file('open_data/data_sources.json')


def get_configuration():
    return mapResources.MapResources(get_config_from_json())


def open_xyz_file_as_panda(file):
    return pd.read_csv('../{0}.xyz'.format(file['path']), delim_whitespace=True,
                       names=['longitude', 'latitude', 'height'])
