import oc2
w = oc2.Wallet()
sst = oc2.SocketClientTransport('0.0.0.0',12008)
sst.debug = 1
w.sendMoney(sst)
