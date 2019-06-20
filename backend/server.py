import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from backend.GeoJsonHandler import GeoJsonHandler

hostName = ""
hostPort = 80


class MyServer(BaseHTTPRequestHandler):
    geoJsonHandler = GeoJsonHandler()

    def getJsonData(self):
        content_length = int(self.headers.get('Content-Length'))  # <--- Gets the size of data
        post_data = (self.rfile.read(content_length)).decode('utf8')  # <--- Gets the data itself
        return json.loads(post_data)

    def sendSuccesfullJson(self, json):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.encode())

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
        print("post", "incoming http: ", self.path)
        try:
            returned_json = self.geoJsonHandler.doAction(self.path, self.getJsonData())
            self.sendSuccesfullJson(returned_json)
        except Exception as e:
            self.send_error(501, repr(e))


myServer = HTTPServer((hostName, hostPort), MyServer)
print(time.asctime(), "Server Starts - %s:%s" % (hostName, hostPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (hostName, hostPort))
