import types
from Crypto.Util import number
import base64

class CryptoContainer:
    def __init__(self, signing=None, encryption=None, blinding=None, hashing=None):
        self.signing = signing
        self.encryption = encryption
        self.blinding = blinding
        self.hashing = hashing

        import types

        if self.signing and not isinstance(self.signing, types.ClassType):
            raise CryptoError('Tried to add something to the container that was not a class!')
        if self.hashing and not isinstance(self.hashing, types.ClassType):
            raise CryptoError('Tried to add something to the container that was not a class!')
        if self.encryption and not isinstance(self.encryption, types.ClassType):
            raise CryptoError('Tried to add something to the container that was not a class!')
        if self.blinding and not isinstance(self.blinding, types.ClassType):
            raise CryptoError('Tried to add something to the container that was not a class!')

    def __str__(self):
        include = []
        if self.signing:
            include.append(str(self.signing))
        if self.encryption:
            include.append(str(self.encryption))
        if self.blinding:
            include.append(str(self.blinding))
        if self.hashing:
            include.append(str(self.hashing))

        # the order is always SIGN-ALG, ENCRYPTION-ALG, BLINDING-ALG, HASH-ALG

        return '[' + ', '.join(include) + ']'

    
class SigningAlgorithm:
    def __init__(self, key, input=None):
        self.key = key
        if input:
            self.update(input)

    def update(self, input):
        """updates the object with more information to sign."""
        raise NotImplementedError

    def sign(self):
        """returns the signature of the hash of the data."""
        raise NotImplementedError

    def verify(self):
        """returns if the signature inputted is valid."""
        raise NotImplementedError

    def reset(self):
        """resets the data for signing to it's default value."""
        raise NotImplementedError

    def __str__(self):
        """returns only the name of the signing algorithm in accordance with the SIGN-ALG name."""
        return self.ALGNAME

class BlindingAlgorithm:
    def __init__(self, key, input=None):
        self.key = key
        if input:
            self.update(input)

    def update(self, input):
        """updates the hash with more hashing information."""
        raise NotImplementedError

    def digest(self):
        """returns the digest of the hash. This does not automatically reset the hash."""
        raise NotImplementedError

    def reset(self):
        """resets the hash to it's default value."""
        raise NotImplemenetedError

    def __str__(self):
        """returns only the name of the hash function in accordance with the HASH-ALG name."""
        return self.ALGNAME


class EncryptionAlgorithm:
    def __init__(self, key, input=None):
        self.key = key
        if input:
            self.update(input)

    def update(self, input):
        """updates the object with more information to encrypt/decrypt."""
        raise NotImplementedError

    def encrypt(self):
        """returns the encryption of the plaintext."""
        raise NotImplementedError

    def decrypt(self):
        """returns the decryption of the ciphertext."""
        raise NotImplementedError
    
    def reset(self):
        """resets the data for encryption/decryption to it's default value."""
        self.hashing.reset()

    def __str__(self):
        """returns only the name of the encryption algorithm in accordance with the ENCRYPTION-ALG name."""
        return self.ALGNAME

    

class HashingAlgorithm:
    def __init__(self, input=None):
        if input:
            self.update(input)

    def update(self, input):
        """updates the hash with more hashing information."""
        raise NotImplementedError

    def digest(self):
        """returns the digest of the hash. This does not automatically reset the hash."""
        raise NotImplementedError

    def reset(self):
        """resets the hash to it's default value."""
        raise NotImplemenetedError

    def __str__(self):
        """returns only the name of the hash function in accordance with the HASH-ALG name."""
        return self.ALGNAME


class KeyPair:
    def __init__(self, public, private):
        self.public = public
        self.private = private

    def hasPrivate(self):
        """hasPrivate returns whether the KeyPair has the private key."""
        return self.private
   
class RSAKeyPair(KeyPair):
    from Crypto.PublicKey import RSA
    def __init__(self, key=None, p=None, q=None, e=None, d=None, n=None, u=None):
        self.key = key

        if not key: # we weren't passed in a key. Have to figure it out ourselves. yay!
            #this function builds just the parts of the tuple contstruct uses
            li = [n, e]
            if d:
                li.append(d)
            if p and q:
                li.append(p, q)
            if u:
                li.append(u)
                
            self.key = RSA.construct(tuple(li))


    def hasPrivate(self):
        return self.key.has_private()

    def public(self):
        return self.key.publickey()

    def private(self):
        if not self.hasPrivate():
            raise CryptoError('Do not have private key')

        return self.key

    def size(self):
        return self.key.size()

    def __str__(self):
        """The string representation of the key. Always the public key."""
        values = [base64.b64encode(number.long_to_bytes(self.key.n)), base64.b64encode(number.long_to_bytes(self.key.e))]
        return ','.join(values)

    def stringPrivate(self):
        if self.hasPrivate():
            key = self.key
            return ','.join([base64.b64encode(number.long_to_bytes(i)) for i in [key.d,key.p,key.q]])
        else: 
            return ''
    
    def toJson(self):
        import json

        return json.write(dict(public=str(self),private=self.stringPrivate()))


    def newPublicKeyPair(self):
        return RSAKeyPair(self.key.publickey())

def createRSAKeyPair(N):
    """Creates an RSA keypair of size N."""
    from Crypto.PublicKey import RSA

    _r.verifyEntropy(N)
    rsaKey = RSA.generate(N, _r.get_bytes)
    return RSAKeyPair(key=rsaKey)


