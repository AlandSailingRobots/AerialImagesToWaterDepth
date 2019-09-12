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
            "getWaterDepthLocal": self.getWaterDepth,
            "calculateWaterDepthPoints": self.calculateDepthPoints,
            "calculateProcess": self.addCalculateDepthPointsProces,
            "getWaterDepthPoints": self.getDepthPoints,
            "getWaterDepthArea": self.getDepthArea,
            "getCurrentPolygon": self.get_current_polygon_df
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

    def readGeoJson(self):
        box = self.jsonData
        query = self.create_query_url(server_settings["osm_finland"], box)
        print(query)
        return self.readGeoPanda(query, box, "minimalised" in box["extra"]).to_json()

    def readGeoPanda(self, url, box, minimalised=False):
        df_retrieved = gpd.read_file(url)
        if minimalised:
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
        elif 'init' not in crs:
            crs = {'init': crs}
        df.crs = crs
        return df

    def getDepthArea(self):
        items = self.get_current_polygon_df(just_box=True)
        print('items', len(items))
        bounds, crs, df = items
        passed_bounds = bounds
        if df is not None and len(df) is not 0:
            passed_bounds = df.bounds
        limit, buffer = 2, 0.001 / 2
        print(buffer)
        if "boatDepth" in self.jsonData["extra"]:
            limit = self.jsonData["extra"]["boatDepth"]
        if "buffer" in self.jsonData["extra"]:
            buffer = self.jsonData["extra"]["buffer"]
        as_buffer = "zoom_level,depth,ST_Buffer(geom, {0}, 'endcap=square') as geom".format(buffer)
        operator = ">=" if "deeper" not in self.jsonData["extra"] else "<="
        polygon_points = self.getDepthPointsFromTable(crs,
                                                      passed_bounds,
                                                      as_buffer=as_buffer,
                                                      extra="AND depth {0} -{1} ".format(operator, limit))

        overlay = polygon_points.dissolve(by='zoom_level')
        properties_dict = {
            "stroke": "#555555",
            "stroke-width": 2,
            "stroke-opacity": 1,
            "fill": "#7987ff",
            "fill-opacity": 0.5}

        for key in properties_dict:
            overlay[key] = [properties_dict[key]] * len(overlay)
        print(overlay.crs)
        return overlay.to_json()

    def getDepthPoints(self, to_json=True):
        print('getting depth points')
        items = self.get_current_polygon_df()
        print('items', len(items))
        bounds, crs, df = items
        passed_bounds = bounds
        if df is not None and len(df) is not 0:
            passed_bounds = df.bounds
        df_all_points = self.getDepthPointsFromTable(crs, passed_bounds)
        if not to_json:
            return df_all_points
        return df_all_points.to_json()

    def getDepthPointsFromTable(self, crs, passed_bounds, extra=None, as_buffer=None):
        print('has extra', "extra" in self.jsonData, self.jsonData["extra"])
        has_depth = 'has_depth' in self.jsonData["extra"]
        all_higher_levels = 'higher_levels' in self.jsonData["extra"]
        print('has depth, higher_levels', has_depth, all_higher_levels)
        df_all_points = self.PostGisConnection.get_envelope(self.PostGisConnection.points_table,
                                                            passed_bounds,
                                                            crs,
                                                            int(self.jsonData["zoom"]),
                                                            has_depth=has_depth,
                                                            all_higher_levels=all_higher_levels,
                                                            extra=extra,
                                                            as_buffer=as_buffer)
        return df_all_points

    def calculateDepthPointsProces(self, jsonData):
        self.jsonData = jsonData
        self.calculateDepthPoints(return_=False)

    def addCalculateDepthPointsProces(self):
        self.PostGisConnection.put_into_calculation(self.jsonData)
        return json.dumps({'succes': True})

    def calculateDepthPoints(self, return_=True):
        bounds, crs, df = self.get_current_polygon_df(only_missing=True, just_box=True)
        geo_list = []
        if len(df) != 0:
            geo_list = self.check_points(df)
        # If there are points not calculated.
        if len(geo_list) != 0:
            calculate = "calculate" in self.jsonData["extra"]
            self.calculate_geolist_update_database(df, geo_list, calculate=calculate)
        if return_:
            return self.getDepthArea()

    def get_current_polygon_df(self, only_water=True, just_box=False, only_missing=False):
        # First check if the current area is already calculated:
        # Create Polygon from current bounding box
        df = self.getCurrentBoundingBox(self.jsonData, self.jsonData["crs"], swap_coordinates=False)
        print('only_water', only_water)
        if only_water:
            water_df = self.getWaterDepth(retrieve_json=False)
            print(df.crs, water_df.crs)
            print('df', len(df), 'water_df', len(water_df))
            df = gpd.overlay(water_df, df, how='intersection')
            df['zoom_level'] = [self.jsonData['zoom']] * len(df)
            print('zoomed', df.columns, len(df))

            df.drop(['zoom_level_1', 'id', 'HISOID', 'HGHTLAKE', 'MAXDEPTH', 'MINDEPTH',
                     'TYPEDEPR', 'CDATE', 'NTMENTRY', 'YEARSWEEP', 'IRROTUS_PVM',
                     'zoom_level_2'], inplace=True, axis=1)
            print('crimped')
        bounds = df.bounds
        crs = int(df.crs['init'].split(':')[1])
        # Get all the polygons where the boundingbox overlaps with
        print('df', len(df))
        df_envelope = self.PostGisConnection.get_envelope(self.PostGisConnection.polygon_table,
                                                          df.bounds,
                                                          crs,
                                                          int(self.jsonData["zoom"]))
        # Get all the areas in the bounding box which are not calculated yet.
        missing = "missing" in self.jsonData['extra']
        if only_missing:
            missing = only_missing
        if df_envelope is not None and len(df_envelope) != 0 and not just_box:
            print('overlay starting', len(df_envelope), len(df))
            how = "difference" if missing else "intersection"
            print('how', how)
            df = gpd.overlay(df_envelope, df, how=how)
            print('overlay done', len(df), df.columns)
        if "polybox" in self.jsonData['extra']:
            return df.to_json()
        return bounds, crs, df

    def post_points(self, crs, geo_, depths=None):
        geo_dict = {'zoom_level': [self.jsonData["zoom"]] * len(geo_),
                    'geometry': geo_}
        if depths is not None:
            geo_dict['depth'] = depths.flatten()
            print('depths.flatten')
        points_df = gpd.GeoDataFrame(geo_dict)
        points_df.crs = crs
        self.PostGisConnection.put_into_table(points_df, "Point", self.PostGisConnection.points_table,
                                              create_table=True, if_exists_action='append')
        return points_df.bounds

    def calculate_geolist_update_database(self, df, geo_list, calculate=False):
        depths = None
        self.post_points(df.crs, geo_list, depths)
        # df["zoom_level"] = df["zoom_level_1"]
        # df.drop(['zoom_level_1', 'zoom_level_2'], axis=1, inplace=True)
        # df.reset_index(drop=True, inplace=True)
        self.PostGisConnection.put_into_table(df, "Polygon", self.PostGisConnection.polygon_table, create_table=True,
                                              if_exists_action='append')

    def get_distance_between_points(self, bounds):
        return bounds['ne']. \
                   reduceDecimals(). \
                   calculate_distance_to_point(bounds['nw'].reduceDecimals()) / 50

    def check_points(self, df):
        bounds = self.create_points_dict()
        origin_point = bounds['nw'].reduceDecimals()
        distance_between_points_km = self.get_distance_between_points(bounds)
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
        return geo_list

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
