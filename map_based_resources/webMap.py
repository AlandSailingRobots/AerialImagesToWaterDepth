from owslib.wmts import WebMapTileService


class MapLayer:
    def __init__(self, name, layer, split):
        self.name = name
        self.layer = layer
        self.split = split
        self.already_splitted = False
        self.row = None
        self.column = None
        self.tile_level = None

    def add_position_on_layer(self,row, column):
        self.row = row
        self.column = column


class WebMap:

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

    def get_info(self, map_layer):
        wmts = self.tile_service
        print('possible maps:', list(wmts.contents.keys()))
        print('possible coordinate system:', list(wmts.tilematrixsets.keys()))
        print('possible formats :', list(wmts.contents[map_layer].formats))
        print('length of the formats', len(wmts.tilematrixsets[self.set_name].tilematrix))
        print('length of the formats', wmts.tilematrixsets[self.set_name].tilematrix)
