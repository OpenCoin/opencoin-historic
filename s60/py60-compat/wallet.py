# Copyright (c) 2006 Jurgen Scheible
# This script creates tabs that let you switch between different applications


import appuifw
import e32
from graphics import *
from key_codes import EKeyLeftArrow, EKeyRightArrow

def callback():
    print 'foo callback'

def exit_key_handler():
    app_lock.signal()

def setCurrency():
    
    cur = content[wallet.current()]
    l = [(u'%s %s' % (sum(cur['coins']),cur['name'])),
         (u'Send coins'),
         (u'Receive coins'),
         (u'-------------'),]

    for coin in cur['coins']:
        l.append(u'"%s" coin' % coin)
    
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

# set app.body to app1 (for start of script)
setWallet()

appuifw.app.exit_key_handler = exit_key_handler
app_lock.wait()
