import geopandas as gpd
import json
import urllib.parse
from shapely.geometry import Polygon

from map_based_resources import point

defaultCrs = 4326
defaultEPSG = f"EPSG:{defaultCrs}"
boundingBoxCrs = {'init': defaultEPSG.lower()}
osm_finland = {
    'url': "http://avaa.tdata.fi/geoserver/osm_finland/ows?",
    'version': '1.3.0',
    'typeName': 'osm_finland:sea_detailed'
}
water_depth = {
    'url': "https://julkinen.vayla.fi/inspirepalvelu/rajoitettu/wfs?",
    'version': '2.0.0',
    'typeName': 'rajoitettu:syvyysalue_a'
}
default_params = {"service": "WFS",
                  "request": "GetFeature",
                  "maxFeatures": 10,
                  "srsName": defaultEPSG,
                  "bbox": None,
                  "outputFormat": "application/json"}


class GeoJsonHandler:
    jsonData = None

    def doAction(self, path, jsonData):
        self.jsonData = jsonData
        calls = {
            "getGeoJson": self.readGeoJson,
            "getLocalGeoJson": self.readLocalGeoJson,
            "getWaterDepthAreas": self.getWaterDepth,
            "getWaterDepthPoints": self.calculateDepthPoints
        }
        action = calls.get(path[1], self.getPoints)
        return action()

    def make_point_from_json(self, data, item):
        point_ = point.DataPoint(latitude=data['box'][item]['lat'], longitude=data['box'][item]['lng'],
                                 coordinate_type=data['crs'].lower(), level=data['zoom'])
        point_.convert_coordinate_systems(save_in_point=True)
        return point_

    def create_query_url(self, properties, box):
        sw = self.make_point_from_json(box, 'sw')
        ne = self.make_point_from_json(box, 'ne')
        bbox = "{0},{1},{2},{3}".format(sw.x, sw.y, ne.x, ne.y)
        params = default_params
        params.update(properties)
        params['bbox'] = bbox
        return params.pop('url') + urllib.parse.urlencode(params)

    def readGeoJson(self, minimalize=False):
        box = self.jsonData
        query = self.create_query_url(osm_finland, box)
        print(query)
        return self.readGeoPanda(query, box, minimalize).to_json()

    def readLocalGeoJson(self):
        return self.readGeoJson(True)

    def readGeoPanda(self, url, box, minimalize=False):
        df_retrieved = gpd.read_file(url)
        if minimalize:
            df_retrieved = self.getMinimalized(df_retrieved, box, df_retrieved.crs)
        return df_retrieved

    def getWaterDepth(self, retrieve_json=True):
        box = self.jsonData
        query = self.create_query_url(water_depth, box)
        print(query)
        df_retrieved = self.readGeoPanda(query, box, True)
        print(box)
        if 'extra' in box.keys() and 'limitDepth' in box['extra'].keys():
            print('limiting from', len(df_retrieved), box['extra']['limitDepth'])
            df_retrieved = df_retrieved[df_retrieved['MAXDEPTH'] <= float(box['extra']['limitDepth'])]
            print('limited to', len(df_retrieved))
        if retrieve_json:
            return df_retrieved.to_json()
        else:
            return df_retrieved

    def createPoint(self, item, swap=False):
        direction = ['lng', 'lat']
        if swap:
            direction.reverse()
            print(direction)

        return float(item[direction[0]]), float(item[direction[1]])

    def getCurrentBoundingBox(self, box, crs=None, swap_coordinates=False):
        polygonBox = []
        for name in ['ne', 'nw', 'sw', 'se']:
            polygonBox.append(self.createPoint(box['box'][name], swap_coordinates))
        df = gpd.GeoDataFrame(geometry=gpd.GeoSeries([Polygon(polygonBox)]))
        if crs is None:
            crs = boundingBoxCrs
        df.crs = crs
        return df

    def calculateDepthPoints(self):
        df = self.getWaterDepth(False)
        df = self.getMinimalized(df, self.jsonData)
        bounds = self.create_points_dict()
        points = []
        origin_point = bounds['nw']
        distance_between_points = bounds['ne'].calculate_distance_to_point(bounds['nw']) / 100
        print(distance_between_points)
        long_point = origin_point
        new_point = origin_point
        number_of_points_checked = 0
        append = points.append
        contains = df.geometry.contains
        lat_check = bounds['se'].y
        long_check = bounds['ne'].x
        distance_between_points = origin_point.circle_distance(float(distance_between_points.km))
        print('long', long_check, 'lat', lat_check)
        while new_point.x <= long_check:
            while new_point.y >= lat_check:
                if contains(new_point).any():
                    append(new_point)
                number_of_points_checked += 1
                new_point = new_point.create_neighbouring_point(distance_between_points, 180)
            long_point = long_point.create_neighbouring_point(distance_between_points, 90)
            new_point = long_point
        print(len(points), number_of_points_checked)

    def getMinimalized(self, df_retrieved, box, crs=None):
        return gpd.overlay(df_retrieved, self.getCurrentBoundingBox(box, crs), how='intersection')

    def create_points_dict(self):
        points_dict = dict()
        json_data = self.jsonData
        for item in json_data['box']:
            points_dict[item] = self.make_point_from_json(json_data, item).convert_coordinate_systems(
                destination=defaultEPSG, return_point=True)
        return points_dict

    def getPoints(self):
        points_dict = self.create_points_dict()
        print(points_dict['nw'].calculate_distance_to_point(points_dict['ne']) / 2)
        listed_points = []
        for key in points_dict.keys():
            point = points_dict[key].convert_coordinate_systems(destination=defaultEPSG, return_point=True)
            listed_points.append({"key": key, "point": point.__dict__})
        return json.dumps(listed_points)