class RSAEncryptionAlgorithm(EncryptionAlgorithm):
    from Crypto.PublicKey import RSA

    def __init__(self, key, input=None):
        self.input = ''
        if not isinstance(key, RSAKeyPair):
            raise CryptoError('key not RSAKeyPair type!. key.__class__: %s' % key.__class__)
        
        EncryptionAlgorithm.__init__(self, key, input)

        self.ALGNAME = 'RSAEncryptionAlgorithm'
        
    def update(self, input):
        self.input = self.input + input
        return self

    def reset(self, input=''):
        self.input = ''
        if input:
            self.update(input)
        return self

    def encrypt(self):
        try:
            return self.key.public().encrypt(self.input, '')[0]
        except PyCryptoRSAError:
            raise CryptoError
    
    def decrypt(self):
        try:
            return self.key.private().decrypt(self.input)
        except PyCryptoRSAError:
            raise CryptoError
        

class RSABlindingAlgorithm(BlindingAlgorithm):
    def __init__(self, key, input=None, blinding_factor=None):
        self.input = ''
        BlindingAlgorithm.__init__(self, key, input)
        self.blinding_factor = blinding_factor
        self.ALGNAME = 'RSABlindingAlgorithm'

    def update(self, input):
        """updates the algorithm with more hashing information."""
        if isinstance(input, types.LongType):
            input = number.long_to_bytes(input)
        self.input = self.input + input
        return self

    def blind(self, blinding_factor=None):
        """returns the blinding of the input with the key and the blinding factor."""
        if blinding_factor:
            self.blinding_factor = blinding_factor
            
        elif not self.blinding_factor:
            # self.key.size returns the size of the key - 1, which is acceptable
            self.blinding_factor = _r.getRandomNumber(self.key.size())

        else:
            pass #self.blinding_factor is already set

        try:
            return self.key.public().blind(self.input, self.blinding_factor), self.blinding_factor
        except PyCryptoRSAError:
            raise CryptoError

    def unblind(self, blinding_factor=None):
        """returns the unblinded value of the input."""
        if blinding_factor:
            self.blinding_factor = blinding_factor

        try:
            return self.key.public().unblind(self.input, self.blinding_factor)
        except PyCryptoRSAError:
            raise CryptoError
        
    def reset(self, input=''):
        """resets the algorithm to it's default value."""
        self.input = ''
        if input:
            self.update(input)
        return self

    
class RSASigningAlgorithm(SigningAlgorithm):
    def __init__(self, key, input=None):
        self.input = ''
        SigningAlgorithm.__init__(self, key, input)
        self.ALGNAME = 'RSASigningAlgorithm'

    def update(self, input):
        """updates the algorithm with more hashing information."""
        self.input = self.input + input
        return self

    def sign(self, message):
        """returns the signature of the message with the key."""
        try:
            key = self.key.private()
            result = key.sign(message, '')[0]
            if isinstance(message, types.StringType):
                return number.long_to_bytes(result)
            return result
        except PyCryptoRSAError, reason:
            print reason
            raise CryptoError('PyCryptoRSAError: %s' % reason)

    def verify(self, signature):
        """returns if the signature of the input is valid."""
        try:
            return self.key.public().verify(self.input, (number.bytes_to_long(signature),))
        except PyCryptoRSAError:
            raise CryptoError

    def reset(self, input=''):
        self.input = ''
        if input:
            self.update(input)
        return self

class SHA256HashingAlgorithm(HashingAlgorithm):
    def __init__(self, input=None):
        self.reset() # setup self.hash. We reset empty since HashingAlgorithm.__init__ will update!

        HashingAlgorithm.__init__(self, input)
        self.ALGNAME='SHA256HashingAlgorithm'

    def update(self, input):
        self.hash.update(input) 
        return self

    def digest(self):
        return self.hash.digest()

    def reset(self, input=''):
        from Crypto.Hash import SHA256
        self.hash = SHA256.new(input)
        return self
        
class CryptoError(Exception): pass

class Random:
    def __init__(self):
        from Crypto.Util.randpool import RandomPool
        self.RandomPool = RandomPool()

    def getRandomString(self, N):
        """Returns a N-bit length random string."""
        r = self.getRandomNumber(N)


        return number.long_to_bytes(r)
    
    def getRandomNumber(self, N):
        """Returns an N-bit length random number."""
        if self.RandomPool.entropy < 2 * N:
            self.RandomPool.randomize(4 * N)
            
        self.RandomPool.add_event('')
        self.RandomPool.stir()

        random = number.getRandomNumber(N, self.RandomPool.get_bytes)

        self.RandomPool.stir()

        return random

    def getPrime(self, N):
        """Returns a N-bit length prime."""
        if self.RandomPool.entropy < 2 * N:
            self.RandomPool.randomize(4 * N)

        self.RandomPool.add_event('')
        self.RandomPool.stir()

        prime = number.getPrime(N, self.RandomPool.get_bytes)

        self.RandomPool.stir()
        
        return prime

    def addEvent(self, text):
        """Adds a bit of random text to the pool as additional entropy. Use caution.
        The curreny implementation of this function just XORs the text over the entropy, probably
        giving it bias if we just roll through our messages. I'm not sure.
        """
        self.RandomPool.add_event(text)
        self.RandomPool.stir()

    def verifyEntropy(self, N):
        """Verifies enough entropy is in the RandomPool. If we are close to no entropy, attempt to add some."""
        if self.RandomPool.entropy < 2 * N:
            self.RandomPool.randomize(4 * N)

        self.RandomPool.add_event('')
        self.RandomPool.stir()

        if self.RandomPool.entropy < N: # if the stirring got rid of entropy, seed with more entropy
            self.verifyEntropy(2 * N)

    def get_bytes(self, num):
        """Get num bytes of randomness from the RandomPool."""
        return self.RandomPool.get_bytes(num)
            
_r = Random()    

import Crypto.PublicKey.RSA as quickRSA
PyCryptoRSAError = quickRSA.error
del quickRSA


