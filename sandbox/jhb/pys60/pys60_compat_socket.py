# Socket simulation module
# must be imported on PC as: 
# "import pys60_compat_socket as socket"
#  Author:  Sergiy Krukovskyy <temer69@ukr.net>

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 

import appuifw

import socket

simulated_access_points = { 10: "life :) Internet", 15: "Vodafone Internet", 25: "WLAN" }
default_access_point = None

def select_access_point():
   """
   This opens popup selection where access points are listed and can be selected. Returns selected
   access point id.
   """
   
   apid = appuifw.selection_list([i['name'] for i in access_points()])
   if apid != None:
      apid+=1 # do not return zero
   return apid # may be None

def access_point(apid):
   """
   This creates access point object by given apid. Returns access point object.
   """
   return repr(apid)
   
def set_default_access_point(apo):
   """
   This sets the default access point that is used when socket is opened. Setting apo to "None" will
   clear default access point.
   """
   default_access_point = apo
   # raise ValueError('Parameter must be access point object or none')
   
def access_points():
   """
   This lists access points id's and names that are available.
   """
   return [{'iapid': k, 'name': unicode(v)} for k,v in simulated_access_points.items()]

# provide access to all canonical socket module's functions, classess, etc...   
def __getattr__(aAttr):
   return getattr(socket, aAttr)
      
def __setattr__(aAttr, aValue):
   return setattr(socket, aAttr, aValue)            
   