import json
import pandas as pd
import os
from data_resources import transformObjects

from map_based_resources import mapResources


def check_dir(dir_name):
    if os.path.isdir(dir_name):
        return dir_name
    if os.path.isdir('../' + dir_name):
        return '../' + dir_name
    raise NotADirectoryError(dir_name)


def check_path(filename):
    if os.path.isfile(filename):
        return filename

    if os.path.isfile('../' + filename):
        return '../' + filename
    raise FileNotFoundError(filename)


def open_json_file(filename):
    with open(check_path(filename)) as f:
        data = json.load(f)
    return data


def get_coordinates_from_file():
    return transformObjects.get_datapoints_from_json(open_json_file('resources/coordinates.json'))


def get_config_from_json():
    return open_json_file('resources/config.json')


def get_data(data_type='open_source'):
    """
    Method to get the existing data.
    :param data_type: Name of what kind of data options: open_source, combined or private. default open_source
    :return: json list with source files en their values.
    """
    if data_type == 'open_source':
        return open_json_file('open_data/data_sources.json')
    elif data_type == 'combined':
        return open_json_file('data/data_sources.json') + open_json_file('open_data/data_sources.json')
    elif data_type == 'private':
        return open_json_file('data/data_sources.json')
    else:
        return open_json_file('open_data/data_sources.json')


def get_configuration():
    return mapResources.MapResources(get_config_from_json())


def open_xyz_file_as_panda(file):
    return pd.read_csv(check_path(file['path'] + '.xyz'), delim_whitespace=True,
                       names=['longitude', 'latitude', 'height'])


def save_panda_as_file(df, name):
    """
    Method to save the panda dataframe in the corrected_path
    :param name: Name of the Dataframe
    :type df: Panda Dataframe
    """
    df.to_csv(check_dir('corrected_data') + '/' + name + '.xyz', sep=' ', header=False, index=False)
