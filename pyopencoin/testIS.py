from oc import entities, transports, tests
ie = entities.IssuerEntity()
IS = ie.issuer
IS.addCDD(tests.CDD)
IS.setCurrentCDDVersion('1')
ssh = transports.SocketServerHandler('0.0.0.0', 12008, IS.listen)
ssh.debug = 1
print 'starting'
ssh.start()
print 'fini'
