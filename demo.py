from data_resources import fileToObjects
from map_based_resources import transformObjects, mapResources

configuration = mapResources.MapResources()
standardized_rendering_pixel_size = configuration.standardized_rendering_pixel_size

coordinates = transformObjects.get_datapoints_from_json(fileToObjects.open_json_file('coordinates.json'))

len(configuration.get_images(coordinates[0]))
