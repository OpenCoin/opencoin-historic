import appuifw,e32

class WalletClient:

    def __init__(self,storage):
        self.storage = storage
        self.wallet = wallet.Wallet(storage)
        self.wallet.getApproval = self.getApproval
        self.wallet.feedback = self.feedback
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
            self.wallet_list.append((title,description,icon))
        if not self.wallet_list:
            self.wallet_list.append(u'no currencies yet')
            self.wallet_menu =  appuifw.Listbox(self.wallet_list,self.displayActionMenu)
        else:
            self.wallet_menu =  appuifw.Listbox(self.wallet_list,self.displayActionMenu)
            self.wallet_menu.bind(EKeyRightArrow,self.displayActionMenu)

    def feedback(self,text):
        #appuifw.note(unicode(message))
        status(unicode(text))
        #i = i=appuifw.InfoPopup()
        #i.show(unicode(message), (0, 0), timeout*1000, 0, appuifw.EHCenterVCenter)
        
     

    def displayWalletMenu(self):
        self.makeWalletMenu()
        appuifw.app.body =  self.wallet_menu
        appuifw.app.title = u'opencoin wallet\nall currencies'
        appuifw.app.menu = [(u'add Currency',self.addCurrency),
                            (u'delete Currency',self.delCurrency)]

    def displayActionMenu(self):

        action_list = [(action[0],action[1]) for action in self.actions]
        self.action_menu = appuifw.Listbox(action_list,self.selectAction)
        self.action_menu.bind(EKeyRightArrow,self.selectAction)
        self.action_menu.bind(EKeyLeftArrow,self.displayWalletMenu)
        appuifw.app.body = self.action_menu
        cdd,amount = self.getCurrentCurrency()
        appuifw.app.title = u'%ss\nactions' % cdd.currencyId
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
        appuifw.app.title = u'%ss\ncoin list' % id
 
    def inspectCoin(self):
        cdd,amount = self.getCurrentCurrency()
        id = cdd.currencyId
        coins = self.wallet.getAllCoins(id)
        coin = coins[self.currency_menu.current()]
        details = []
        details.append((u'Standard Id',unicode(coin.standardId)))
        details.append((u'Currency Id',unicode(coin.currencyId)))
        details.append((u'Denomination',unicode(coin.denomination)))
        details.append((u'Serial',unicode(coin.serial)))
        details.append((u'Signature',unicode(coin.signature)))
        self.coin_menu = appuifw.Listbox(details,self.inspectCurrency)
        self.coin_menu.bind(EKeyLeftArrow,self.inspectCurrency)
        appuifw.app.body = self.coin_menu
        appuifw.app.title = u'%ss\ncoin details' % id
 
    def addCurrency(self):
        url = appuifw.query(u'url','text',u'http://baach.de:9090')
        self.todo['url'] = url
        transport = self.getHTTPTransport(url) 
        self.wallet.addCurrency(transport)
        self.displayWalletMenu()


    def getCurrentCurrency(self):
        return self.currencies[self.wallet_menu.current()]

    def delCurrency(self):
        cdd,amount = self.getCurrentCurrency()
        id = cdd.currencyId
        result = appuifw.query(u'Delete %s %ss?' % (amount,id),'query')
        if result:
            self.wallet.deleteCurrency(id)
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
        coinsound.play() 
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
        self.displayWalletMenu()


    def freshenUp(self):
        cdd,alreadythere = self.getCurrentCurrency()
        transport = self.getHTTPTransport(cdd.issuerServiceLocation)
        self.wallet.freshenUp(transport,cdd)
        coinsound.play() 
        self.displayWalletMenu()


    def execute(self):
        #print 'execute'
        print self.todo

    def receiveCoins(self):
        methodlist = [u'bluetooth',u'internet']
        method = appuifw.popup_menu(methodlist,u'how to connect?')

        cdd,alreadythere = self.getCurrentCurrency()
        transport = self.getHTTPTransport(cdd.issuerServiceLocation)

        if method ==0:
            self.receiveCoinsBT(transport)
        else:
            self.receiveCoinsHTTP(transport)

        coinsound.play() 
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
        self.startInternet()
        
        #hack to open internet
        #r = urllib.urlopen('http://google.com')
        
        httpd = BaseHTTPServer.HTTPServer(("",port),OCHandler)
        self.feedback(u'waiting at %s:%s' % ('localhost',port),'conf')
        httpd.handle_request()
        httpd.handle_request()
        self.stopInternet()

    def getBTTransport(self):
        
        import btsocket
        sock=btsocket.socket(btsocket.AF_BT,btsocket.SOCK_STREAM)
        addr,services=btsocket.bt_discover()
        if len(services)>0:
            #choices=services.keys()
            #choices.sort()
            #choice=appuifw.popup_menu([unicode(services[x])+": "+x for x in choices],u'Choose port:')
            #port=services[choices[choice]]
            port = services[u'opencoin']
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
            self.feedback(u'Receive coins: ready to receive...')
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
            
        methodlist = [u'bluetooth',u'internet']
        method = appuifw.popup_menu(methodlist,u'how to connect?')


        cdd,alreadythere = self.getCurrentCurrency()
        if method == 1:
            url = appuifw.query(u'url','text',u'http://192.168.2.105:9091')
            transport = self.getHTTPTransport(url)
            self.wallet.spendCoins(transport,cdd.currencyId,amount,target)
        else:
            ready =self.query('Is the other side ready to receive?')
            if ready:
                transport = self.getBTTransport() 
                self.wallet.spendCoins(transport,cdd.currencyId,amount,target)

        self.displayWalletMenu()




    def getApproval(self,message):
        amount = message.amount
        target = message.target
        return self.query(u'"%s": accept %s coins?' % (target,amount)) 

    def query(self,text):
        return appuifw.query(unicode(text),'query')
    




    def startInternet(self):
        if not self.ip:
            import sys
            if sys.platform == 'symbian_s60':
                self.feedback(u'Preparing internet access:searching access points')
                e32.ao_sleep(1)
                import socket
                aps = [ap['name'] for ap in socket.access_points()]
                aps.sort()
                apid = appuifw.popup_menu(aps,u'select access point')
                self.feedback(u'Preparing internet access:setting access point')
                e32.ao_sleep(1)

                socket.set_default_access_point(aps[apid])
                self.ip = 'some ip, s60'

            else:
                import socket
                self.ip = 'some ip'
            

    def stopInternet(self):
        pass

