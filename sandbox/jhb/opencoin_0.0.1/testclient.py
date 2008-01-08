# (c) 2007 Nils Toedtmann, Joerg Baach, License GPL
import xmlrpclib
from Wallet import Wallet

url = 'http://opencoin.net/cur1'
server = 'http://localhost:8000'

i =  xmlrpclib.ServerProxy(server)
w = Wallet({url:i})

w.createCoins([1,1,2],url)
print w.getBalance()
w.fetchSignedBlinds()
print w.getBalance()
w.fetchSignedBlinds()
print w.getBalance()

coin = w.valid.values()[0]

w.sendCoins(i,[coin],'foobar')
w.sendCoins(i,[coin],'foobar')
#w2 = xmlrpclib.ServerProxy('http://localhost:8001')
#coin = w.valid.values()[0]
#print `coin`
#w.sendCoins(w2,[coin],'foobar')



