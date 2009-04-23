from entity import *
import messages

class Mint(Entity):

    def __init__(self,storage=None):
        Entity.__init__(self,storage)
        self.delay = False

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


    def addAuthKey(self,key):
        keyid = key.hash()
        self.storage.setdefault('authkeys',{})[keyid] = key

    def getAuthKey(self,keyid):
        return self.storage['authkeys'][keyid]

    def validateAuthorization(self,message):
        keyid = message.keyId
        key = self.getAuthKey(keyid)
        return key.verifyContainerSignature(message)

    def handleMintingRequest(self,authorizedMessage):
         
        if not self.validateAuthorization(authorizedMessage):
            return messages.TransferReject()
         
        message = authorizedMessage.message
        blinds = message.blinds
        return self._mintBlinds(message)
    
    def handleExchangeRequest(self,message):
        #import pdb; pdb.set_trace()
        coins = message.coins
        blinds = message.blinds
        payed = sum([int(coin.denomination) for coin in coins])
        
        amount = 0
        for keyid,blind in blinds:
            priv,pub,denomination,version = self.getMintKeyById(keyid)
            amount += int(denomination)
        
        if payed != amount:
            reject = messages.TransferReject()
            reject.reason = 'mismatch'
            return reject

        return self._mintBlinds(message)
            
    def _mintBlinds(self,message):
        
        blinds = message.blinds
        result = []
        for keyid,blind in blinds:
            priv,pub,denomination,version = self.getMintKeyById(keyid)
            signature = priv.sign(blind)
            result.append(signature)

        if self.delay:
            self.addToTransactions(message.transactionId,result)
            answer =  messages.TransferDelay()
            answer.transactionId = message.transactionId
            answer.reason = 'mint asked to delay'
        else:            
            answer = messages.TransferAccept()
            answer.signatures = result
        
        return answer

    def addToTransactions(self,transactionId,result):
        self.storage.setdefault('transactions',{})[transactionId]=result
