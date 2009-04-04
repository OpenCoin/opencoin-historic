from entity import *

class Mint(Entity):

    def setCDD(self,cdd):
        self.storage['cdd'] = cdd
    
    def getCDD(self):
        return self.storage['cdd']
    
    def newMintKeys(self):
        cdd = self.getCDD()    
        version = cdd.version
        denominations = cdd.denominations
        out = {}
        for denomination in denominations:
            priv,pub = occrypto.KeyFactory(1024)
            self._addMintKey(priv,pub,denomination,version)
            out[denomination] = pub
        return out

    def _addMintKey(self,priv,pub,denomination,version=-1):
        keylist = self.storage.setdefault('keys',[])
        if version -1 > len(keylist) or len(keylist)==0:
            keylist.append({})
        keylist[version][denomination] = (priv,pub)

    def getMintKey(self,denomination,version=-1):
        keylist = self.storage['keys']
        return keylist[version][denomination][version] 
