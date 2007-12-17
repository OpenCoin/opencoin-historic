# Copyright (c) 2006 Jurgen Scheible
# This script creates tabs that let you switch between different applications


import appuifw
import e32
from graphics import *

def callback():
    print 'foo callback'
# define application 1: text app
app1 = appuifw.Text(u'Appliation o-n-e is on')

# define application 2: text app
app2 = appuifw.Text(u'Appliation t-w-o is on')

# define application 3: text app
app3 = appuifw.Listbox([(u'Sum',u'22'),(u'ones',u'12'),(u'twos',u'2')],callback)



def exit_key_handler():
    app_lock.signal()

# create a tab handler that switches the application based on what tab is selected
def handle_tab(index):
    global lb
    if index == 0:
        appuifw.app.body = app1 # switch to application 1
    if index == 1:
        appuifw.app.body = app2 # switch to application 2
    if index == 2:
        appuifw.app.body = app3 # switch to application 3
        appuifw.app.menu = [(u'Send',callback)]

    
# create an Active Object
app_lock = e32.Ao_lock()

# create the tabs with its names in unicode as a list, include the tab handler
appuifw.app.set_tabs([u"One", u"Two", u"Three"],handle_tab)

# set the title of the script
appuifw.app.title = u'Tabs'

# set app.body to app1 (for start of script)
appuifw.app.body = app1


appuifw.app.exit_key_handler = exit_key_handler
app_lock.wait()
