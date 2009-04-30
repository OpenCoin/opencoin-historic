#
# e32dbm
#
# Authors: Marcelo Barros de Almeida <marcelobarrosalmeida@gmail.com>

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

"""
Emulation of e32dbm module from Python for S60

This module emulates the e32dbm functionality for testing and emulating
Symbian applications on a desktop.

"""

# Configurations tested (all with unicode enabled):
#  * Linux with wxPython 2.5.2


import dbm

class s60dbm:
    def __init__(self,filename,flag="r",mode=0666):
        self.dbm = dbm.open(filename,flag,mode)
        
    def has_key(self,key):
        return self.dbm.has_key(key)
    
    def update(self,e,**f):
        self.dbm.update(e,f)
        
    def iterkeys(self):
        return self.dbm.iterkeys()
    
    def iteritems(self):
        return self.dbm.iteritems()
    
    def itervalues(self):
        return self.dbm.itervalues()
    
    def get(self,k,d=None):
        if d:
            return self.dbm.get(k,d)
        else:
            return self.dbm.get(k)
        
    def setdefault(self,k,d=None):
        if d:
            return self.dbm.setdefault(k,d)
        else:
            return self.dbm.setdefault(k)
        
    def pop(self,k,d=None):
        if d:
            return self.dbm.pop(k,d)
        else:
            return self.dbm.pop(k)
        
    def popitem(self):
        return self.dbm.popitem()
    
    def clear(self):
        self.dbm.clear()

    def __getitem__(self,k):
        return self.dbm[k]

    def __setitem__(self,k,d):
        self.dbm[k] = d

    def __delitem__(self,k):
        del self.dbm[k]

    def __len__(self):
        return len(self.dbm)

    def __iter__(self):
        return self.iterkeys()

    def close(self):
        pass

    def reorganize(self):
        pass

    def sync(self):
        pass


def open(filename,flag="r",mode=0666):
    return s60dbm(filename,flag,mode)
