from http.server import BaseHTTPRequestHandler, HTTPServer
from map_based_resources import point
import time
import json

hostName = ""
hostPort = 80


class MyServer(BaseHTTPRequestHandler):
    def make_point_from_json(self, data, item):
        point_ = point.DataPoint(latitude=data['box'][item]['lat'], longitude=data['box'][item]['lng'],
                                 coordinate_type=data['crs'].lower(), level=data['zoom'])
        converted = point_.convert_coordinate_systems(save_in_point=True)
        return point_

    def do_GET(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        # self.wfile.write("<html><body>Hello world!</body></html>")
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
        # self.send_header('Content-type', 'text/html')
        self.end_headers()
        print('post')
        print("incoming http: ", self.path)
        content_length = int(self.headers.get('Content-Length'))  # <--- Gets the size of data
        post_data = (self.rfile.read(content_length)).decode('utf8')  # <--- Gets the data itself

        json_data = json.loads(post_data)
        points_dict = dict()
        for item in json_data['box']:
            points_dict[item] = self.make_point_from_json(json_data, item)
        print(points_dict['nw'].calculate_distance_to_point(points_dict['ne'])/2)


myServer = HTTPServer((hostName, hostPort), MyServer)
print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
