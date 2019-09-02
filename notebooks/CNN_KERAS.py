#! /usr/bin/env python
import tensorflow as tf
import keras
from keras import layers
from data_resources import fileToObjects, singleTile
from map_based_resources import point
import numpy as np
import pandas as pd

sources = fileToObjects.get_data(fileToObjects.DatasourceType.csv)
source = sources[0]

previous_mode = None


def line_execute(line, configuration, panda=False):
    global previous_mode
    if panda:
        line_s = line
    else:
        line_s = line.strip().split(',')
    coordinate = point.DataPoint(float(line_s[1]),
                                 float(line_s[0]),
                                 source['coordinate_system'],
                                 15)
    coordinate_tile = singleTile.get_image_and_plot(coordinate, configuration, show=False, specific=3)
    image = coordinate_tile.get_cropped_image_single(2, 0)
    if previous_mode is None:
        previous_mode = image.mode
    if image.mode != previous_mode:
        image = image.convert(previous_mode)

    image_arr = np.array(image)

    image.close()
    height = float(line_s[-1])
    return (image_arr, round(height, 1))


def file_execute(files, amount, yielded=True):
    images = []
    labels = []
    print(len(files))
    counter_file = 0
    for file in files:
        counter_file += 1
        print(counter_file, file['path'])
        file = open(fileToObjects.check_path(file['path']))
        index = 0
        configuration = fileToObjects.get_configuration()
        for line in file:
            image, depth = line_execute(line, configuration)
            images.append(image)
            labels.append(depth)
            index += 1
            if index % 10 == 0:
                if yielded:
                    #                     print(images[0].shape)
                    yield (np.array(images), np.array(labels))
                    images.clear()
                    labels.clear()
                configuration.clear_images()
        file.close()
        print(counter_file, index)
        print(len(images), len(labels))
        yield (np.array(images), np.array(labels))
        images.clear()
        labels.clear()
        configuration.clear_images()


def panda_execute(amount, yielded=True):
    images = []
    labels = []
    counter_file = 0
    configuration = fileToObjects.get_configuration()
    index = 0
    print('opening file')
    big = pd.read_csv(fileToObjects.check_path(source['path']), names=['x', 'y', 'height'])
    print(len(big))
    print('read in file')
    for row in big.sample(frac=amount).iterrows():
        image, depth = line_execute(row[1], configuration, panda=True)
        images.append(image)
        labels.append(depth)
        index += 1
        if index % 10 == 0:
            if yielded:
                #                     print(images[0].shape)
                yield (np.array(images), np.array(labels))
                images.clear()
                labels.clear()
            configuration.clear_images()
    print(counter_file, index)
    print(len(images), len(labels))
    yield (np.array(images), np.array(labels))
    images.clear()
    labels.clear()
    configuration.clear_images()


size = 16
row = 4


def build_model():
    model_ = keras.Sequential([
        #         layers.Reshape((size,size,row,),input_shape=(size,size,row)),
        layers.Conv2D(input_shape=[size, size, row], filters=32, kernel_size=[5, 5], padding="same",
                      activation=tf.nn.relu),
        layers.MaxPool2D(pool_size=[2, 2], strides=2),
        layers.Conv2D(input_shape=[size, size, row], filters=64, kernel_size=[5, 5], padding="same",
                      activation=tf.nn.relu),
        layers.MaxPool2D(pool_size=[2, 2], strides=2),
        layers.Dense(64, activation=tf.nn.relu),
        #         layers.Dropout(0.4),
        layers.Reshape((size * size * row,)),
        layers.Dense(size * size * 64),
        layers.Dropout(0.99),
        layers.Dense(size * 64),
        layers.Dropout(0.99),
        layers.Dense(64),
        layers.Dropout(0.99),
        layers.Dense(1)
    ])
    optimizer = keras.optimizers.Adamax()

    model_.compile(loss=tf.losses.mean_squared_error,
                   optimizer=optimizer,
                   metrics=[keras.metrics.binary_accuracy, 'mean_absolute_error', 'mean_squared_error'])
    return model_


model = build_model()
model.summary()
gen = file_execute([source], None)

# gen = file_execute(sources[0:50], None)

# gen = panda_execute(0.5)

history = model.fit_generator(gen, steps_per_epoch=100, epochs=10, max_queue_size=100)
model.save('image_5_size_5_steps_1000_epochs_100.h5')
