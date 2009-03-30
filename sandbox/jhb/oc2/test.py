import BaseHTTPServer, threading

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        if self.path == '/stop':
            raise 'foobar'
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write('foo')
        
PORT = 8000

httpd = BaseHTTPServer.HTTPServer(("", PORT), Handler)
print "serving at port", PORT
t = threading.Thread(target=httpd.handle_request)
t.start()
#import time
#for i in range(10):
#    time.sleep(3)
print 'foobar'

#httpd.serve_forever()

