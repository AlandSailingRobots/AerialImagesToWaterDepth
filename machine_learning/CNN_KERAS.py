#! /usr/bin/env python
import keras
from keras import layers, backend as K
import numpy as np
from data_resources import fileToObjects, DataSourcesTypes
from keras.models import load_model
from map_based_resources import point, mapResources

keras_config = fileToObjects.open_json_file("machine_learning/keras_setup.json")
sources = fileToObjects.get_data(DataSourcesTypes.DataSourceEnum[keras_config["data"]["type"]])
df_is_panda = keras_config["data"]["is_panda"]
train_model_config = fileToObjects.open_json_file("machine_learning/train_models.json")[keras_config["model"]]
if "limit_dataset" in train_model_config:
    sources = sources[train_model_config["limit_dataset"][0]:train_model_config["limit_dataset"][1]]


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
    # coordinate_tile = singleTile.get_image_and_plot(coordinate, configuration, show=False,
    #                                                 specific=model_config)
    # image = coordinate_tile.get_cropped_image_single(model_config["size_in_meters"])
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


size = train_model_config["size_in_meters"] * train_model_config["pixels_per_meter"]
row = 4


def equal_pred(y_true, y_pred):
    return K.equal(K.round(y_pred), K.round(y_true))


def root_mean_squared_error(y_true, y_pred):
    return K.sqrt(K.mean(K.square(y_pred - y_true)))


def build_model():
    model_ = keras.Sequential([
        #         layers.Reshape((size,size,row,),input_shape=(size,size,row)),
        layers.Conv2D(input_shape=[size, size, row], filters=32, kernel_size=[5, 5], padding="same",
                      activation='relu'),
        layers.Conv2D(filters=32, kernel_size=[5, 5]),
        layers.Dropout(0.5),
        layers.MaxPool2D(pool_size=[2, 2], strides=2),
        layers.Conv2D(input_shape=[size, size, row], filters=64, kernel_size=[5, 5], padding="same",
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
    optimizer = keras.optimizers.Adamax()

    model_.compile(loss=keras.losses.mean_absolute_percentage_error,
                   optimizer=optimizer,
                   metrics=[keras.metrics.binary_accuracy,
                            'mean_absolute_error', 'mean_squared_error', root_mean_squared_error,
                            equal_pred])
    return model_


if df_is_panda:
    for source in sources:
        fileToObjects.check_xyz_file(source)
model = build_model()
model.summary()
gen = file_execute(sources[0:-3], train_model_config, panda=df_is_panda)
gen_validator = file_execute(sources[-3:], train_model_config, panda=df_is_panda,
                             limit=train_model_config["steps_per_epoch"] * train_model_config["epochs"] * 0.25)
tb = keras.callbacks.tensorboard_v1.TensorBoard()

save_string = '-'.join([f'{key}-{value}' for key, value in train_model_config.items()])
if "save_to_backup" in train_model_config and train_model_config["save_to_backup"]:
    save_string = fileToObjects.models_map + save_string

try:
    check_path = fileToObjects.check_path(save_string + '.h5')
    print('cp', check_path)
    if check_path is None:
        history = model.fit_generator(gen,
                                      steps_per_epoch=train_model_config["steps_per_epoch"],
                                      epochs=train_model_config["epochs"],
                                      max_queue_size=train_model_config["max_queue_size"],
                                      #                               # validation_data=gen_validator,
                                      #                               # validation_steps=train_model_config["steps_per_epoch"] / 4,
                                      callbacks=[tb])
        model.save(save_string + '.h5')
    else:
        model = load_model(save_string + '.h5', custom_objects={"root_mean_squared_error": root_mean_squared_error,
                                                                "equal_pred": equal_pred})
    score = model.evaluate_generator(generator=gen_validator,
                                     steps=train_model_config["steps_per_epoch"] * train_model_config[
                                         "steps_per_epoch"] / 4, verbose=1)

    print(save_string)
    import pandas as pd

    data_ = list(score)
    data_.insert(0, train_model_config["webmap_name"])
    data_.insert(1, train_model_config["layer_name"])
    data_.insert(2, train_model_config['limit_depth'])

    results = pd.DataFrame(data=[data_],
                           columns=['webmap', 'layer', 'range'] + model.metrics_names)
    results.to_csv('results.csv', mode='a', header=False, index=False)
    print(score)
except KeyboardInterrupt:
    pass
