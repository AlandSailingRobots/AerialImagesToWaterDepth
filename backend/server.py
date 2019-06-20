import json
from http.server import BaseHTTPRequestHandler, HTTPServer

import time

from backend.GeoJsonHandler import GeoJsonHandler

hostName = ""
hostPort = 80


class MyServer(BaseHTTPRequestHandler):
    geoJsonHandler = GeoJsonHandler()

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
        print("post", "incoming http: ", self.path)
        returned_json = self.geoJsonHandler.doAction(self.path, self.getJsonData())
        self.wfile.write(returned_json.encode())


myServer = HTTPServer((hostName, hostPort), MyServer)
print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
