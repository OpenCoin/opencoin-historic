import appuifw,e32,httplib, urllib
from graphics import *
from key_codes import EKeyLeftArrow, EKeyRightArrow
import encodings
from oc2 import storage,wallet, transports
import sys

class WalletClient:

    def __init__(self,storage):
        self.storage = storage
        self.wallet = wallet.Wallet(storage)
        self.makeWalletMenu()
        self.displayWalletMenu()        
        self.actions=[(u'Send',u'Send coins to someone',self.spendCoins),
                      (u'Receive',u'Receive coins',self.receiveCoins),
                      (u'Freshen up',u'Freshen up the coins',self.freshenUp),
                      (u'Mint',u'new coins from issuer',self.mintCoins),
                      (u'Redeem',u'redeem from issuer',self.redeemCoins),
                      (u'Details',u'See what coins you hold',self.inspectCurrency),]

        
        self.todo = {}
        self.ip = None

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


    def inspectCurrency(self):
        #print 'inspect'
        cdd,amount = self.getCurrentCurrency()
        id = cdd.currencyId
        coins = self.wallet.getAllCoins(id)
        coinlist = []
        for coin in coins:
            coinlist.append(u'%s %s' % (coin.denomination,cdd.currencyId))
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
        details.append((u'Standard Id',unicode(coin.standardId)))
        details.append((u'Currency Id',unicode(coin.currencyId)))
        details.append((u'Denomination',unicode(coin.denomination)))
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

        transport = self.getHTTPTransport(url)
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

        transport = self.getHTTPTransport(url)
        self.wallet.redeemCoins(transport,amount,target)
        self.makeWalletMenu()
        self.displayWalletMenu()


    def freshenUp(self):
        cdd,alreadythere = self.getCurrentCurrency()
        transport = self.getHTTPTransport(cdd.issuerServiceLocation)
        self.wallet.freshenUp(transport,cdd)
        self.makeWalletMenu()
        self.displayWalletMenu()


    def execute(self):
        #print 'execute'
        print self.todo

    def receiveCoins(self):
        methodlist = [u'internet',u'bluetooth']
        method = appuifw.popup_menu(methodlist)

        cdd,alreadythere = self.getCurrentCurrency()
        transport = self.getHTTPTransport(cdd.issuerServiceLocation)

        if method ==1:
            self.receiveCoinsBT(transport)
        else:
            self.receiveCoinsHTTP(transport)
        
        self.makeWalletMenu()
        self.displayWalletMenu()
    


    def getHTTPTransport(self,url):
        self.startInternet()
        transport = transports.HTTPTransport(url)
        return transport
    
    def receiveCoinsHTTP(self,transport):
        import BaseHTTPServer, urllib
        
        class OCHandler(BaseHTTPServer.BaseHTTPRequestHandler):

            def do_POST(self):
                #print self.server
                if self.path == '/stop':
                    raise 'foobar'
                length = self.headers.get('Content-Length')
                data = self.rfile.read(int(length))
                data = urllib.unquote(data)
                message = transports.createMessage(data)
                if message.header == 'SumAnnounce':
                    answer = self.wallet.listenSum(message)
                if message.header == 'SpendRequest':
                    answer = self.wallet.listenSpend(message,transport)
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.wfile.write('\r\n')
                self.wfile.write(answer.toString(True))
                
        port = int(appuifw.query(u'port','number','9091'))
        OCHandler.wallet = self.wallet
        OCHandler.wallet.getApproval = self.getApproval
        self.startInternet()
        
        #hack to open internet
        #r = urllib.urlopen('http://google.com')
        
        httpd = BaseHTTPServer.HTTPServer(("",port),OCHandler)
        appuifw.note(u'waiting at %s:%s' % ('localhost',port),'conf')
        httpd.handle_request()
        httpd.handle_request()
        self.stopInternet()

    def getBTTransport(self):
        
        import btsocket
        sock=btsocket.socket(btsocket.AF_BT,btsocket.SOCK_STREAM)
        addr,services=btsocket.bt_discover()
        if len(services)>0:
            choices=services.keys()
            choices.sort()
            choice=appuifw.popup_menu([unicode(services[x])+": "+x for x in choices],u'Choose port:')
            port=services[choices[choice]]
        else:
            port=services[services.keys()[0]]
        address=(addr,port)
        sock.connect(address)
        return transports.BTTransport(sock)

  
    
    def receiveCoinsBT(self,transport):
        if sys.platform == 'symbian_s60':
            import btsocket
            server_socket = btsocket.socket(btsocket.AF_BT, btsocket.SOCK_STREAM)
            port = btsocket.bt_rfcomm_get_available_server_channel(server_socket)
            server_socket.bind(("", port))
            server_socket.listen(1)
            btsocket.bt_advertise_service( u"opencoin", server_socket, True, btsocket.RFCOMM)
            btsocket.set_security(server_socket, btsocket.AUTH)
            appuifw.note(u'waiting for bt connection')
            (sock,peer_addr) = server_socket.accept()

        else:
            import bluetooth as bt
            server_sock=bt.BluetoothSocket(bt.RFCOMM)
            server_sock.bind(("",bt.PORT_ANY))
            server_sock.listen(1)
            port = server_sock.getsockname()[1]

            uuid = "9e72d9d8-e06d-41cb-bbd4-89cd052cccb8"
            
            bt.advertise_service( server_sock, u"opencoin",)
                               
            sock, client_info = server_sock.accept()

        
        bt = transports.BTTransport(sock)
        self.wallet.getApproval = self.getApproval 
        bt.send(self.wallet.listenSum(bt.receive()))
        bt.send(self.wallet.listenSpend(bt.receive(),transport))
        import e32
        e32.ao_sleep(1)    


    def spendCoins(self):

        amount = self.getAmount()
        if not amount:
            return
        
        target = self.getTarget()
        if not target:
            return
            
        methodlist = [u'internet',u'bluetooth']
        method = appuifw.popup_menu(methodlist)


        cdd,alreadythere = self.getCurrentCurrency()
        if method == 0:
            url = appuifw.query(u'url','text',u'http://192.168.2.105:9091')
            transport = self.getHTTPTransport(url)
        else:
            transport = self.getBTTransport() 

        self.wallet.spendCoins(transport,cdd.currencyId,amount,target)
        self.makeWalletMenu()
        self.displayWalletMenu()




    def getApproval(self,message):
        amount = message.amount
        target = message.target
        return appuifw.query(u'Accept %s (ref "%s")?' % (amount,target),'query') 


    




    def startInternet(self):
        if not self.ip:
            import sys
            if sys.platform == 'symbian_s60':
                import socket
                appuifw.note(u'Preparing access points')
                aps = [ap['name'] for ap in socket.access_points()]
                aps.sort()
                apid = appuifw.popup_menu(aps,u'select access point')
                socket.set_default_access_point(aps[apid])
                self.ip = 'some ip, s60'

            else:
                import socket
                self.ip = 'some ip'
            

    def stopInternet(self):
        pass


    

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
