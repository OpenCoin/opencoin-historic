#!/usr/bin/python

libdir = '/home/joerg/opencoin'
datadir = '/home/joerg/opencoin/webwallet'

##################################

import sys, os
sys.path.append(libdir)
import cgitb; cgitb.enable()
import cgi
import oc2
from oc2 import storage as oc2storage
from oc2 import wallet, transports



class CGIWallet:

    def __init__(self,storage):
        self.storage = storage
        self.wallet = wallet.Wallet(storage)
        self.output = []
        self.mimetype = 'text/html'

    def out(self,text):
        if type(text) != type(''):
            text = str(text)
        self.output.append(text)
        
    def printout(self):
        print """Content-type:%s""" % self.mimetype
        print "\r"
        if self.mimetype == 'text/html':
            print '<br/>\n'.join(self.output)
        else:
            print '\n'.join(self.output)

    def getCurrency(self,currencyId):
        return dict(self.getCurrencies())[currencyId]

    def getCurrencies(self):
        return [(cdd.currencyId,(cdd,amount)) for cdd,amount in self.wallet.listCurrencies()]

    def dispatchRequest(self):
        self.env = os.environ
        self.form = cgi.FieldStorage(keep_blank_values=1)
        self.action = action = self.form.getfirst('action','')
        self.method = method = self.env['REQUEST_METHOD'].lower()
       
        postmapping = dict(addcurrency = self.addCurrency,
                           mint = self.mintCoins,
                           redeem = self.redeemCoins,
                           delcurrency = self.delCurrency,
                           spend = self.spendCoins)

        getmapping = dict(addcurrency = self.displayAddCurrency,
                          mint = self.displayMint,
                          redeem = self.displayRedeem,
                          spend = self.displaySpend,
                          delcurrency = self.displayDelCurrency,
                          freshenup = self.freshenUp)

        if method == 'post':
            if postmapping.has_key(action):
                postmapping[action]()
            else:
                self.receiveCoins()

        elif method == 'get':
            if getmapping.has_key(action):
                getmapping[action]()
            else:
                self.displayMain()


################################ main ################################################


    def displayMain(self):
        tmp = [(cdd.currencyId,cdd,amount) for cdd,amount in self.wallet.listCurrencies()]
        tmp.sort()
        currencies = [(t[1],t[2]) for t in tmp]
        items = []
        for cdd,amount in currencies:
            entry = """
            <p>%(amount)s <b href='%(isl)s'>%(cid)ss</b><br/>
                <a href='%(baseurl)s?action=spend&currencyId=%(cid)s'>Pay</a>
                <a href='%(baseurl)s?action=freshenup&currencyId=%(cid)s'>Refresh</a>
                <a href='%(baseurl)s?action=mint&currencyId=%(cid)s'>Withdraw</a>
                <a href='%(baseurl)s?action=redeem&currencyId=%(cid)s'>Redeem</a>
                <a href='%(baseurl)s?action=delcurrency&currencyId=%(cid)s'>Remove</a>
            </p>
            """ % dict(amount=amount,
                       isl=cdd.issuerServiceLocation,
                       cid=cdd.currencyId,
                       baseurl=baseurl)
            items.append(entry)
        items = '\n'.join(items)
        html = """
        <html><body>
        <h2>Wallet content</h2>
        %s
        ----<br/>
        <a href='%s?action=addcurrency'>Add a currency</a>
        </body></html>
        """ % (items,baseurl)
        self.out(html)

############################### add a currency ####################################


    def addCurrency(self):
        url = self.form.getfirst('url','')
        if url:
            transport = transports.HTTPTransport(url)
            self.wallet.addCurrency(transport)
            self.storage.save()
        self.displayMain()        

    def displayAddCurrency(self):
        html="""
        <html><body>
        <h2>Add a currency</h2>
        <form action='%s' method='post'>
            The url of the issuer:<br>
            <input type='text' name='url' value='http://baach.de:9090' /><br>
            <input type='submit' />
            <input type='hidden' name='action' value='addcurrency'/>
        </form>
        </body></html>
        """ % baseurl
        self.out(html)



############################### delete a currency ####################################

    def displayDelCurrency(self):
        currencyId = self.form.getfirst('currencyId','')
        cdd,amount = self.getCurrency(currencyId)
        html="""
        <html><body>
        <h2>Remove  %s</h2>
        <form action='%s' method='post'>
            <p>Really really delete %s with %s coins - there is no way to recover</p>
            <p><input type='submit' value='Remove %ss'/>
            or
            
            <a href='%s'>go back to main screen</a>
            </p>
            <input type='hidden' name='action' value='delcurrency'/>
            <input type='hidden' name='currencyId' value='%s'/>
        </form>
        </body></html>
        """ % (currencyId,baseurl,currencyId,amount,currencyId,baseurl,currencyId)
        self.out(html)

    def delCurrency(self):
        id = self.form.getfirst('currencyId','')
        self.wallet.deleteCurrency(id)
        self.storage.save()
        self.displayMain()


