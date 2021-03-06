#!/usr/bin/env python
# coding: utf-8
from data_resources import fileToObjects, DataSourcesTypes
from multiprocessing import Process, Lock

from map_based_resources import point, singleTile, mapResources

sources = fileToObjects.get_data(DataSourcesTypes.DataSourceEnum.height_corrected)
configuration = mapResources.MapResources()


def line_execute(line, lock):
    line_s = line.strip().split(' ')
    coordinate = point.DataPoint(float(line_s[1]),
                                 float(line_s[0]),
                                 source['coordinate_system'],
                                 15)
    del line_s
    singleTile.get_image_and_save(coordinate, configuration, lock)
    del coordinate


def source_execute(source_, lock):
    file = open(fileToObjects.check_path(source_['path']))
    for line in file:
        line_execute(line, lock)
    file.close()


image_lock = Lock()
for source in sources[1:]:
    Process(target=source_execute, args=(source, image_lock)).start()
