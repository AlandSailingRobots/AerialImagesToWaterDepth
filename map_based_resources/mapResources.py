import io

from PIL import Image
from owslib.wmts import WebMapTileService


class ImageTile:

    def __init__(self, tile, level, row, column):
        self.tile = tile
        self.level = level
        self.row = row
        self.column = column

    def get_image_from_tile(self):
        tile_bytes = self.tile.read()
        image_stream = io.BytesIO(tile_bytes)
        return Image.open(image_stream)


class MapLayer:
    def __init__(self, name, layer, split):
        self.name = name
        self.layer = layer
        self.split = split
        self.already_splitted = False
        self.original_layer = layer
        self.pixel_size = None
        self.image_tiles = set()

    def __str__(self) -> str:
        return str(self.__class__) + ": " + str(self.__dict__)

    def __repr__(self):
        return repr(vars(self))

    def add_image_tile(self, image_tile: ImageTile):
        self.image_tiles.add(image_tile)

    def image_tile_in_layer(self, level, row, column):
        for item in self.image_tiles:
            if item.level == level and item.row == row and item.column == column:
                return True
        return False

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
        self.map_layers = list()
        self.special_level = "special_level" in json_object
        for layer in json_object["map_layers"]:
            self.map_layers.append(MapLayer(layer["name"], layer["layer"], "split" in layer))
        if not self.ignore:
            self.tile_service = WebMapTileService(self.url)

    def __str__(self) -> str:
        return str(self.__class__) + ": " + str(self.__dict__)

    def __repr__(self):
        return repr(vars(self))

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
        self.web_maps = list()
        for wmts in config["wmts"]:
            self.web_maps.append(MapService(wmts))
