from container import Container,Field
import sha
import rsa

  

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
        return rsa.encrypt(data,self.key)

    def verifySignature(self,signature,data):
        clear = rsa.verify(signature,self.key)
        return data == clear

    def verifyContainerSignature(self,container):
        signature = container.signature
        data = container.toString()
        return self.verifySignature(signature=signature,data=data)

    def createBlindingSecret(self):
        return rsa.getUnblinder(self.key['n'])

    def blind(self,data):
        secret = self.createBlindingSecret()
        blinder =  rsa.powMod(rsa.invMod(secret, self.key['n']), self.key['e'], self.key['n'])
        blinded = rsa.blind(data,blinder,self.key)
        return secret, blinded

    def unblind(self,secret,data):
        #number =  cryptomath.stringToNumber(data)
        number = data
        return (number * secret) % self.key['n']

class PrivKey(Container):
    
    fields = [KeyField('key'),
              Field('signature',signing=False)]

    def decrypt(self,data):
        return rsa.decrypt(data,self.key)

    def sign(self,data):
        return rsa.sign(data,self.key)

    def signblind(self,number):
        return rsa.encrypt_int(number,self.key['d'],self.key['p']*self.key['q'])

    def signContainer(self,container):
        signature =  self.sign(container.toString())
        container.signature = signature
        return container

def hash(data):
    return sha.sha(data).digest()

def KeyFactory(bitlen):
    pub,priv = rsa.gen_pubpriv_keys(bitlen)
    pubkey = PubKey()
    pubkey.key = pub
    privkey = PrivKey()
    privkey.key = priv
    return privkey,pubkey
 
if __name__ == '__main__':
    keys = KeyFactory(1024)
