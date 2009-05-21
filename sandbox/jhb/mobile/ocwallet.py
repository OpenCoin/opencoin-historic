import appuifw,e32,os,sys

class WalletClient:

    def __init__(self,storage):
        self.storage = storage
        self.wallet = wallet.Wallet(storage)
        self.wallet.getApproval = self.getApproval
        self.wallet.feedback = self.feedback
        self.displayWalletMenu()        
        self.actions=[(u'Send',u'Send coins to someone',icons['right'],self.spendCoins),
                      (u'Receive',u'Receive coins',icons['left'],self.receiveCoins),
                      (u'Freshen up',u'Freshen up the coins',icons['refresh'],self.freshenUp),
                      (u'Mint',u'new coins from issuer',icons['down'],self.mintCoins),
                      (u'Redeem',u'redeem from issuer',icons['up'],self.redeemCoins),
                      (u'Details',u'See what coins you hold',icons['coins'],self.inspectCurrency),]

        
        self.todo = {}
        self.ip = None
        self.external_ip = None
        self.imagecounter = 0

    def makeWalletMenu(self):
        self.wallet_list = []
        tmp = [(cdd.currencyId,cdd,amount) for cdd,amount in self.wallet.listCurrencies()]
        tmp.sort()
        self.currencies = [(t[1],t[2]) for t in tmp]

        for cdd,amount in self.currencies:
            title = u'%s %ss' % (amount,cdd.currencyId)
            description = unicode(cdd.issuerServiceLocation)
            self.wallet_list.append((title,description,icons['opencoin']))
        if not self.wallet_list:
            self.wallet_list.append(u'no currencies yet')
            self.wallet_menu =  appuifw.Listbox(self.wallet_list,self.displayActionMenu)
        else:
            self.wallet_menu =  appuifw.Listbox(self.wallet_list,self.displayActionMenu)
            self.wallet_menu.bind(EKeyRightArrow,self.displayActionMenu)

    def feedback(self,text,cb=None):
        status(unicode(text),callback=cb)
        

    def displayWalletMenu(self):
        self.makeWalletMenu()
        appuifw.app.body =  self.wallet_menu
        appuifw.app.title = u'opencoin wallet\nall currencies'
        appuifw.app.menu = [(u'add currency',self.addCurrency),
                            (u'delete currency',self.delCurrency)]

    def displayActionMenu(self):

        action_list = [(action[0],action[1],action[2]) for action in self.actions]
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
        self.actions[current][3]()


    def getAmount(self,min=1,max=-1):
        ok = False  
        text = ['Amount']
        text.append('min %s' % min)
        if max != -1:
            text.append('max %s' % max)
        text = u', '.join([unicode(t) for t in text])                
        while not ok:
            amount = appuifw.query(text,'number')
            if amount:
                amount = int(amount)
                if amount < min:
                    appuifw.note(u'amount to small','error')
                    continue
                if max != -1 and amount > max:
                    appuifw.note(u'amount to large','error')
                    continue
            ok = True                    

        self.todo['amount'] = amount
        return amount

    def getTarget(self):
        target = ''
        while target == '':
            target = appuifw.query(u'Reference','text')
        self.todo['target'] = target
        return target            


    def inspectCurrency(self):
        #print 'inspect'
        cdd,amount = self.getCurrentCurrency()
        id = cdd.currencyId
        coins = self.wallet.getAllCoins(id)
        coinlist = []
        for coin in coins:
            coinlist.append((unicode(cdd.currencyId),unicode(coin.denomination),icons['coin']))
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
        cdd,alreadythere = self.getCurrentCurrency()
        amount = self.getAmount(max=alreadythere)
        if not amount:
            return
        
        target = self.getTarget()
        if not target:
            return

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


    def receiveCoins(self):
        methodlist = [u'bluetooth',u'internet']
        method = appuifw.popup_menu(methodlist,u'how to connect?')

        cdd,alreadythere = self.getCurrentCurrency()
        if method ==0:
            transport = self.getHTTPTransport(cdd.issuerServiceLocation)
            self.receiveCoinsBT(transport)
        else:
            transport = self.getHTTPTransport(cdd.issuerServiceLocation)
            self.receiveCoinsHTTP(transport,walletport)

        coinsound.play() 
        self.displayWalletMenu()
    


    def getHTTPTransport(self,url):
        self.startInternet()
        transport = transports.HTTPTransport(url)
        return transport
    
    def receiveCoinsHTTP(self,transport,port):
        import BaseHTTPServer, urllib,socket
       
        class StoppableHTTPServer(BaseHTTPServer.HTTPServer):

            def server_bind(self):
                BaseHTTPServer.HTTPServer.server_bind(self)
                self.socket.settimeout(0.5)
                self.run = True

            def get_request(self):
                while self.run:
                    try:
                        e32.ao_yield()
                        sock, addr = self.socket.accept()
                        sock.settimeout(None)
                        return (sock, addr)
                    except socket.timeout:
                        if not self.run:
                            self.socket.close()
                            raise socket.error

            def stop(self):
                self.run = False

            def serve(self):
                while self.run:
                    self.handle_request()


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

            def log_message(self,*args,**kwargs):
                pass

        OCHandler.wallet = self.wallet
        self.startInternet()
        
        self.httpd = StoppableHTTPServer(("",port),OCHandler)
        self.feedback(u'Receiving coins: waiting at %s' % (self.ip),self.stopReceiveCoinsHTTP)
        if self.httpd.run:
            self.httpd.handle_request()
        if self.httpd.run:
            self.httpd.handle_request()
        self.httpd.socket.close()          
        self.stopInternet()

    def stopReceiveCoinsHTTP(self):
        self.httpd.stop()


    def getBTTransport(self):
        if sys.platform == 'symbian_s60': 
            import btsocket
            sock=btsocket.socket(btsocket.AF_BT,btsocket.SOCK_STREAM)
            addr,services=btsocket.bt_discover()
            if len(services)>0:
                port = services[u'opencoin']
            else:
                port=services[services.keys()[0]]
            address=(addr,port)
            sock.connect(address)
        else:
            import bluetooth as bt
            #evil hack
            appuifw.note(u'Searching for devices','info')
            results = [r for r in bt.find_service() if r['name']==None]
            targets = []
            for result in results:
                targets.append(u'%s' % (bt.lookup_name(result['host'])))
            selected = appuifw.popup_menu(targets,u'Connect to...?')
            
            host = results[selected]['host']
            #port = results[selected]['port']
            port = 3
            print 'host: %s, port: %s' % (host,port)
            sock=bt.BluetoothSocket( bt.RFCOMM )
            sock.connect((host, port))

            



        return transports.BTTransport(sock)

  
    
    def receiveCoinsBT(self,transport):
        if sys.platform == 'symbian_s60':
            import btsocket
            server_socket = btsocket.socket(btsocket.AF_BT, btsocket.SOCK_STREAM)
            #port = btsocket.bt_rfcomm_get_available_server_channel(server_socket)
            #server_socket.bind(("", port))
            server_socket.bind(("", 3))
            server_socket.listen(1)
            btsocket.bt_advertise_service( u"opencoin", server_socket, True, btsocket.RFCOMM)
            btsocket.set_security(server_socket, btsocket.AUTH)
            self.feedback(u'Receive coins: ready to receive...')
            (sock,peer_addr) = server_socket.accept()

        else:
            import bluetooth as bt
            server_sock=bt.BluetoothSocket(bt.RFCOMM)
            #server_sock.bind(("",bt.PORT_ANY))
            server_sock.bind(("",3))
            server_sock.listen(1)
            port = server_sock.getsockname()[1]

            uuid = "9e72d9d8-e06d-41cb-bbd4-89cd052cccb8"
            bt.advertise_service( server_sock, u"opencoin",
                   service_id = uuid,
                   service_classes = [ uuid, bt.SERIAL_PORT_CLASS ],
                   profiles = [ bt.SERIAL_PORT_PROFILE ] )
 
            #bt.advertise_service( server_sock, u"opencoin",)
                               
            self.feedback(u'Receive coins: ready to receive...')
            sock, client_info = server_sock.accept()

        bt = transports.BTTransport(sock)
        self.wallet.getApproval = self.getApproval 
        bt.send(self.wallet.listenSum(bt.receive()))
        self.feedback(u'Receive coins: receiving...')
        bt.send(self.wallet.listenSpend(bt.receive(),transport))
        import e32
        e32.ao_sleep(1)    


    def spendCoins(self):

        cdd,alreadythere = self.getCurrentCurrency()
        
        amount = self.getAmount(max=alreadythere)
        if not amount:
            return
        
        target = self.getTarget()
        if not target:
            return
            
        methodlist = [u'bluetooth',u'internet']
        method = appuifw.popup_menu(methodlist,u'how to connect?')


        if method == 1:
            url = appuifw.query(u'address','text',u'192.168.2.105')
            if not url:
                return                
            else:     
                url = 'http://%s:%s' % (url,walletport)
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
            import socket
            if sys.platform == 'symbian_s60':
                self.feedback(u'Preparing internet access:searching access points')
                aps = [ap['name'] for ap in socket.access_points()]
                aps.sort()
                apid = appuifw.popup_menu(aps,u'select access point')
                self.feedback(u'Preparing internet access:setting access point')

                socket.set_default_access_point(aps[apid])
           
            else:
                import socket
                self.ip = 'some ip'
            
            #one time socket, for just finding out our ip
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #anonymity issue here
            s.connect(('www.google.com',80))
            self.ip = s.getsockname()[0]


    def stopInternet(self):
        pass

