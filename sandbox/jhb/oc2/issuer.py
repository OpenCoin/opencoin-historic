from entity import *
import datetime

class Issuer(Entity):
 
    def createMasterKeys(self):
        priv,pub = occrypto.KeyFactory(1024)
        self.storage.masterPrivKey = priv
        self.storage.masterPubKey = pub

    def makeCDD(self, currencyId, 
                      shortCurrencyId, 
                      denominations, 
                      issuerServiceLocation, 
                      options):

        cdd = container.CDD()
        cdd.standardId='http://opencoin.org/OpenCoinProtocol/jhb1'
        cdd.currencyId = currencyId
        cdd.shortCurrencyId = shortCurrencyId
        cdd.denominations = denominations
        cdd.issuerServiceLocation = issuerServiceLocation
        cdd.options = options
        cdd.masterPubKey = self.storage.masterPubKey
        cdd.issuer = self.storage.masterPubKey.hash()
        if not hasattr(self.storage,'cdds'):
            self.storage.cdds = Item()
        cddlist = getattr(self.storage.cdds,shortCurrencyId,[])
        setattr(self.storage.cdds,shortCurrencyId,cddlist)
        cdd.version = len(cddlist)   
        self.storage.masterPrivKey.signContainer(cdd)
        cddlist.append(cdd)
        return cdd

    def getCDD(self,shortCurrencyId,version=None):
        cddlist = getattr(self.storage.cdds,shortCurrencyId,None)
        if version:
            return cddlist[version]
        else:
            return cddlist[-1]

    def getMasterPubKey(self):
        return self.storage.masterPubKey

    def _getMasterPrivKey(self):
        return self.storage.masterPrivKey

    def signMintKeys(self,keys,
                         cdd=None,
                         notBefore=None,
                         keyNotAfter=None,
                         coinNotAfter=None):
        if not cdd:
            cdd = self.getCDD(shortCurrencyId)
        
       
        masterKey = self._getMasterPrivKey()

        for denomination,pub in keys.items():
            mkc = container.MKC()
            mkc.keyId = pub.hash()
            mkc.currencyId = cdd.currencyId
            mkc.version = cdd.version
            mkc.denomination = denomination
            mkc.notBefore = notBefore and notBefore or datetime.datetime.now()
            mkc.keyNotAfter = keyNotAfter and keyNotAfter or mkc.notBefore + datetime.timedelta(365)
            mkc.coinNotAfter = coinNotAfter and coinNotAfter or mkc.notBefore + datetime.timedelta(365)
            mkc.publicKey = pub
            mkc.issuer = cdd.issuer
            masterKey.signContainer(mkc)
            self.addMKC(cdd,mkc)

        return self.getCurrentMKCs()

    def addMKC(self,cdd,mkc):

        if not self.has('mkclist'):
            self.set('mkclist',[])
        mkclist = self.get('mkclist')            
        if len(mkclist) <= cdd.version:
            mkclist.append({})
        mkclist[cdd.version][mkc.denomination]=mkc    
        
    def getCurrentMKCs(self,version=-1):
        return self.get('mkclist')[version]

