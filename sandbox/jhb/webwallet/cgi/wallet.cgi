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

    def out(self,text):
        if type(text) != type(''):
            text = str(text)
        self.output.append(text+'<br/>')
        
    def printout(self):
        print """Content-type:text/html"""
        print
        print '\n'.join(self.output)

    def getCurrency(self,currencyId):
        return dict(self.getCurrencies())[currencyId]

    def getCurrencies(self):
        return [(cdd.currencyId,(cdd,amount)) for cdd,amount in w.wallet.listCurrencies()]

    def dispatchRequest(self):
        self.env = os.environ
        self.form = cgi.FieldStorage(keep_blank_values=1)
        self.action = action = self.form.getfirst('action','')
        self.method = method = self.env['REQUEST_METHOD'].lower()
        

        if method == 'post':
            if action == 'addcurrency':
                self.addCurrency()
            elif action == 'mint':
                self.mintCoins()
            elif action == '':
                pass 

        elif method == 'get':
            if action == '':
                #basically nothing happened
                self.displayMain()
            elif action == 'addcurrency':
                self.displayAddCurrency()
            elif action == 'mint':
                self.displayMint()


    def addCurrency(self):
        url = self.form.getfirst('url','')
        if url:
            transport = transports.HTTPTransport(url)
            w.wallet.addCurrency(transport)
            storage.save()
        self.displayMain()        


    def mintCoins(self):
        amount = int(self.form.getfirst('amount',1))
        reference = self.form.getfirst('reference')
        cdd,wehave = self.getCurrency(self.form.getfirst('currencyId'))
        transport = transports.HTTPTransport(cdd.issuerServiceLocation)
        self.wallet.mintCoins(transport,amount,reference)
        self.storage.save()
        self.displayMain()


    def displayMain(self):
        tmp = [(cdd.currencyId,cdd,amount) for cdd,amount in self.wallet.listCurrencies()]
        tmp.sort()
        currencies = [(t[1],t[2]) for t in tmp]
        items = []
        for cdd,amount in currencies:
            entry = """
            <p>%s <b href='%s'>%ss</b><br/>
                <a href='%s?action=mint&currencyId=%s'>Withdraw</a>
            </p>
            """ % (amount,cdd.issuerServiceLocation,cdd.currencyId,baseurl,cdd.currencyId)
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

    def displayMint(self):
        currencyId = self.form.getfirst('currencyId','coin')
        html="""
        <html><body>
        <h2>Get new coins</h2>
        <form action='%s' method='post'>
            How many <b>%ss</b><br>
            <input type='text' name='amount' value='1' /><br>
            Reference<br>
            <input type='text' name='reference' value='secret' /><br>
            <input type='submit' />
            <input type='hidden' name='action' value='mint'/>
            <input type='hidden' name='currencyId' value='%s'/>
        </form>
        </body></html>

        """ % (baseurl,currencyId,currencyId)
        self.out(html)

        
baseserver = "http://%s:%s" % (os.environ['SERVER_NAME'],os.environ['SERVER_PORT'])
baseurl = os.environ['SCRIPT_NAME']



storage = oc2storage.Storage()
storage.setFilename(datadir+'/wallet.bin')
storage.restore()
w = CGIWallet(storage)
w.dispatchRequest()

#out('=' * 80)
#for key,value in sorted(env.items()):
#    #out("%50s: %s" % (key,value))
#    pass
#out(form.list)
w.printout()
