# Copyright (c) 2006 Jurgen Scheible
# This script creates tabs that let you switch between different applications


import appuifw,e32,socket
from graphics import *
from key_codes import EKeyLeftArrow, EKeyRightArrow

def callback():
    print 'foo callback'

def exit_key_handler():
    app_lock.signal()

def setCurrency():
    
    cur = content[wallet.current()]
    l = [(u'%s %s:' % (sum(cur['coins']),cur['name'])),]

    for coin in cur['coins']:
        l.append(u"a '%s' coin" % coin)
    
    cl = appuifw.Listbox(l,callback)
    cl.bind(EKeyLeftArrow,setWallet)                  
    appuifw.app.body = cl

    
def setWallet():
    appuifw.app.body =  wallet

def sum(seq, start=0):
        s = 0
        for i in seq:
            s = s + i
        return s

class Wallet:



    def sendCoins(self):
        appuifw.query(u'Enter Recepients Address',u'text')

    def receiveCoins(self):
        pass

    def sendCoinsBT(self):
        self.sock=socket.socket(socket.AF_BT,socket.SOCK_STREAM)
        try:
            addr,services=socket.bt_discover()
        except Exception:
            appuifw.note(u'Bluetooth failed')
            return
            
        if len(services)>0:
            choices=services.keys()
            choices.sort()
            choice=appuifw.popup_menu([unicode(services[x])+": "+x
                                       for x in choices],u'Choose port:')
            port=services[choices[choice]]
        else:
            port=services[services.keys()[0]]
        address=(addr,port)
        self.sock.connect(address)
        appuifw.note(u'Bluetooth connected')
        self.sock.send('A coin \n')
        appuifw.note(u'Coin sent')

                    
    def receiveCoinsBT(self):
        pass

    def buyCoins(self):
        pass

    def redeemCoins(self):
        pass

w = Wallet()

content = [{'name':'opencents','description':'opencents.org','coins':[1,7,3,4,7,2,3]},
           {'name':'hubtokens','description':'the-hub.net','coins': [11,13,4,11,22]},]

wl = []
for cur in content:
    wl.append((u'%s %s' % (sum(cur['coins']),cur['name']),unicode(cur['description'])))
wallet = appuifw.Listbox(wl,setCurrency)
wallet.bind(EKeyRightArrow,setCurrency)

# create an Active Object
app_lock = e32.Ao_lock()

# set the title of the script
appuifw.app.title = u'Opencoin Wallet'
appuifw.app.menu=[(u'Send coins',((u'via Internet',w.sendCoins),
                                  (u'via Bluetooth',w.sendCoinsBT))),
                  (u'Receive coins',((u'via Internet',w.receiveCoins),
                                     (u'via Bluetooth',w.receiveCoinsBT))),
                  (u'Buy coins',w.buyCoins),
                  (u'Redeem coins',w.redeemCoins)]

appuifw.query(u'Wallet Password',u'code')

# set app.body to app1 (for start of script)
setWallet()

appuifw.app.exit_key_handler = exit_key_handler
app_lock.wait()
