import unittest

from map_based_resources import mapResources, singleTile, point


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.configuration = mapResources.MapResources()
        self.coordinate = point.DataPoint(latitude=60.062936,
                                          longitude=19.968358,
                                          level=15,
                                          coordinate_type="epsg:4326")
        self.specific = {"webmap_name": "ava",
                         "layer_name": "ava_infrared"}

    def test_single_image(self):
        result = singleTile.get_image_and_plot(self.coordinate, self.configuration, specific=self.specific)
        self.assertEqual(len(result.image_points), 1)

    def test_all_image(self):
        result = singleTile.get_image_and_plot(self.coordinate, self.configuration, show=False)
        self.assertEqual(len(result.image_points), 7)

    if __name__ == '__main__':
        unittest.main()
