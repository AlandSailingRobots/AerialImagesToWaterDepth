import json
import pandas as pd
import os
import wget
from keras import backend as K
from keras.engine.saving import model_from_json
from tensorflow.python.util import deprecation
from PIL import Image

deprecation._PRINT_DEPRECATION_WARNINGS = False

if os.path.isfile("data_resources/data_settings.json"):
    data_settings = json.load(open("data_resources/data_settings.json"))
elif os.path.isfile("../data_resources/data_settings.json"):
    data_settings = json.load(open("../data_resources/data_settings.json"))
else:
    print("ERROR no data settings")
    data_settings = None
backup_map = data_settings["backup_map"]
images_map = backup_map + data_settings["images_map"]
data_map = backup_map + data_settings["data_map"]
models_map = backup_map + data_settings["models_map"]
available_paths = ['./', '../', data_map, images_map, models_map, './resources/', '../resources/']


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


def get_data(data_type):
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


def check_xyz_file(file):
    path = check_path(file['path'])
    if path is None and 'url' not in file:
        raise FileNotFoundError(file['name'])
    if path is None and 'url' in file:
        print('Missing {0}, retrieving from url {1}'.format(file['name'], file['url']))
        local_dir = file['path'].split('/')[0]
        directory = check_dir(data_map + local_dir)
        if directory is None:
            os.mkdir(data_map + local_dir)
            directory = data_map + local_dir
        wget.download(file['url'], '{0}/{1}.xyz'.format(directory, file['name']))


def open_xyz_file_as_panda(file, delimiter=','):
    path = check_path(file['path'])
    check_xyz_file(file)
    if path.split('.')[-1] == 'xyz':
        delimiter = ' '
    return pd.read_csv(path, names=['longitude', 'latitude', 'height'], delimiter=delimiter)


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
    if not os.path.exists(path):
        return False
    try:
        Image.open(path)
    except IOError:
        os.remove(path)
        return False
    return True


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


def get_wmts_config_from_json(lock=None):
    return open_json_file('resources/wmts_config.json', lock)


def get_model_path(config, with_h5=True, overwrite_backup=False):
    path = '-'.join([f'{key}-{value}' for key, value in config.items()])
    if ("save_to_backup" in config and config["save_to_backup"]) or overwrite_backup:
        path = models_map + path
    if with_h5:
        path = path + '.h5'
    print(path)
    return path


def equal_pred(y_true, y_pred):
    return K.equal(K.round(y_pred), K.round(y_true))


def root_mean_squared_error(y_true, y_pred):
    return K.sqrt(K.mean(K.square(y_pred - y_true)))


def get_custom_objects_cnn_model():
    return {"root_mean_squared_error": root_mean_squared_error,
            "equal_pred": equal_pred}


def model_to_json(model, path):
    model_json = model.to_json()
    with open(path, "w") as json_file:
        json_file.write(model_json)


def load_model_from_json(path):
    with open(path, 'r') as json_file:
        loaded_model_json = json_file.read()
    return model_from_json(loaded_model_json)
