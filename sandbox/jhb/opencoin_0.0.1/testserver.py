# (c) 2007 Nils Toedtmann, Joerg Baach, License GPL
from SimpleXMLRPCServer import SimpleXMLRPCServer
import os, pickle

server = SimpleXMLRPCServer(("0.0.0.0", 8000))
filename = 'testserver.dat'

#Get an Issuer
if os.path.exists(filename):
    print 'reading issuer'
    f = file(filename,'r')
    i = pickle.loads(f.read())
    f.close()
else:
    print 'new Issuer'
    import Issuer
    i = Issuer.Issuer('http://opencoin.net/cur1',[1,2])

#Register Issuer
server.register_function(i.getSignedBlind)
server.register_function(i.getPubKeys_encoded)
server.register_function(i.getUrl)
server.register_function(i.checkDoubleSpending)
server.register_function(i.receiveCoins)


try:
    while True:
        server.handle_request()
except KeyboardInterrupt:
    server.server_close()
    print 'writing issuer'
    f = file(filename,'w')
    f.write(pickle.dumps(i))
    f.close()
    print 'theend'



