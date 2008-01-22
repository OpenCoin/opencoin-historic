from oc import oc2
w = oc2.Wallet()
sst = oc2.SocketServerTransport('0.0.0.0',12008)
sst.debug = 1
print 'starting'
w.receiveMoney(sst)
print 'fini'
