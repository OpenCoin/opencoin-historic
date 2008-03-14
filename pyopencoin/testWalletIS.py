from oc import entities,transports 
import sys

if len(sys.argv) > 1:
    addr = sys.argv[1]
else:
    addr = '0.0.0.0'

w = entities.Wallet()
sst = transports.SocketClientTransport(addr, 12008)
sst.debug = 1

w.fetchMintKey(sst, denominations=['1'])
w.fetchMintKey(sst, denominations=['4'])

