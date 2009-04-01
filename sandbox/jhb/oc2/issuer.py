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
            self.storage.cdds = []
        cdds = self.get('cdds')
        cdd.version = len(cdds)   
        self.storage.masterPrivKey.signContainer(cdd)
        cdds.append(cdd)
        return cdd

    def getCDD(self,version=None):
        cdds = self.get('cdds')
        if version:
            return cdds[version]
        else:
            return cdds[-1]

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

