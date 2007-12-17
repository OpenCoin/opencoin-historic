# Copyright (c) 2005 Jurgen Scheible
# This script performs a query with a single-field dialog, each with a
# different input type.
# It uses the .query() function of the appuifw module


# import the application user interface framework module
import appuifw


# text:
# create a single-field dialog (text input field):  appuifw.query(label, type)
data = appuifw.query(u"Type a word:", "text")
print data

# number:
# create a single-field dialog (number input field):  appuifw.query(label, type)
data = appuifw.query(u"Type a number:", "number")
print data

# date:
# create a single-field dialog (date input field):  appuifw.query(label, type)
data = appuifw.query(u"Type a date:", "date")
print data

# time:
# create a single-field dialog (time input field):  appuifw.query(label, type)
data = appuifw.query(u"Type a time:", "time")
print data

# code:
# create a single-field dialog (code input field):  appuifw.query(label, type)
data = appuifw.query(u"Type a code:", "code")
print data

# query:
# create a single-field dialog (question):  appuifw.query(label, type)
if appuifw.query(u"Are you ok:", "query") == True:
    print "you pressed ok"
else:
    print "you pressed cancel"

