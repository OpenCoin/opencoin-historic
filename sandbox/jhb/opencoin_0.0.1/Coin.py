# (c) 2007 Nils Toedtmann, Joerg Baach, License GPL
#The mighty coin
import time, pprint, os, sha
from Crypto.PublicKey import *
from Crypto.Util.randpool import RandomPool
from Crypto.Util import number
import cPickle as pickle

# Globals
pool = RandomPool()
pool.stir()

serialsize = 128

class Coin:

    def __init__(self,issuerurl,issuerPubKey,value):
        self.issuerurl =  issuerurl
        self.pubkey = issuerPubKey
        self.value = value
        self.serial = "%s %s %s" % (value,issuerurl, number.getRandomNumber(serialsize, pool.get_bytes))
        self.signature = None
        self.blindingFactor = number.getRandomNumber(self.pubkey.size() - 1, pool.get_bytes)
        self.deleted = None

    def __repr__(self):
        return "<Coin(%s,%s,%s)>" % (self.issuerurl,self.pubkey,self.value)

    def getHash(self):
        """get the Hash of the serial"""
        return sha.sha(self.serial).digest()

    def getBlind(self):
        """Returns the blinded hash of the coin"""
        return self.pubkey.blind(self.getHash(), self.blindingFactor)

    def verifySignature(self):
        return self.pubkey.verify(self.getHash(),(self.signature,))

    def setSignature(self,signature):
        signature = self.pubkey.unblind(signature, self.blindingFactor)
        if self.pubkey.verify(self.getHash(),(signature,)):
            self.signature = signature
            self.blindingFactor = None
            return True
        else:
            return False
