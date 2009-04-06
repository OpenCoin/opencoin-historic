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
        keys = self.storage.setdefault('keys',[])
        keyids = self.storage.setdefault('keyids',{})
        if version -1 > len(keys) or len(keys)==0:
            keys.append({})
        keys[version][denomination] = [priv,pub]
        if version == -1:
            version = len(keys) -1
        keyids[pub.hash()] = [priv,pub,denomination,version]

    def getMintKeyByDenomination(self,denomination,version=-1):
        return self.storage['keys'][version][denomination]

    def getMintKeyById(self,keyid):
        return self.storage['keyids'][keyid]

    def denominationToValue(self,denomination):
        return int(denomination)


    def addAuthKey(self,key):
        keyid = key.hash()
        self.storage.setdefault('authkeys',{})[keyid] = key

    def getAuthKey(self,keyid):
        return self.storage['authkeys'][keyid]

    def validateAuthorization(self,message):
        keyid = message.keyId
        key = self.getAuthKey(keyid)
        return key.verifyContainerSignature(message)

    def handleTransferRequest(self,authorizedMessage):
        
        if not self.validateAuthorization(authorizedMessage):
            return ('nonvalid','')
        else: 
            message = authorizedMessage.message
        
        target = message.target
        blinds = message.blinds
        coins = message.coins

        amount = 0
        currentversion = len(self.storage['keys']) - 1
        errors = None
        result = []
        mintkeys = []

        for keyid,blind in blinds:
            error = None
            priv,pub,denomination,version = self.getMintKeyById(keyid)
            mintkeys.append(priv)
            if version != currentversion:
                error = 'Key not current'
            
            if error:
                errors = True
                result.append(('error',error))
            else:
                result.append(['ok',''])
    
            amount += self.denominationToValue(denomination)
        
        if errors:
            return ('errors',result)

        else:
            i = 0
            for keyid,blind in blinds:
                signature = mintkeys[i].sign(blind)
                result[i][1] = signature
                i += 1
                        
        return ('minted',result)


