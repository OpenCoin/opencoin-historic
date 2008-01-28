from oc import entities,transports
w = entities.Wallet()
sst = transports.SocketServerTransport('0.0.0.0',12008)
sst.debug = 1
print 'starting'
w.receiveMoney(sst)
print 'fini'
