from data_resources import fileToObjects
from multiprocessing import Process, Lock
import random

from map_based_resources import point, singleTile, mapResources


def get_cropped_images_from_file(arr, cropped_size=2, lock=None):
    file, source, config = arr
    index_ = 0
    for line in file:
        line_s = line.strip().split(' ')
        coordinate = point.DataPoint(float(line_s[1]),
                                     float(line_s[0]),
                                     source['coordinate_system'],
                                     15)
        del line_s
        singleTile.get_image_and_plot(coordinate, config, show=False, specific=3).get_cropped_image_single(cropped_size,
                                                                                                           0, lock)
        index_ += 1
        del coordinate
        if (index_ % 1000) is 0:
            config.clear_images()


def execution(file, source, config, cropped_size, lock=None):
    print('Executing:', source['name'])
    get_cropped_images_from_file((file, source, config), cropped_size, lock)


def create_process(source, cropped_size, lock):
    file = open(fileToObjects.check_path(source['path']))
    configuration = mapResources.MapResources()
    return Process(target=execution, args=(file, source, configuration, cropped_size, lock))


sources = fileToObjects.get_data(fileToObjects.DatasourceType.height_corrected)
lock_ = Lock()
list_of_processes = []
cropped_size_point = 10
amount_executed_parallel = 5

for i in range(amount_executed_parallel):
    list_of_processes.append(
        create_process(sources.pop(random.randint(0, len(sources) - 1)), cropped_size_point, lock_))
    list_of_processes[-1].start()

while len(list_of_processes) is not 0:
    if amount_executed_parallel > len(list_of_processes) > 0:
        list_of_processes.append(
            create_process(sources.pop(random.randint(0, len(sources) - 1)), cropped_size_point, lock_))
        list_of_processes[-1].start()

    for item in list_of_processes:
        if not item.is_alive():
            list_of_processes.remove(item)
