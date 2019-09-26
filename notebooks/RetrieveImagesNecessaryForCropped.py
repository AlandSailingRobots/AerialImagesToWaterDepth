from data_resources import fileToObjects, DataSourcesTypes
from multiprocessing import Process, Lock
import random

from map_based_resources import point, singleTile, mapResources


def get_cropped_images_from_file(arr, model_config, lock=None):
    file, source, config = arr
    index_ = 0
    for line in file:
        line_s = line.strip().split(' ')
        coordinate = point.DataPoint(float(line_s[1]),
                                     float(line_s[0]),
                                     source['coordinate_system'],
                                     15)
        del line_s
        singleTile.get_image_and_plot(coordinate, config, show=False,
                                      specific=model_config).get_cropped_image_single(model_config["size_in_meters"],
                                                                                      lock=lock)
        index_ += 1
        del coordinate
        if (index_ % 1000) is 0:
            config.clear_images()


def execution(file, source, config, model_config, lock=None):
    print('Executing:', source['name'])
    get_cropped_images_from_file((file, source, config), model_config, lock)


def create_process(source, model_config, lock):
    file = open(fileToObjects.check_path(source['path']))
    configuration = mapResources.MapResources()
    return Process(target=execution, args=(file, source, configuration, model_config, lock))


sources = fileToObjects.get_data(DataSourcesTypes.DataSourceEnum.height_corrected)
lock_ = Lock()
list_of_processes = []
train_model_config = fileToObjects.open_json_file("machine_learning/train_models.json")[0]
amount_executed_parallel = 5

for i in range(amount_executed_parallel):
    list_of_processes.append(
        create_process(sources.pop(random.randint(0, len(sources) - 1)), train_model_config, lock_))
    list_of_processes[-1].start()

while len(list_of_processes) is not 0:
    if amount_executed_parallel > len(list_of_processes) > 0:
        list_of_processes.append(
            create_process(sources.pop(random.randint(0, len(sources) - 1)), train_model_config, lock_))
        list_of_processes[-1].start()

    for item in list_of_processes:
        if not item.is_alive():
            list_of_processes.remove(item)
