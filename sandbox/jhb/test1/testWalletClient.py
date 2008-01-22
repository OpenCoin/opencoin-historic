import oc import oc2, 
import sys

if len(sys.argv) > 1:
    addr = sys.argv[1]
else:
    addr = '0.0.0.0'
w = oc2.Wallet()
sst = oc2.SocketClientTransport(addr,12008)
sst.debug = 1
w.sendMoney(sst)
