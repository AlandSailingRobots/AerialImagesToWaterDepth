import json

import pandas as pd
import os
import urllib.request as req
from PIL import Image

from data_resources.DataSourcesTypes import DataSourceEnum

data_settings = json.load(open("../data_resources/data_settings.json"))
backup_map = data_settings["backup_map"]
images_map = backup_map + data_settings["images_map"]
data_map = backup_map + data_settings["data_map"]
models_map = backup_map + data_settings["models_map"]
available_paths = ['../', data_map, images_map, models_map, '../resources/']


def check_dir(dir_name):
    if os.path.isdir(dir_name):
        return dir_name
    if os.path.isdir('../' + dir_name):
        return '../' + dir_name
    return None


for path_ in [backup_map] + available_paths:
    if check_dir(path_) is None:
        os.mkdir(path_)


def check_path(filename):
    if os.path.isfile(filename):
        return filename
    if filename[0] == '/' and os.path.isfile('..' + filename):
        return '..' + filename
    for path in available_paths:
        if os.path.isfile(path + filename):
            return path + filename
    return None


def open_json_file(filename, lock=None):
    path = check_path(filename)
    if path is None:
        raise FileNotFoundError(backup_map, filename)
    with open(path) as f:
        if lock is not None:
            lock.acquire()
        data = json.load(f)
    f.close()
    if lock is not None:
        lock.release()
    return data


def get_wmts_config_from_json(lock=None):
    return open_json_file('wmts_config.json', lock)


def get_data(data_type=DataSourceEnum.open_source):
    """
    Method to get the existing data.
    :type data_type: DataSourceEnum
    :param data_type: Name of what kind of data options: open_source, combined, private, corrected and combined
    corrected. default open_source
    :return: json list with source files en their values.
    """
    json_list = list()
    for source in data_type.value:
        json_list += open_json_file(source)
    return json_list


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


def save_panda_as_file(df: pd.DataFrame, name, dir_name='corrected_data'):
    """
    Method to save the panda DataFrame in the corrected_path
    :param dir_name: Directory to put the file in
    :param name: Name of the DataFrame
    :type df: Panda DataFrame
    """
    file_path = '{0}/{1}.xyz'.format(check_dir(dir_name), name)
    df.to_csv(file_path, sep=' ', header=False, index=False)
    return file_path


def check_image(layer_name, level, row, column):
    path = images_map
    path += '/{0}/{1}/{2}/{3}.png'.format(layer_name, level, row, column)
    return os.path.exists(path)


def get_image(layer_name, level, row, column):
    path = images_map
    path += '/{0}/{1}/{2}/{3}.png'.format(layer_name, level, row, column)
    if os.path.exists(path):
        return Image.open(path)
    else:
        return None


def save_image(image: Image, layer_name, level, row, column, lock=None):
    path = images_map
    for sub_dir in [layer_name, level, row]:
        path += f'/{sub_dir}'
        if not os.path.exists(path):
            os.mkdir(path)
    path += '/{0}.png'.format(column)
    if lock is not None:
        lock.acquire()
    image.save(path, format='PNG')
    if lock is not None:
        lock.release()


def get_available_cnn_models():
    return open_json_file('backend/cnn_models.json')