def filmIt(foo=None):
    import os
    image = screenshot()
    counter = len(os.listdir('e:\\screenshots'))
    filename = 'e:\\screenshots\\ocwallet%s.jpg' % counter
    image.save(filename,filmIt)


def status(text,icon=None,callback=None):
    if ':' in text:
        items = [unicode(p.strip()) for p in text.split(':',1)]
    else:        
        items = [unicode(text)]
    if icon:
        items.append(icon)
            
    body = appuifw.Listbox([tuple(items)], lambda: None)
    if callback:
            body.bind(EKeyLeftArrow,callback)
    appuifw.app.body=body
    e32.ao_sleep(0.3)

def startup(text):
    if sys.platform == 'symbian_s60':
        status('opencoin: loading '+text,icons['restore'])



############################### main code ############################        
walletport = 9091
app_lock = e32.Ao_lock()
appuifw.app.screen='normal'
appuifw.app.exit_key_handler = app_lock.signal
import oc2
import sys
oc2path = oc2.__file__
if sys.platform == 'symbian_s60':
    basedrive = oc2path[:2]
    if oc2path[3:].startswith('python'):
        #no standalone app
        mediapath = u'%s\\python\\' % basedrive
    else:
        #standalone app
        mediapath = u'%s\\private\\%s\\' % (basedrive,appuifw.app.uid())