############################### minting ####################################

    def mintCoins(self):
        amount = int(self.form.getfirst('amount',1))
        reference = self.form.getfirst('reference')
        cdd,wehave = self.getCurrency(self.form.getfirst('currencyId'))
        transport = transports.HTTPTransport(cdd.issuerServiceLocation)
        self.wallet.mintCoins(transport,amount,reference)
        self.storage.save()
        self.displayMain()


    def displayMint(self):
        currencyId = self.form.getfirst('currencyId','coin')
        html="""
        <html><body>
        <h2>Get new coins</h2>
        <form action='%s' method='post'>
            How many <b>%ss</b><br>
            <input type='number' name='amount' value='1' /><br>
            Optional message<br>
            <input type='text' name='reference' value='secret' /><br>
            <input type='submit' />
            <input type='hidden' name='action' value='mint'/>
            <input type='hidden' name='currencyId' value='%s'/>
        </form>
        </body></html>

        """ % (baseurl,currencyId,currencyId)
        self.out(html)

############################### redeem ####################################

    def redeemCoins(self):
        amount = int(self.form.getfirst('amount',1))
        reference = self.form.getfirst('reference')
        cdd,wehave = self.getCurrency(self.form.getfirst('currencyId'))
        transport = transports.HTTPTransport(cdd.issuerServiceLocation)
        self.wallet.redeemCoins(transport,amount,reference)
        self.storage.save()
        self.displayMain()


    def displayRedeem(self):
        currencyId = self.form.getfirst('currencyId','coin')
        html="""
        <html><body>
        <h2>Redeem coins</h2>
        <form action='%s' method='post'>
            How many <b>%ss</b><br>
            <input type='number' name='amount' value='1' /><br>
            Optional message<br>
            <input type='text' name='reference' value='secret' /><br>
            <input type='submit' />
            <input type='hidden' name='action' value='redeem'/>
            <input type='hidden' name='currencyId' value='%s'/>
        </form>
        </body></html>

        """ % (baseurl,currencyId,currencyId)
        self.out(html)

############################### spend ####################################

    def spendCoins(self):
        amount = int(self.form.getfirst('amount',1))
        reference = self.form.getfirst('reference')
        url = self.form.getfirst('url')
        url = 'http://%s:9091' % url
        cid = self.form.getfirst('currencyId')
        transport = transports.HTTPTransport(url)
        self.wallet.spendCoins(transport,cid,amount,reference)
        self.storage.save()
        self.displayMain()


    def displaySpend(self):
        currencyId = self.form.getfirst('currencyId','coin')
        html="""
        <html><body>
        <h2>Pay someone</h2>
        <form action='%s' method='post'>
            Recipient<br/>
            <input type='text' name='url' value='192.168.1.66' /><br>
            How many <b>%ss</b><br>
            <input type='number' name='amount' value='1' /><br>
            Optional message<br>
            <input type='text' name='reference' value='secret' /><br>
            Please make sure the other side is ready to accept!<br>
            <input type='submit' />
            <input type='hidden' name='action' value='spend'/>
            <input type='hidden' name='currencyId' value='%s'/>
        </form>
        </body></html>

        """ % (baseurl,currencyId,currencyId)
        self.out(html)

############################### freshenUp ####################################

    def freshenUp(self):
        cdd,wehave = self.getCurrency(self.form.getfirst('currencyId'))
        transport = transports.HTTPTransport(cdd.issuerServiceLocation)
        self.wallet.freshenUp(transport,cdd)
        self.storage.save()
        self.displayMain()


############################### freshenUp ####################################

    def receiveCoins(self):
        message = transports.createMessage(self.form.list[0].name)

        if message.header == 'SumAnnounce':
            answer = self.wallet.listenSum(message)
        if message.header == 'SpendRequest':
            cdd,wehave = self.getCurrency(message.coins[0].currencyId)
            transport = transports.HTTPTransport(cdd.issuerServiceLocation)
            answer = self.wallet.listenSpend(transport,message)
        self.storage.save()
        self.mimetype='text/plain'
        self.out(answer.toString(True))

baseserver = "http://%s:%s" % (os.environ['SERVER_NAME'],os.environ['SERVER_PORT'])
baseurl = os.environ['SCRIPT_NAME']

storage = oc2storage.Storage()
storage.setFilename(datadir+'/wallet.bin')
storage.restore()
w = CGIWallet(storage)
w.dispatchRequest()
w.printout()
