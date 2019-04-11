import json
from enum import Enum

import pandas as pd
import os
from data_resources import transformObjects
import urllib.request as req
from map_based_resources import mapResources


class DatasourceType(Enum):
    open_source = ['open_data/data_sources.json']
    private = ['data/data_sources.json']
    corrected = ['data/data_sources_corrected.json']
    combined = open_source + private
    combined_corrected = open_source + corrected


def check_dir(dir_name):
    if os.path.isdir(dir_name):
        return dir_name
    if os.path.isdir('../' + dir_name):
        return '../' + dir_name
    return None


def check_path(filename):
    if os.path.isfile(filename):
        return filename

    if os.path.isfile('../' + filename):
        return '../' + filename
    return None


def open_json_file(filename):
    path = check_path(filename)
    if path is None:
        raise FileNotFoundError(filename)
    with open(path) as f:
        data = json.load(f)
    return data


def get_coordinates_from_file():
    return transformObjects.get_datapoints_from_json(open_json_file('resources/coordinates.json'))


def get_config_from_json():
    return open_json_file('resources/config.json')


def get_data(data_type=DatasourceType.open_source):
    """
    Method to get the existing data.
    :type data_type: DatasourceType
    :param data_type: Name of what kind of data options: open_source, combined, private, corrected and combined
    corrected. default open_source
    :return: json list with source files en their values.
    """
    json_list = list()
    for source in data_type.value:
        json_list += open_json_file(source)
    return json_list


def get_configuration():
    return mapResources.MapResources(get_config_from_json())


def open_xyz_file_as_panda(file):
    path = check_path(file['path'])
    if path is None and 'url' not in file:
        raise FileNotFoundError(file['name'])
    if path is None and 'url' in file:
        print('Missing {0}, retrieving from url {1}'.format(file['name'], file['url']))
        directory = check_dir(file['path'].split('/')[0])
        req.urlretrieve(file['url'], '{0}/{1}.xyz'.format(directory, file['name']))
        path = file['url']
    return pd.read_csv(path, delim_whitespace=True,
                       names=['longitude', 'latitude', 'height'])


def save_panda_as_file(df, name):
    """
    Method to save the panda DataFrame in the corrected_path
    :param name: Name of the DataFrame
    :type df: Panda Dataframe
    """
    df.to_csv('{0}/{1}.xyz'.format(check_dir('corrected_data'), name), sep=' ', header=False, index=False)
