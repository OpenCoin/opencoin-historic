from entity import *
import messages
class Authorizer(Entity):


    def __init__(self,storage=None):
        Entity.__init__(self,storage)
        self.deny = False

    def createKeys(self):
        priv,pub = occrypto.KeyFactory(1024)
        self.setKeys((priv,pub))
        return pub

    def setKeys(self,keys):
        self.storage.setdefault('keys',[]).append(keys)

    def _getKeys(self):
        return self.storage['keys'][-1]
    
    def denominationToValue(self,denomination):
        return int(denomination)

    def authorize(self,message):
        
        target = message.target
        blinds = message.blinds
        coins = message.coins

        amount = 0
        
        if self.deny:
            answer = messages.Error()
            answer.text = 'authorizer was told to deny'
            return answer

        for keyid,blind in blinds:
            mkc = self.getMKCById(keyid)
            amount += self.denominationToValue(mkc.denomination)
        if amount > 10000000:
            error = messages.Error()
            error.text = 'way too much'
            return error

        answer = messages.AuthorizedMessage()
        answer.message = message
        priv,pub = self._getKeys()
        answer.keyId = pub.hash()
        priv.signContainer(answer)
        return answer

    def setMKCs(self,mkcs):
        mkclist = self.storage.setdefault('mkcs',{})
        for mkc in mkcs:
            mkclist[mkc.keyId] = mkc

    def getMKCById(self,keyid):
        return self.storage['mkcs'][keyid]
