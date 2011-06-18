from container import Container,Field
import sha
from tlslite_utils import *



   


class KeyField(Field):
    
    def __init__(self,name,signing=True,isPrivate=False,default=''):
        Field.__init__(self,name=name,signing=signing,default=default)
        self.isPrivate = isPrivate

    def getencoded(self,object,allData=False):
        key = getattr(object,self.name,self.default)
        return key.write() 

    def setdecoded(self,object,data):
        if self.isPrivate:
            key = keyfactory.parsePrivateKey(data)
        else:
            key = keyfactory.parseAsPublicKey(data)
        setattr(object,self.name,key)


class PubKey(Container):

    fields = [KeyField('key'),
              Field('signature',signing=False)]

    def encrypt(self,data):
        bytes = compat.stringToBytes(data)
        encrypted = self.key.encrypt(bytes)
        return compat.bytesToString(encrypted)

    def verifySignature(self,signature,data):
        signatureBytes = compat.stringToBytes(signature)
        dataBytes = compat.stringToBytes(data)
        return self.key.verify(sigBytes=signatureBytes,bytes=dataBytes)

    def verifyContainerSignature(self,container):
        signature = container.signature
        data = container.toString()
        return self.verifySignature(signature=signature,data=data)

    def createBlindingSecret(self):
        return cryptomath.getRandomNumber(2,self.key.n)

    def blind(self,data):
        secret = self.createBlindingSecret()
        blinder =  cryptomath.powMod(cryptomath.invMod(secret, self.key.n), self.key.e, self.key.n)
        number = cryptomath.stringToNumber(data)
        return secret, pow(number,blinder,self.key.n)

    def unblind(self,secret,data):
        #number =  cryptomath.stringToNumber(data)
        number = data
        return cryptomath.numberToString((number * secret) % self.key.n)

class PrivKey(Container):
    
    fields = [KeyField('key'),
              Field('signature',signing=False)]

    def decrypt(self,data):
        bytes = compat.stringToBytes(data)
        decrypted = self.key.decrypt(bytes)
        return compat.bytesToString(decrypted)

    def sign(self,data):
        dataBytes = compat.stringToBytes(data)
        return compat.bytesToString(self.key.sign(dataBytes))

    def signblind(self,number):
        return pow(number,self.key.d,self.key.n)

    def signContainer(self,container):
        signature =  self.sign(container.toString())
        container.signature = signature
        return container

def hash(data):
    return sha.sha(data).digest()

def KeyFactory(bitlen):
    full = keyfactory.generateRSAKey(bitlen)
    keystring = full.write()
    pub = keyfactory.parseAsPublicKey(keystring)
    pubkey = PubKey()
    pubkey.key = pub
    privkey = PrivKey()
    privkey.key = full
    return privkey,pubkey
 
if __name__ == '__main__':
    keys = KeyFactory(1024)
