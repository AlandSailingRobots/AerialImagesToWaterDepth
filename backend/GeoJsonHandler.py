import geopandas as gpd
import json
import urllib.parse
from shapely.geometry import Polygon, Point

from backend.PostGisHandler import PostGisHandler
from data_resources import fileToObjects
from map_based_resources import point

server_settings = fileToObjects.open_json_file('backend/server_settings.json')["GeoJson"]


class GeoJsonHandler:

    def __init__(self) -> None:
        super().__init__()
        self.PostGisConnection = PostGisHandler()
        self.jsonData = None

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
        params = server_settings["default_params"]
        params.update(properties)
        params['bbox'] = bbox
        return params.pop('url') + urllib.parse.urlencode(params)

    def readGeoJson(self, minimalize=False):
        box = self.jsonData
        query = self.create_query_url(server_settings["osm_finland"], box)
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
        query = self.create_query_url(server_settings["water_depth"], box)
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

    def getCurrentBoundingBox(self, box, crs=None, swap_coordinates=False, get_poly=False):
        polygonBox = []
        for name in ['ne', 'nw', 'sw', 'se']:
            polygonBox.append(self.createPoint(box['box'][name], swap_coordinates))
        if get_poly:
            return Polygon(polygonBox)
        df = gpd.GeoDataFrame({'zoom_level': [self.jsonData["zoom"]], 'geometry': [Polygon(polygonBox)]})
        if crs is None:
            crs = server_settings["boundingBoxCrs"]
        df.crs = crs
        return df

    def calculateDepthPoints(self):
        # First check if the current area is already calculated:
        print(self.jsonData)
        # Create Polygon from current bounding box
        df = self.getCurrentBoundingBox(self.jsonData, self.jsonData["crs"], swap_coordinates=False)
        bounds = df.bounds
        crs = int(df.crs.split(':')[1])
        # Get all the polygons where the boundingbox overlaps with
        print('df', len(df))
        df_envelope = self.PostGisConnection.get_envelope("test_polygon",
                                                          df.bounds,
                                                          int(df.crs.split(':')[1]),
                                                          int(self.jsonData["zoom"]))
        # Get all the areas in the bounding box which are not calculated yet.

        if df_envelope is not None and len(df_envelope) != 0:
            print('overlay starting')
            df = gpd.overlay(df_envelope, df, how='difference')
            print('overlay done', len(df))
        print('df', len(df))
        if len(df) != 0:
            geo_list, new_point = self.check_points(df)
            points_df = gpd.GeoDataFrame({'zoom_level': [self.jsonData["zoom"]] * len(geo_list), 'geometry': geo_list})
            points_df.crs = df.crs
            self.PostGisConnection.put_into_table(points_df, "Point", 'test_points', create_table=True)
            self.PostGisConnection.put_into_table(df, "Polygon", 'test_polygon', create_table=True,
                                                  if_exists_action='replace')

        df_all_points = self.PostGisConnection.get_envelope("test_points",
                                                            bounds,
                                                            crs,
                                                            int(self.jsonData["zoom"]))

        return df_all_points.to_json()

    def check_points(self, df):
        bounds = self.create_points_dict()
        origin_point = bounds['nw'].reduceDecimals()
        distance_between_points_km = bounds['ne'].calculate_distance_to_point(origin_point) / 100
        # Distance between the points differs per level. this so that the amount of points is always the same and
        # reduces load.
        long_point = origin_point
        new_point = origin_point
        number_of_points_checked = 0
        contains = df.geometry.contains
        lat_check = bounds['se'].reduceDecimals().y
        long_check = bounds['ne'].reduceDecimals().x
        distance_between_points = origin_point.circle_distance(float(distance_between_points_km.km))
        geo_list = []
        while new_point.x <= long_check:
            while new_point.y >= lat_check:
                if contains(new_point).any():
                    local = Point(new_point.x, new_point.y)
                    geo_list.append(local)
                number_of_points_checked += 1
                new_point = new_point.create_neighbouring_point(distance_between_points, 180)
            long_point = long_point.create_neighbouring_point(distance_between_points, 90)
            new_point = long_point
        print(len(geo_list), number_of_points_checked)
        df_ = gpd.GeoDataFrame(geometry=geo_list)
        print('compare', len(df_[df_.intersects(df)]), len(geo_list))
        return geo_list, new_point

    def getMinimalized(self, df_retrieved, box, crs=None, method_overlay='intersection'):
        return gpd.overlay(df_retrieved, self.getCurrentBoundingBox(box, crs), how=method_overlay)

    def create_points_dict(self):
        points_dict = dict()
        json_data = self.jsonData
        for item in json_data['box']:
            points_dict[item] = self.make_point_from_json(json_data, item).convert_coordinate_systems(
                destination=server_settings["defaultEPSG"], return_point=True)
        return points_dict

    def getPoints(self):
        points_dict = self.create_points_dict()
        listed_points = []
        for key in points_dict.keys():
            point_ = points_dict[key].convert_coordinate_systems(destination=server_settings["defaultEPSG"],
                                                                 return_point=True)
            listed_points.append({"key": key, "point": point_.__dict__})
        return json.dumps(listed_points)
