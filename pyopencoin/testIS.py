from oc import entities, transports, tests
IS = entities.Issuer()
IS.cdd = tests.CDD
IS.masterKey = tests.CDD_private
ssh = transports.SocketServerHandler('0.0.0.0', 12008, IS.listen)
ssh.debug = 1
print 'starting'
ssh.start()
print 'fini'
