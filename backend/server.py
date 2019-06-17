from http.server import BaseHTTPRequestHandler, HTTPServer
from map_based_resources import point
import geopandas as gpd
import time
import json

hostName = ""
hostPort = 80


class MyServer(BaseHTTPRequestHandler):
    def make_point_from_json(self, data, item):
        point_ = point.DataPoint(latitude=data['box'][item]['lat'], longitude=data['box'][item]['lng'],
                                 coordinate_type=data['crs'].lower(), level=data['zoom'])
        point_.convert_coordinate_systems(save_in_point=True)
        return point_

    def readGeoJson(self):
        box = self.getJsonData()
        sw = self.make_point_from_json(box, 'sw')
        ne = self.make_point_from_json(box, 'ne')
        url = "http://avaa.tdata.fi/geoserver/osm_finland/ows?service=WFS&version=1.3.0&request=GetFeature&typeName" \
              "=osm_finland:sea_detailed&maxFeatures=10&srsName=EPSG:4326&bbox={0},{1}," \
              "{2},{3}&outputFormat=application%2Fjson".format(sw.longitude, sw.latitude, ne.longitude, ne.latitude, )
        return gpd.read_file(url).to_json()

    def createPoint(self, item):
        return (float(item['lat']), float(item['lng']))

    def getPoints(self):
        points_dict = dict()
        json_data = self.getJsonData()
        for item in json_data['box']:
            points_dict[item] = self.make_point_from_json(json_data, item)
        print(points_dict['nw'].calculate_distance_to_point(points_dict['ne']) / 2)
        listed_points = []
        for key in points_dict.keys():
            point = points_dict[key].convert_coordinate_systems(destination='EPSG:4326', return_point=True)
            listed_points.append({"key": key, "point": point.__dict__})
        return listed_points

    def getJsonData(self):
        content_length = int(self.headers.get('Content-Length'))  # <--- Gets the size of data
        post_data = (self.rfile.read(content_length)).decode('utf8')  # <--- Gets the data itself
        return json.loads(post_data)

    def do_GET(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        print(self.headers)
        self.connection.shutdown(1)

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        print('post')
        print("incoming http: ", self.path)

        splitted_path = self.path.strip().split('/')
        print(splitted_path)
        json_return = None
        if splitted_path[1] == "getGeoJson":
            json_return = self.readGeoJson()
        else:
            json_return = json.dumps(self.getPoints())
        self.wfile.write(json_return.encode())


myServer = HTTPServer((hostName, hostPort), MyServer)
print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