def status(text):
    if ':' in text:
        appuifw.app.body = appuifw.Listbox([tuple([unicode(p.strip()) for p in text.split(':')]),], lambda:None)
    else:        
        appuifw.app.body = appuifw.Listbox([unicode(text)], lambda: None)

def startup(text):
    status('Welcome to opencoin!:loading... '+text)
############################### main code ############################        
app_lock = e32.Ao_lock()
appuifw.app.screen='normal'
appuifw.app.exit_key_handler = app_lock.signal

startup('network')
import httplib, urllib
startup('graphics')
from graphics import *
startup('ui')
import audio
import sys
import encodings
from key_codes import EKeyLeftArrow, EKeyRightArrow

startup('storage')
from oc2 import storage
startup('oc wallet')
from oc2 import wallet
startup('transports')
from oc2 import transports


startup('media')
icon = appuifw.Icon(u'e:\\python\\coin_icon.mif',16384,16385)
coinsound = audio.Sound.open('e:\\python\\coinsound.wav')


#appuifw.app.screen='full'
startup('coins')
storage = storage.Storage()
storage.setFilename('wallet.bin')
storage.restore()
startup('done')
w = WalletClient(storage)
import time
app_lock.wait()
status('Shut down:saving data...')
storage.save()
status('Shut down:exit')
time.sleep(1)
