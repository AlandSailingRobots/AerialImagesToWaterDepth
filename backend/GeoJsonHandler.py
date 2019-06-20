from map_based_resources import point
import geopandas as gpd
from shapely.geometry import Polygon
import json
import urllib.parse

defaultCrs = 4326
boundingBoxCrs = {'init': f'epsg:{defaultCrs}'}
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
                  "maxFeatures": "10",
                  "srsName": "EPSG:4326",
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
        }

        splitted_path = path.strip().split('/')
        call = splitted_path[1]
        action = calls.get(call, self.getPoints)
        return action()

    def make_point_from_json(self, data, item):
        point_ = point.DataPoint(latitude=data['box'][item]['lat'], longitude=data['box'][item]['lng'],
                                 coordinate_type=data['crs'].lower(), level=data['zoom'])
        point_.convert_coordinate_systems(save_in_point=True)
        return point_

    def create_query_url(self, properties, box):
        sw = self.make_point_from_json(box, 'sw')
        ne = self.make_point_from_json(box, 'ne')
        bbox = "{0},{1},{2},{3}".format(sw.longitude, sw.latitude, ne.longitude, ne.latitude)
        params = default_params
        params.update(properties)
        print(type(bbox), bbox)
        params['bbox'] = bbox
        print(params)
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

    def getWaterDepth(self):
        box = self.jsonData
        query = self.create_query_url(water_depth, box)
        print(query)
        df_retrieved = self.readGeoPanda(query, box, True)
        print(box)
        if 'extra' in box.keys() and 'limitDepth' in box['extra'].keys():
            print('limiting from', len(df_retrieved), box['extra']['limitDepth'])
            df_retrieved = df_retrieved[df_retrieved['MAXDEPTH'] <= float(box['extra']['limitDepth'])]
            print('limited to', len(df_retrieved))
        return df_retrieved.to_json()

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

    def getMinimalized(self, df_retrieved, box, crs=None):
        return gpd.overlay(df_retrieved, self.getCurrentBoundingBox(box, crs), how='intersection')

    def getPoints(self):
        points_dict = dict()
        json_data = self.jsonData
        for item in json_data['box']:
            points_dict[item] = self.make_point_from_json(json_data, item)
        print(points_dict['nw'].calculate_distance_to_point(points_dict['ne']) / 2)
        listed_points = []
        for key in points_dict.keys():
            point = points_dict[key].convert_coordinate_systems(destination='EPSG:4326', return_point=True)
            listed_points.append({"key": key, "point": point.__dict__})
        return json.dumps(listed_points)
