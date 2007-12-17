# Copyright (c) 2006 Jurgen Scheible
# This script creates a form


import appuifw
import e32

# create an Active Object
app_lock = e32.Ao_lock()


def forming():
    # create a list to be used in 'combo' selection mode
    model = [u'6600', u'6630', u'7610', u'N90', u'N70']
    
    # define the field list (consists of tuples: (label, type ,value)); label is a unicode string
    # type is one of the following strings: 'text', 'number', 'date', 'time',or 'combo'
    data = [(u'Mobile','text', u'Nokia'),(u'Model','combo', (model,0)),(u'Amount','number', 5),(u'Date','date'),(u'Time','time')]

    # set the view/edit mode of the form  
    flags = appuifw.FFormEditModeOnly

    # creates the form
    f = appuifw.Form(data, flags)
    
    # make the form visible on the UI
    f.execute()

def exit_key_handler():
    app_lock.signal()
    
# set the title of the script
appuifw.app.title = u'Form'

# call the function that creates the form
forming()

appuifw.app.exit_key_handler = exit_key_handler
app_lock.wait()