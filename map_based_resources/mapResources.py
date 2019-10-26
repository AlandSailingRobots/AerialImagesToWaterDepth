import io
from typing import List, Set, Any

from data_resources import fileToObjects
from PIL import Image
from owslib.wmts import WebMapTileService

from map_based_resources import singleTile


class ImageTile:
    column: int
    image: Image
    layer_name: str
    level: int
    row: int
    tile: Any

    def __init__(self, tile, layer_name, level, row, column, image=None):
        self.tile = tile
        self.layer_name = layer_name
        self.level = level
        self.row = row
        self.column = column
        self.image = image

    def read_and_save(self, lock=None):
        tile_bytes = self.tile.read()
        image_stream = io.BytesIO(tile_bytes)
        self.image = Image.open(image_stream)
        fileToObjects.save_image(self.image, self.layer_name, self.level, self.row, self.column, lock)
        del image_stream
        del tile_bytes

    def save_image(self, lock):
        self.read_and_save(lock)
        self.image.close()

    def get_image_from_tile(self, lock=None):
        if self.image is None:
            self.read_and_save(lock)
        return self.image


class MapLayer:
    already_splitted: bool
    image_tiles: Set[ImageTile]
    images_gotten: Set[tuple]
    layer: str
    level: int
    name: str
    original_layer: str
    pixel_size: float
    split: bool
    coordinate_system: str

    def __init__(self, dict_item):
        self.name = dict_item['name']
        self.layer = dict_item['layer']
        self.split = 'split' in dict_item
        if 'coordinate_system' in dict_item:
            self.coordinate_system = dict_item['coordinate_system']
        else:
            self.coordinate_system = None
        self.already_splitted = False
        self.original_layer = dict_item['layer']
        self.pixel_size = None
        self.image_tiles = set()
        self.images_gotten = set()
        self.level = None

    def add_image_gotten(self, image_tile: ImageTile):
        self.images_gotten.add((image_tile.level, image_tile.row, image_tile.column))

    def add_image_tile(self, image_tile: ImageTile):
        self.add_image_gotten(image_tile)
        self.image_tiles.add(image_tile)

    def image_tile_in_layer(self, level, row, column):
        found = (level, row, column) in self.images_gotten
        return found

    def get_image_tile(self, level, row, column):
        for item in self.image_tiles:
            if item.level == level and item.row == row and item.column == column:
                return item
        return None

    def clear_images(self):
        for image_tile in self.image_tiles:
            if image_tile.image is not None:
                image_tile.image.close()
        self.image_tiles.clear()
        self.images_gotten.clear()


class MapService:
    ignore: bool
    map_layers: List[MapLayer]
    name: str
    set_name: str
    special_level: bool
    tile_service: WebMapTileService
    special_level: bool
    coordinate_system: str

    def __init__(self, json_object):
        self.name = json_object["name"]
        self.ignore = "ignore" in json_object
        self.set_name = json_object["set_name"]
        self.map_layers = list(
            MapLayer(layer) for layer in json_object["map_layers"])
        self.special_level = "special_level" in json_object
        if "coordinate_system" in json_object:
            self.coordinate_system = json_object['coordinate_system']
        else:
            self.coordinate_system = None
        if not self.ignore:
            self.tile_service = WebMapTileService(json_object["url"])

    def get_info(self, map_layer):
        wmts = self.tile_service
        print('possible maps:', list(wmts.contents.keys()))
        print('possible coordinate system:', list(wmts.tilematrixsets.keys()))
        print('possible formats :', list(wmts.contents[map_layer].formats))
        print('length of the formats', len(wmts.tilematrixsets[self.set_name].tilematrix))
        print('length of the formats', wmts.tilematrixsets[self.set_name].tilematrix)

    def clear_images(self):
        for i in range(len(self.map_layers)):
            self.map_layers[i].clear_images()


class MapResources:
    standardized_rendering_pixel_size: float
    web_maps: List[MapService]

    def __init__(self):
        config = fileToObjects.get_wmts_config_from_json()
        self.standardized_rendering_pixel_size = config["standardized_rendering_pixel_size"]
        self.web_maps = list(MapService(wmts) for wmts in config["wmts"])

    def get_coordinate_system(self, web_map_name):
        for web_map in self.web_maps:
            if web_map.name == web_map_name:
                return web_map.coordinate_system

    def clear_images(self):
        for i in range(len(self.web_maps)):
            self.web_maps[i].clear_images()

    def get_images(self, coordinate, show=False, size_in_meters=2):
        return singleTile.get_image_and_plot(coordinate, self, show=show, specific=None).get_cropped_images(
            size=size_in_meters)

    def get_image(self, coordinate, show=False, specific=None):
        return singleTile.get_image_and_plot(coordinate, self, show=show, specific=specific).get_cropped_image_single(
            specific["size_in_meters"])
