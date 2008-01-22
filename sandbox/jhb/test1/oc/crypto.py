

#The following is for s60 compatibility 
import rsa
import crypto_mathew as cm

class SimpleKeyPair:
    def __init__(self,pub=None,priv=None,size=1024):
        if not pub and not priv:
            (pub,priv) =  rsa.gen_pubpriv_keys(size)
        self.privateKey = SimplePublicKey(priv)
        self.publicKey = SimplePrivateKey(pub)


class SimplePublicKey:
    
    def __init__(self,key):
        self.key = key

    def encrypt(self,message):
        return rsa.encrypt(message,self.key)

    def decrypt(self,message):
        return rsa.verify(message,self.key)


class SimplePrivateKey:
    
    def __init__(self,key):
        self.key = key

    def encrypt(self,message):
        return rsa.sign(message,self.key)

    def decrypt(self,message):
        return rsa.decrypt(message,self.key)




class MixedKeyPair:

    def __init__(self,pub=None,priv=None,size=1024):
        if not pub and not priv:
            keypair =   cm.createRSAKeyPair(size)
            key = keypair.key
            priv = {'d': key.d, 'p': key.p, 'q': key.n}
            pub = {'e': key.e, 'n': key.n}

        self.privateKey = SimplePublicKey(pub)
        self.publicKey = SimplePrivateKey(priv)

#and now some faster key

class FastKeyPair:
    def __init__(self,pub=None,priv=None,size=1024):
        if not pub and not priv:
            keypair =  cm.createRSAKeyPair(size)
            private = keypair.private()
            public = keypair.public()
        self.privateKey = FastKey(private)
        self.publicKey = FastKey(public)

class FastKey:

    def __init__(self,key):
        self.key = key

    def encrypt(self,message):
        return self.key.encrypt(message,'')

    def decrypt(self,message):
        return self.key.decrypt(message)

    def sign(self,message):
        return self.key.sign(message,'')

    def verify(self,message):
        return self.key.verify(message)
     
print __name__     
if __name__ == '__main__':
    pair = MixedKeyPair(size=512)
    public = pair.publicKey
    private = pair.privateKey
    c = public.encrypt('foo')
    print private.decrypt(c)
