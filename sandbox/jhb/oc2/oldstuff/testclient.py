import BaseHTTPServer, threading
import protocols, transports, urllib

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_POST(self):
        
        wallet = self.server.wallet
        client = self.server.walletclient
        
        if self.path == '/stop':
            raise 'foobar'
        length = self.headers.get('Content-Length')
        data = self.rfile.read(int(length))
        data = urllib.unquote(data)
        message = transports.createMessage(data)
        
        if message.header == 'SpendRequest':
            protocol = protocols.SpendListen(wallet,client)
 
        answer = protocol.run(message)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.wfile.write('\r\n')
        self.wfile.write(answer.toString(True))


class Client(object):

    def __init__(self,port,wallet=None):
        self.wallet = wallet
        self.port = port

    def http_run_once(self):
        import time
        time.sleep(0.001)
        httpd = BaseHTTPServer.HTTPServer(("", self.port), Handler)
        httpd.wallet = self.wallet
        httpd.walletclient = self
        import threading
        t = threading.Thread(target=httpd.handle_request)     
        t.start()

