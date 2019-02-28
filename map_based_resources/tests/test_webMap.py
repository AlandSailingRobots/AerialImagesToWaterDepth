import unittest
from map_based_resources.webMap import WebMapService


def test_web_map(json_name):
    webMap = WebMapService(json_name)
    return webMap


class MyTestCase(unittest.TestCase):

    def test_correct_json(self):
        json_object = {
            "name": "something",
            "url": "https://avoin-karttakuva.maanmittauslaitos.fi/avoin/wmts",
            "set_name": "ETRS-TM35FIN",
            "map_layers": [
                {
                    "name": "orto",
                    "layer": "ortokuva"
                }
            ]
        }
        web_map = test_web_map(json_object)
        self.assertEqual(json_object['name'], web_map.name)
        self.assertEqual(json_object['url'], web_map.url)
        self.assertEqual(json_object['set_name'], web_map.set_name)
        self.assertEqual(len(json_object['map_layers']), len(web_map.map_layers))
        self.assertIsNotNone(web_map.tile_service)
        for i in range(len(json_object["map_layers"])):
            layer = json_object["map_layers"][i]
            self.assertEqual(web_map.map_layers[i].name, layer["name"])
            self.assertEqual(web_map.map_layers[i].layer, layer["layer"])


if __name__ == '__main__':
    unittest.main()
