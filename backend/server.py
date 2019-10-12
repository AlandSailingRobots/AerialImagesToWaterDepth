import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from backend.Handlers import GeoJsonHandler
from data_resources import fileToObjects

# Source: https://automating-gis-processes.github.io/CSC/notebooks/L2/data_io.html


server_settings = fileToObjects.open_json_file('server_settings.json')["Host"]


class MyServer(BaseHTTPRequestHandler):
    geoJsonHandler = GeoJsonHandler.GeoJsonHandler()

    def dissect_path(self):
        return self.path.strip().split('/')

    def getJsonData(self):
        content_length = int(self.headers.get('Content-Length'))  # <--- Gets the size of data
        post_data = (self.rfile.read(content_length)).decode('utf8')  # <--- Gets the data itself
        return json.loads(post_data)

    def sendSuccesfullJson(self, json_):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json_.encode())

    def do_GET(self):
        if self.dissect_path()[1] == "MapSettings":
            map_settings = json.dumps(json.loads(open(fileToObjects.check_path("map_settings.json")).read()))
            self.sendSuccesfullJson(map_settings)

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        print("post", "incoming http: ", self.path)
        try:
            returned_json = self.geoJsonHandler.doAction(self.dissect_path(), self.getJsonData())
            self.sendSuccesfullJson(returned_json)
        except Exception as e:
            self.send_error(501, repr(e))


hostName, hostPort = server_settings['name'], server_settings['port']
myServer = HTTPServer((hostName, hostPort), MyServer)
print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()

print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
