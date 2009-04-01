import BaseHTTPServer, threading
import protocols, issuer, mint, transports, urllib


class Handler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_POST(self):
        #print self.server
        if self.path == '/stop':
            raise 'foobar'
        length = self.headers.get('Content-Length')
        data = self.rfile.read(int(length))
        data = urllib.unquote(data)
        message = transports.createMessage(data)
        if message.header == 'AskLatestCDD':
            protocol = protocols.GiveLatestCDD(self.issuer)
        answer = protocol.run(message)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.wfile.write('\r\n')
        self.wfile.write(answer.toString(True))


def run_once(port,issuer=None):
    Handler.issuer = issuer
    httpd = BaseHTTPServer.HTTPServer(("", port), Handler)
    import threading
    t = threading.Thread(target=httpd.handle_request)     
    t.start()

