from oc import entities, transports, tests
IS = entities.Issuer()
IS.cdd = tests.CDD
IS.masterKey = tests.CDD_private
sst = transports.SocketServerTransport('0.0.0.0',12008)
sst.debug = 1
print 'starting'
IS.listen(sst)
print 'fini'
