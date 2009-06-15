# File: cgihttpserver-example-1.py

import CGIHTTPServer
import BaseHTTPServer

class Handler(CGIHTTPServer.CGIHTTPRequestHandler):
    cgi_directories = [""]


def address_string(self):
    host, port = self.client_address[:2]
    return host

Handler.address_string = address_string

PORT = 9091


httpd = BaseHTTPServer.HTTPServer(("", PORT), Handler)
httpd.address_string = address_string
print "serving at port", PORT
httpd.serve_forever()
