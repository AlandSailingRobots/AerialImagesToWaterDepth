from owslib.wmts import WebMapTileService


class WebMap:
    class MapLayer:
        def __init__(self, name, layer, split):
            self.name = name
            self.layer = layer
            self.split = split

    def __init__(self, json_object):
        self.name = json_object["name"]
        self.ignore = "ignore" in json_object
        self.url = json_object["url"]
        self.set_name = json_object["set_name"]
        self.map_layers = list()
        self.special_level = "special_level" in json_object
        for layer in json_object["map_layers"]:
            self.map_layers.append(self.MapLayer(layer["name"], layer["layer"], "split" in layer))
        if not self.ignore:
            self.tile_service = WebMapTileService(self.url)
