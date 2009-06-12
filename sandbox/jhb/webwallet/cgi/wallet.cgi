#!/usr/bin/python

libdir = '/home/joerg/opencoin'
datadir = '/home/joerg/opencoin/webwallet'

##################################

import cgitb; cgitb.enable()
import cgi
import sys, os
sys.path.append(libdir)
import oc2
from oc2 import storage as oc2storage
from oc2 import wallet, transports


def out(text):
    if type(text) != type(''):
        text = str(text)
    output.append(text+'<br/>')

def printout():
    print """Content-type:text/html"""
    print
    print '\n'.join(output)



class CGIWallet:

    def __init__(self,storage):
        self.storage = storage
        self.wallet = wallet.Wallet(storage)

    def getCurrency(self,currencyId):
        return dict(self.getCurrencies())[currencyId]

    def getCurrencies(self):
        return [(cdd.currencyId,(cdd,amount)) for cdd,amount in w.wallet.listCurrencies()]


baseserver = "http://%s:%s" % (os.environ['SERVER_NAME'],os.environ['SERVER_PORT'])
baseurl = os.environ['SCRIPT_NAME']

env = os.environ
form = cgi.FieldStorage(keep_blank_values=1)

subpath = env['PATH_INFO']

if subpath.startswith('/'):
    subpath=subpath[1:]
method = env['REQUEST_METHOD'].lower()

action = form.getfirst('action','')

output = []


storage = oc2storage.Storage()
storage.setFilename(datadir+'/wallet.bin')
storage.restore()
w = CGIWallet(storage)

#

if method=='post' and action == 'addcurrency':
    url = form.getfirst('url','')
    if url:
        transport = transports.HTTPTransport(url)
        w.wallet.addCurrency(transport)
        storage.save()
        action = ''
elif method=='post' and action == 'mint':
    amount = int(form.getfirst('amount',1))
    reference = form.getfirst('reference')
    cdd,wehave = w.getCurrency(form.getfirst('currencyId'))
    transport = transports.HTTPTransport(cdd.issuerServiceLocation)
    w.wallet.mintCoins(transport,amount,reference)
    action = ''

elif method == 'post' and action == '':
    #we got stuff posted from a wallet
    pass


if action == '':
    tmp = [(cdd.currencyId,cdd,amount) for cdd,amount in w.wallet.listCurrencies()]
    tmp.sort()
    currencies = [(t[1],t[2]) for t in tmp]
    items = []
    for cdd,amount in currencies:
        entry = """
        <li>%s %s<br/>
            %s<br>
            <a href='%s?action=mint&currencyId=%s'>Withdraw</a>
        </li>
        """ % (amount,cdd.currencyId,cdd.issuerServiceLocation,baseurl,cdd.currencyId)
        items.append(entry)
    items = '\n'.join(items)
    html = """
    <html><body>
    <b>Wallet content</b>
    <ul>
    %s
    </ul>
    ----<br/>
    <a href='%s?action=addcurrency'>Add a currency</a>
    </body></html>
    """ % (items,baseurl)
    out(html)

elif action == 'addcurrency':
    html="""
    <html><body>
    <b>Add a currency</b>
    <form action='%s' method='post'>
        The url of the issuer:<br>
        <input type='text' name='url' value='http://baach.de:9090' /><br>
        <input type='submit' />
        <input type='hidden' name='action' value='addcurrency'/>
    </form>
    </body></html>
    """ % baseurl
    out(html)

elif action == 'mint':
    currencyId = form.getfirst('currencyId','coin')
    html="""
    <html><body>
    <b>Get new coins</b>
    <form action='%s' method='post'>
        How many %ss<br>
        <input type='text' name='amount' value='1' /><br>
        Reference<br>
        <input type='text' name='reference' value='secret' /><br>
        <input type='submit' />
        <input type='hidden' name='action' value='mint'/>
        <input type='hidden' name='currencyId' value='%s'/>
    </form>
    </body></html>

    """ % (baseurl,currencyId,currencyId)
    out(html)

#out('=' * 80)
for key,value in sorted(env.items()):
    #out("%50s: %s" % (key,value))
    pass
#out(form.list)
printout()
