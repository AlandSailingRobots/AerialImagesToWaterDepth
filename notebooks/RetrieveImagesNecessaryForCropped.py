from data_resources import fileToObjects, transformObjects, singleTile
from multiprocessing import Process, Lock
import random


def get_train_test_split_from_df(arr, cropped_size=1, lock=None):
    df, source, config = arr
    for index_ in range(len(df)):
        coordinate = df.loc[index_]
        coordinate = transformObjects.get_data_point_from_row(
            coordinate, source['coordinate_system'], 15)
        singleTile.get_image_and_plot(
            coordinate, config, show=False).get_cropped_images(cropped_size, lock)
        if (index_ % 1000) is 0:
            config.clear_images()


def execution(df_, source, config, cropped_size, lock=None):
    print('Executing:', source['name'])
    get_train_test_split_from_df((df_, source, config), cropped_size, lock)


def create_process(source, cropped_size, lock):
    df_ = fileToObjects.open_xyz_file_as_panda(source)
    configuration = fileToObjects.get_configuration()
    return Process(target=execution, args=(df_, source, configuration, cropped_size, lock))


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

    for index in range(len(list_of_processes)):
        if not list_of_processes[index].is_alive():
            list_of_processes.pop(index)
