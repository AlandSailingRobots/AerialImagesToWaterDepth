from webMap import WebMap


class MapResources:
    def __init__(self, config):
        self.standardized_rendering_pixel_size = config["standardized_rendering_pixel_size"]
        self.web_maps = list()
        for wmts in config["wmts"]:
            self.web_maps.append(WebMap(wmts))
