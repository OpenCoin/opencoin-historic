# Copyright (c) 2006 Jurgen Scheible
# This script creates tabs that let you switch between different applications


import appuifw,e32,socket,httplib, urllib
from graphics import *
from key_codes import EKeyLeftArrow, EKeyRightArrow

import oc2

def callback():
    print 'foo callback'

def exit_key_handler():
    app_lock.signal()





    

def sum(seq, start=0):
        s = 0
        for i in seq:
            s = s + i
        return s

class Wallet:

   
    

    def __init__(self):
        self.content = [{'name':u'opencents','description':u'opencents.org','coins':[1,7,3,4,7,2,3]},
                        {'name':u'hubtokens','description':u'the-hub.net','coins': [11,13,4,11,22]},]


        
        self.wallet_list = []
        for cur in self.content:
            self.wallet_list.append((u'%s %s' % (sum(cur['coins']),cur['name']),unicode(cur['description'])))
        self.wallet_menu = appuifw.Listbox(self.wallet_list,self.displayActions)
        self.wallet_menu.bind(EKeyRightArrow,self.displayActions)

        
        appuifw.query(u'Wallet Password',u'code')
        self.displayWallet()


    def createOptionMenu(self):
        appuifw.app.menu=[(u'Send coins',((u'via Internet',w.sendCoins),
                          (u'via Bluetooth',w.sendCoinsBT))),
                  (u'Receive coins',((u'via Internet',w.receiveCoins),
                                     (u'via Bluetooth',w.receiveCoinsBT))),
                  (u'Buy coins',w.buyCoins),
                  (u'Redeem coins',w.redeemCoins)]
    
    
    def getActiveCurrency(self):
        return self.content[self.wallet_menu.current()]
    
    def displayWallet(self):
        appuifw.app.body =  self.wallet_menu
        appuifw.app.title = u'Opencoin Wallet'

    def displayDetails(self):
    
        cur = self.getActiveCurrency()
        l = [(u'%s %s:' % (sum(cur['coins']),cur['name'])),]

        for coin in cur['coins']:
            l.append(u"a '%s' coin" % coin)
    
        cl = appuifw.Listbox(l,callback)
        cl.bind(EKeyLeftArrow,self.displayActions)                  
        appuifw.app.body = cl
        appuifw.app.title = u'Opencoin \n%s - details' % cur['name']

    def displayActions(self):
        name = self.getActiveCurrency()['name']
        action_list = [u'Show details' ,
                       u'Send %s' % name,
                       u'Receive %s' % name,
                       u'Buy %s' % name,
                       u'Redeem %s' % name]

        self.action_menu = appuifw.Listbox(action_list,self.selectAction)
        self.action_menu.bind(EKeyRightArrow,self.selectAction)
        self.action_menu.bind(EKeyLeftArrow,self.displayWallet)

        appuifw.app.body = self.action_menu
        appuifw.app.title = u'Opencoin \n%s - actions' % name

    def selectAction(self):
        current = self.action_menu.current()

        actions = [self.displayDetails,self.sendCoins,self.receiveCoins,self.buyCoins,self.redeemCoins]
        actions[current]()


    def sendCoins(self):
        name = self.getActiveCurrency()['name']
        number = appuifw.query(u'number of %s' % name,u'number')
        selection = appuifw.popup_menu([u'internet',u'bluetooth'],u'Send %s %s via' % (number,name))
        if selection == 1:
            self.sendCoinsBT()
        elif selection == 0:
            address = appuifw.query(u'Recipients address',u'text')
            conn = httplib.HTTPConnection(address)
            appuifw.note(u'Making connection. May take a while...')
            conn.request('POST','/wallet')


    def receiveCoins(self):
        name = self.getActiveCurrency()['name']
        selection = appuifw.popup_menu([u'internet',u'bluetooth'],u'Receive %s via' % name)
        if selection == 0:
            w = oc2.Wallet()
            sst = oc2.SocketServerTransport('0.0.0.0',12008)
            r = urllib.urlopen('https://opencoin.org/myownip')
            appuifw.note(u'send the coins now')
            w.receiveMoney(sst)
            appuifw.note(u'got coins: %s' % repr(w.coins))


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





# create an Active Object
app_lock = e32.Ao_lock()

# set the title of the script
w = Wallet()

# set app.body to app1 (for start of script)

appuifw.app.exit_key_handler = exit_key_handler
app_lock.wait()
