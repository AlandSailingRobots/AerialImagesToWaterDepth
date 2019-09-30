#! /usr/bin/env python
import keras
from keras import layers

from data_resources import fileToObjects, DataSourcesTypes
from map_based_resources import point, singleTile, mapResources
import numpy as np

sources = fileToObjects.get_data(DataSourcesTypes.DataSourceEnum.open_source)
train_model_config = fileToObjects.open_json_file("machine_learning/train_models.json")[1]
source = sources[0]

previous_mode = "RGBA"


def line_execute(line, configuration, panda=False):
    global previous_mode
    if panda:
        line_s = line
    else:
        line_s = line.strip().split(',')
    coordinate = point.DataPoint(float(line_s[1]),
                                 float(line_s[0]),
                                 source['coordinate_system'],
                                 train_model_config["level"])
    coordinate_tile = singleTile.get_image_and_plot(coordinate, configuration, show=False,
                                                    specific=train_model_config)
    image = coordinate_tile.get_cropped_image_single(train_model_config["size_in_meters"])
    if previous_mode is None:
        previous_mode = image.mode
    if image.mode != previous_mode:
        image = image.convert(previous_mode)

    image_arr = np.array(image)

    image.close()
    height = float(line_s[-1])
    return image_arr, round(height, 1)


def file_execute(files):
    counter_file = 0
    configuration = mapResources.MapResources()
    for file in files:
        counter_file += 1
        print(counter_file, file['path'])
        file = open(fileToObjects.check_path(file['path']))
        index = 0
        for line in file:
            image, depth = line_execute(line, configuration)
            index += 1
            yield (np.array([image]), np.array([depth]))
            if index % 10 == 0:
                configuration.clear_images()
        file.close()
        configuration.clear_images()


def panda_execute(files, limit_depth=None):
    configuration = mapResources.MapResources()
    index = 0
    for file in files:
        big = fileToObjects.open_xyz_file_as_panda(file)
        if limit_depth is not None:
            big = big[big['height'] >= limit_depth]
        for df_row in big.itertuples(index=False, name=None):
            image, depth = line_execute(df_row, configuration, panda=True)
            yield np.array([image]), np.array([depth])
            index += 1
            if index % 10 == 0:
                configuration.clear_images()
        configuration.clear_images()


size = train_model_config["size_in_meters"] * train_model_config["pixels_per_meter"]
row = 4


def build_model():
    model_ = keras.Sequential([
        #         layers.Reshape((size,size,row,),input_shape=(size,size,row)),
        layers.Conv2D(input_shape=[size, size, row], filters=32, kernel_size=[5, 5], padding="same",
                      activation='relu'),
        layers.MaxPool2D(pool_size=[2, 2], strides=2),
        layers.Conv2D(input_shape=[size, size, row], filters=64, kernel_size=[5, 5], padding="same",
                      activation='relu'),
        layers.MaxPool2D(pool_size=[2, 2], strides=2),
        layers.Dense(64, activation='relu'),
        #         layers.Dropout(0.4),
        layers.Reshape((size * size * row,)),
        layers.Dense(size * size * 64),
        layers.Dropout(0.5),
        layers.Dense(size * 64),
        layers.Dropout(0.5),
        layers.Dense(64),
        layers.Dropout(0.5),
        layers.Dense(1)
    ])
    optimizer = keras.optimizers.Adamax()

    model_.compile(loss=keras.losses.mean_squared_error,
                   optimizer=optimizer,
                   metrics=[keras.metrics.binary_accuracy, 'mean_absolute_error', 'mean_squared_error'])
    return model_


for source in sources:
    fileToObjects.check_xyz_file(source)
model = build_model()
model.summary()
gen = panda_execute(sources[0:5], limit_depth=train_model_config['limit_depth'])

# gen = file_execute(sources[0:50], None)

try:
    history = model.fit_generator(gen,
                                  steps_per_epoch=train_model_config["steps_per_epoch"],
                                  epochs=train_model_config["epochs"],
                                  max_queue_size=train_model_config["max_queue_size"])
except KeyboardInterrupt:
    pass

save_string = '-'.join([f'{key}-{value}' for key, value in train_model_config.items()])
if "save_to_backup" in train_model_config and train_model_config["save_to_backup"]:
    save_string = fileToObjects.models_map + save_string
model.save(save_string + '.h5')
