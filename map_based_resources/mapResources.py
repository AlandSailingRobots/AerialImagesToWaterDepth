import io
from data_resources import fileToObjects
from PIL import Image
from owslib.wmts import WebMapTileService


class ImageTile:

    def __init__(self, tile, layer_name, level, row, column, image=None):
        self.tile = tile
        self.layer_name = layer_name
        self.level = level
        self.row = row
        self.column = column
        self.image = image

    def save_image(self, lock):
        tile_bytes = self.tile.read()
        image_stream = io.BytesIO(tile_bytes)
        self.image = Image.open(image_stream)
        fileToObjects.save_image(self.image, self.layer_name, self.level, self.row, self.column, lock)
        self.image.close()
        del image_stream
        del tile_bytes

    def get_image_from_tile(self):
        if self.image is None:
            tile_bytes = self.tile.read()
            image_stream = io.BytesIO(tile_bytes)
            self.image = Image.open(image_stream)
            fileToObjects.save_image(self.image, self.layer_name, self.level, self.row, self.column)
        return self.image


class MapLayer:
    def __init__(self, name, layer, split):
        self.name = name
        self.layer = layer
        self.split = split
        self.already_splitted = False
        self.original_layer = layer
        self.pixel_size = None
        self.image_tiles = set()
        self.images_gotten = set()
        self.level = None

    def add_image_gotten(self, image_tile: ImageTile):
        self.images_gotten.add((image_tile.level, image_tile.row, image_tile.column))

    def add_image_tile(self, image_tile: ImageTile):
        self.image_tiles.add(image_tile)

    def image_tile_in_layer(self, level, row, column):
        found = (level, row, column) in self.images_gotten
        return found

    def get_image_tile(self, level, row, column):
        for item in self.image_tiles:
            if item.level == level and item.row == row and item.column == column:
                return item
        return None


class MapService:

    def __init__(self, json_object):
        self.name = json_object["name"]
        self.ignore = "ignore" in json_object
        self.url = json_object["url"]
        self.set_name = json_object["set_name"]
        self.map_layers = list(
            MapLayer(layer["name"], layer["layer"], "split" in layer) for layer in json_object["map_layers"])
        self.special_level = "special_level" in json_object
        if not self.ignore:
            self.tile_service = WebMapTileService(self.url)

    def get_info(self, map_layer):
        wmts = self.tile_service
        print('possible maps:', list(wmts.contents.keys()))
        print('possible coordinate system:', list(wmts.tilematrixsets.keys()))
        print('possible formats :', list(wmts.contents[map_layer].formats))
        print('length of the formats', len(wmts.tilematrixsets[self.set_name].tilematrix))
        print('length of the formats', wmts.tilematrixsets[self.set_name].tilematrix)


class MapResources:
    def __init__(self, config):
        self.standardized_rendering_pixel_size = config["standardized_rendering_pixel_size"]
        self.web_maps = list(MapService(wmts) for wmts in config["wmts"])
