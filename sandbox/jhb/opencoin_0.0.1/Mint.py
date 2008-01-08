# (c) 2007 Nils Toedtmann, Joerg Baach, License GPL

import time, pprint, os, sha
from Crypto.PublicKey import *
from Crypto.Util.randpool import RandomPool
from Crypto.Util import number

pool = RandomPool()
pool.stir()

#The magical mint
class Mint:

    def __init__(self,issuerurl,denominations,keysize=256):
        """Sets up a mint for an issuer url, creating keys for the denominations
        >>> m = Mint('http://localhost',[1,2])
        """
        # ToDo: replace "keys" woth "pubkeys"
        self.keys = {}
        for d in denominations:
            self.keys[d] = RSA.generate(keysize, pool.get_bytes)


    def getPubKeys(self):
        """Return the pubkeys
        >>> m = Mint('http://localhost',[1,2])
        """
        return dict((d,k.publickey()) for d,k in self.keys.items())

    def signBlind(self,blind,value):
        #mint the coin
        return self.keys[value].sign(blind,None)[0]

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
