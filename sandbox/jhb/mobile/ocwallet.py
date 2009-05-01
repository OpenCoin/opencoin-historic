import appuifw,e32,socket,httplib, urllib
from graphics import *
from key_codes import EKeyLeftArrow, EKeyRightArrow
import encodings
from oc2 import storage,wallet, transports

class WalletClient:

    def __init__(self,storage):
        self.storage = storage
        self.wallet = wallet.Wallet(storage)
        self.makeWalletMenu()
        self.displayWalletMenu()        
        self.actions=[(u'Send',u'Send coins to someone',self.getDetails),
                      (u'Receive',u'Receive coins',self.getReceiveDetails),
                      (u'Freshen up',u'Freshen up the coins',self.freshenUp),
                      (u'Buy',u'Buy new coins',self.mintCoins),
                      (u'Sell',u'Sell coins',self.redeemCoins),
                      (u'Details',u'See what coins you hold',self.inspectCurrency),]

        self.methods=[(u'Internet',u'Use the internet'),
                      (u'Bluetooth',u'Mobile to mobile')]
        
        self.todo = {}
        self.apo = None

    def makeWalletMenu(self):
        self.wallet_list = []
        tmp = [(cdd.currencyId,cdd,amount) for cdd,amount in self.wallet.listCurrencies()]
        tmp.sort()
        self.currencies = [(t[1],t[2]) for t in tmp]

        for cdd,amount in self.currencies:
            title = u'%s %ss' % (amount,cdd.currencyId)
            description = unicode(cdd.issuerServiceLocation)
            self.wallet_list.append((title,description))
        if not self.wallet_list:
            self.wallet_list.append(u'no currencies yet')
            self.wallet_menu =  appuifw.Listbox(self.wallet_list,self.displayActionMenu)
        else:
            self.wallet_menu =  appuifw.Listbox(self.wallet_list,self.displayActionMenu)
            self.wallet_menu.bind(EKeyRightArrow,self.displayActionMenu)

    def displayWalletMenu(self):
        appuifw.app.body =  self.wallet_menu
        appuifw.app.title = u'opencoin - main\nchoose your currency'
        appuifw.app.menu = [(u'add Currency',self.addCurrency),
                            (u'delete Currency',self.delCurrency)]

    def displayActionMenu(self):

        action_list = [(action[0],action[1]) for action in self.actions]
        self.action_menu = appuifw.Listbox(action_list,self.selectAction)
        self.action_menu.bind(EKeyRightArrow,self.selectAction)
        self.action_menu.bind(EKeyLeftArrow,self.displayWalletMenu)
        appuifw.app.body = self.action_menu
        appuifw.app.title = u'opencoin - currency\nSelect the action'
        #print 'displayActionMenu'

    def selectAction(self):
        current = self.action_menu.current()
        self.todo['action'] = self.actions[current][0]
        self.actions[current][2]()


    def getAmount(self):
        amount = appuifw.query(u'Amount','number')
        amount = int(amount)
        self.todo['amount'] = amount
        return amount

    def getTarget(self):
        target = ''
        while target == '':
            target = appuifw.query(u'Reference','text')
        self.todo['target'] = target
        return target            

    def getDetails(self):
        
        amount = self.getAmount()
        if not amount:
            return

        target = self.getTarget()
        if not target:
            return

        method = self.getMethod()
        if method ==1:
            url = appuifw.query(u'url','text',u'http://')
            self.todo['url'] = url

        self.execute()

    def getReceiveDetails(self):
        method = self.getMethod()
        if method ==1:
            appuifw.note(u'we are reachable at:','conf')
        self.execute()



    def getMethod(self):
        methodlist = [u'mobile to mobile',u'internet']
        method = appuifw.popup_menu(methodlist)
        self.todo['method'] = method
        return method
                              
    def inspectCurrency(self):
        #print 'inspect'
        cdd,amount = self.getCurrentCurrency()
        id = cdd.currencyId
        coins = self.wallet.getAllCoins(id)
        coinlist = []
        for coin in coins:
            coinlist.append(u'coin: %s' % coin.denomination)
        self.currency_menu = appuifw.Listbox(coinlist,self.inspectCoin)
        self.currency_menu.bind(EKeyRightArrow,self.inspectCoin)
        self.currency_menu.bind(EKeyLeftArrow,self.displayActionMenu)
        appuifw.app.body = self.currency_menu
        appuifw.app.title = u'opencoin - currency\nCoins in wallet'
 
    def inspectCoin(self):
        cdd,amount = self.getCurrentCurrency()
        id = cdd.currencyId
        coins = self.wallet.getAllCoins(id)
        coin = coins[self.currency_menu.current()]
        details = []
        details.append((unicode(coin.standardId),u'Standard Id'))
        details.append((unicode(coin.currencyId),u'Currency Id'))
        details.append((unicode(coin.denomination),u'Denomination'))
        self.coin_menu = appuifw.Listbox(details,self.inspectCurrency)
        self.coin_menu.bind(EKeyLeftArrow,self.inspectCurrency)
        appuifw.app.body = self.coin_menu
        appuifw.app.title = u'opencoin - coin\nDetails of coin'
 
    def addCurrency(self):
        url = appuifw.query(u'url','text',u'http://192.168.2.101:9090')
        self.todo['url'] = url
        transport = self.getHTTPTransport(url) 
        self.wallet.addCurrency(transport)
        self.makeWalletMenu()
        self.displayWalletMenu()


    def getCurrentCurrency(self):
        return self.currencies[self.wallet_menu.current()]

    def delCurrency(self):
        cdd,amount = self.getCurrentCurrency()
        id = cdd.currencyId
        result = appuifw.query(u'Delete %s %ss?' % (amount,id),'query')
        if result:
            self.wallet.deleteCurrency(id)
        self.makeWalletMenu()
        self.displayWalletMenu()

    def mintCoins(self):
        amount = self.getAmount()
        if not amount:
            return
        
        target = self.getTarget()
        if not target:
            return

        cdd,alreadythere = self.getCurrentCurrency()
        url = cdd.issuerServiceLocation

        transport = transports.HTTPTransport(url)
        self.wallet.mintCoins(transport,amount,target)
        self.makeWalletMenu()
        self.displayWalletMenu()


    def redeemCoins(self):
        amount = self.getAmount()
        if not amount:
            return
        
        target = self.getTarget()
        if not target:
            return

        cdd,alreadythere = self.getCurrentCurrency()
        url = cdd.issuerServiceLocation

        transport = transports.HTTPTransport(url)
        self.wallet.redeemCoins(transport,amount,target)
        self.makeWalletMenu()
        self.displayWalletMenu()


    def freshenUp(self):
        cdd,alreadythere = self.getCurrentCurrency()
        transport = transports.HTTPTransport(cdd.issuerServiceLocation)
        self.wallet.freshenUp(transport,cdd)
        self.makeWalletMenu()
        self.displayWalletMenu()


    def execute(self):
        #print 'execute'
        print self.todo


    def getHTTPTransport(self,url):
        self.startInternet()
        transport = transports.HTTPTransport(url)
        return transport

    def startInternet(self):
        if not self.apo:
            import sys
            try:
                #sys.modules['socket'] = __import__('btsocket')
                import btsocket as socket
                #apid = socket.select_access_point()
                #apo = socket.access_point(apid)
                #socket.set_default_access_point(apo)
                #apo.start()
                #self.apo = apo
                #self.ip = apo.ip()

            except ImportError:
                import socket
            

    def stopInternet(self):
        if self.apo:
            self.apo.stop()
            self.apo = None



    

#appuifw.app.screen='full'
app_lock = e32.Ao_lock()
storage = storage.Storage()
storage.setFilename('wallet.bin')
storage.restore()

w = WalletClient(storage)
appuifw.app.screen='normal'
appuifw.app.exit_key_handler = app_lock.signal
import time
app_lock.wait()
storage.save()
print 'fini'