else:
    mediapath = u''
        
#only for documenting it
#from graphics import *
#filmIt()

names = dict(coin=0,opencoin=1,coins=2,detail=3,down=4,left=5,refresh=6,
             restore=7,right=8,save=9,up=10,zoom=11)
icons = dict([(k,appuifw.Icon(mediapath+u'ocicons.mbm',v*2,v*2+1)) for k,v in names.items()])

startup('storage')
from oc2 import storage as oc2storage
password = ''
while 1:
    password = appuifw.query(u'password','text')

    if password == None:
        sys.exit()   
    startup('encrypted data')
    storage = oc2storage.CryptedStorage()
    storage.setPassword(password)
    storage.setFilename('wallet.bin')
    try:
        storage.restore()
        break
    except:
        pass


startup('netlib')
import httplib, urllib
startup('ui')
import audio
import encodings
from key_codes import EKeyLeftArrow, EKeyRightArrow

startup('oc wallet')
from oc2 import wallet
startup('transports')
from oc2 import transports
startup('media')



coinsound = audio.Sound.open(mediapath+u'coinsound.wav')


#appuifw.app.screen='full'
startup('coins')
startup('done')
w = WalletClient(storage)
import time
app_lock.wait()
status('Shut down:saving data...',icons['save'])
storage.save()
status('Shut down:exit',icons['save'])
time.sleep(1)
