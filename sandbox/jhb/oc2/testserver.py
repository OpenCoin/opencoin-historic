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
        elif message.header == 'FetchMintKeys':
            protocol = protocols.GiveMintKeys(self.issuer)
        elif message.header == 'TransferRequest':
            protocol = protocols.TransferHandling(self.mint,self.authorizer)
        answer = protocol.run(message)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.wfile.write('\r\n')
        self.wfile.write(answer.toString(True))


def run_once(port,issuer=None,mint=None,authorizer=None):
    Handler.issuer = issuer
    Handler.mint = mint
    Handler.authorizer = authorizer
    httpd = BaseHTTPServer.HTTPServer(("", port), Handler)
    import threading
    t = threading.Thread(target=httpd.handle_request)     
    t.start()

