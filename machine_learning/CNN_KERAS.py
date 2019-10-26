#! /usr/bin/env python
import keras
from keras import layers
import numpy as np
import pandas as pd
from data_resources import fileToObjects, DataSourcesTypes
from keras.models import load_model
from map_based_resources import point, mapResources


def line_execute(line, configuration, model_config, coordinate_system, panda=False):
    if panda:
        line_s = line
    else:
        line_s = line.strip().split(',')
    coordinate = point.DataPoint(float(line_s[1]),
                                 float(line_s[0]),
                                 coordinate_system,
                                 model_config["level"])
    image = configuration.get_image(coordinate, specific=model_config)
    if image.mode != "RGBA":
        image = image.convert("RGBA")
    image_arr = np.array(image)
    image.close()
    height = float(line_s[-1])
    return image_arr, round(height, 1)


def file_execute(files, model_config, panda=False, limit=None):
    configuration = mapResources.MapResources()
    for file in files:
        iterator = get_file_iterator(file, model_config, panda)
        index = 0
        for line in iterator:
            image, depth = line_execute(line, configuration, model_config, file['coordinate_system'], panda)
            index += 1
            yield (np.array([image]), np.array([depth]))
            if index % 10 == 0:
                configuration.clear_images()
            if limit is not None and index == limit:
                break
        if limit is not None and index == limit:
            break
        if not panda:
            iterator.close()
        configuration.clear_images()


def get_file_iterator(file, model_config, panda):
    if panda:
        big = fileToObjects.open_xyz_file_as_panda(file)
        if 'limit_depth' in model_config:
            big = big[(big['height'] >= model_config['limit_depth'][0]) & (
                    big['height'] <= model_config['limit_depth'][1])]
        return big.sample(frac=1).itertuples(index=False, name=None)
    else:
        return open(fileToObjects.check_path(file['path']))


def build_model(path, size_, row_=4):
    if fileToObjects.check_path(path) is None:
        model_ = keras.Sequential([
            layers.Conv2D(input_shape=[size_, size_, row_], filters=32, kernel_size=[5, 5], padding="same",
                          activation='relu'),
            layers.Conv2D(filters=32, kernel_size=[5, 5]),
            layers.Dropout(0.5),
            layers.MaxPool2D(pool_size=[2, 2], strides=2),
            layers.Conv2D(input_shape=[size_, size_, row_], filters=64, kernel_size=[5, 5], padding="same",
                          activation='relu'),
            layers.Conv2D(filters=64, kernel_size=[5, 5]),
            layers.Dropout(0.5),
            layers.MaxPool2D(pool_size=[2, 2], strides=2),
            layers.Dropout(0.5),
            layers.Flatten(),
            layers.Dense(512),
            layers.Dropout(0.5),
            layers.Dense(1),
        ])

        fileToObjects.model_to_json(model_, path)
    else:
        model_ = fileToObjects.load_model_from_json(path)

    optimizer = keras.optimizers.Adamax()

    model_.compile(loss=keras.losses.mean_absolute_percentage_error,
                   optimizer=optimizer,
                   metrics=[keras.metrics.binary_accuracy,
                            'mean_absolute_error', 'mean_squared_error', fileToObjects.root_mean_squared_error,
                            fileToObjects.equal_pred])
    return model_


def save_results(model_, config):
    print(save_string)
    data_ = list(score)
    data_.insert(0, config["webmap_name"])
    data_.insert(1, config["layer_name"])
    data_.insert(2, config['limit_depth'])
    results = pd.DataFrame(data=[data_],
                           columns=['webmap', 'layer', 'range'] + model_.metrics_names)
    results.to_csv('results.csv', mode='a', header=False, index=False)


keras_config = fileToObjects.open_json_file("machine_learning/keras_setup.json")
sources = fileToObjects.get_data(DataSourcesTypes.DataSourceEnum[keras_config["data"]["type"]])
df_is_panda = keras_config["data"]["is_panda"]
train_model_config = fileToObjects.open_json_file("machine_learning/train_models.json")[keras_config["model"]]
if "limit_dataset" in train_model_config:
    sources = sources[train_model_config["limit_dataset"][0]:train_model_config["limit_dataset"][1]]
size = train_model_config["size_in_meters"] * train_model_config["pixels_per_meter"]

if df_is_panda:
    for source in sources:
        fileToObjects.check_xyz_file(source)
model = build_model(keras_config['model_architecture_path'], size)
create_new = False
if "create_new" in keras_config:
    create_new = keras_config["create_new"]
model.summary()
gen = file_execute(sources[0:-3], train_model_config, panda=df_is_panda)
gen_validator = file_execute(sources[-3:], train_model_config, panda=df_is_panda,
                             limit=train_model_config["steps_per_epoch"] * train_model_config["epochs"] * 0.25)
tb = keras.callbacks.tensorboard_v1.TensorBoard()

save_string = fileToObjects.get_model_path(train_model_config)

try:
    check_path = fileToObjects.check_path(save_string)
    print('cp', check_path)
    if check_path is None or create_new is True:
        history = model.fit_generator(gen,
                                      steps_per_epoch=train_model_config["steps_per_epoch"],
                                      epochs=train_model_config["epochs"],
                                      max_queue_size=train_model_config["max_queue_size"],
                                      callbacks=[tb])
        model.save(save_string)
    else:
        model = load_model(save_string, custom_objects=fileToObjects.get_custom_objects_cnn_model())
    score = model.evaluate_generator(generator=gen_validator,
                                     steps=train_model_config["steps_per_epoch"] * train_model_config[
                                         "steps_per_epoch"] / 4, verbose=1)

    save_results(model, train_model_config)
    print(score)
except KeyboardInterrupt:
    pass
