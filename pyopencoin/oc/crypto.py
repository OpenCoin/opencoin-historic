"""A Crypto library.
    >>> private = createRSAKeyPair(1024)
    >>> public = private.newPublicKeyPair()

    >>> public.hasPrivate()
    False
    
    >>> hash = SHA256HashingAlgorithm()
 
    >>> text = 'Foobar'
    >>> digest = hash.update(text).digest()

    >>> blinder = RSABlindingAlgorithm(public)
    >>> blinded, factor = blinder.blind(digest)

    >>> signer = RSASigningAlgorithm(private)
    >>> blinded_sig = signer.sign(blinded)
    
    >>> unblinded_sig = blinder.unblind(blinded_sig)

    >>> sig_verifier = RSASigningAlgorithm(public)
    >>> sig_verifier.verify(digest, unblinded_sig)
    True

    We can test encryption using the SHA256 digest as well
    >>> encrypt = RSAEncryptionAlgorithm(public)
    >>> decrypt = RSAEncryptionAlgorithm(private)
    >>> digest == decrypt.decrypt(encrypt.encrypt(digest))
    True
    """
import types
from Crypto.Util import number
import base64

class CryptoContainer:
    def __init__(self, signing=None, blinding=None, hashing=None):
        self.signing = signing
        self.blinding = blinding
        self.hashing = hashing

        import types

        if self.signing and not isinstance(self.signing, types.ClassType):
            raise CryptoError('Tried to add something to the container that was not a class!')
        if self.hashing and not isinstance(self.hashing, types.ClassType):
            raise CryptoError('Tried to add something to the container that was not a class!')
        if self.blinding and not isinstance(self.blinding, types.ClassType):
            raise CryptoError('Tried to add something to the container that was not a class!')

    def __str__(self):
        include = []
        if self.signing:
            include.append(self.signing.ALGNAME)
        if self.blinding:
            include.append(self.blinding.ALGNAME)
        if self.hashing:
            include.append(self.hashing.ALGNAME)

        # the order is always SIGN-ALG, BLINDING-ALG, HASH-ALG

        return '[' + ', '.join(include) + ']'

    def __eq__(self, other):
        if not isinstance(other, CryptoContainer):
            raise NotImplementedError
        return self.signing.ALGNAME == other.signing.ALGNAME and \
               self.hashing.ALGNAME == other.hashing.ALGNAME and \
               self.blinding.ALGNAME == other.blinding.ALGNAME
        

def decodeCryptoContainer(container):
    # raise NotImplementedError, str(container)
    return CryptoContainer(signing=RSASigningAlgorithm,
                           blinding=RSABlindingAlgorithm,
                           hashing=SHA256HashingAlgorithm)

def encodeCryptoContainer(container):
    include = []
    if container.signing:
        include.append(container.signing.ALGNAME)
    if container.blinding:
        include.append(container.blinding.ALGNAME)
    if container.hashing:
        include.append(container.hashing.ALGNAME)

    return include
    
class SigningAlgorithm:
    def __init__(self, key):
        self.key = key

    def sign(self, message):
        """returns the signature of the hash of the data."""
        raise NotImplementedError

    def verify(self, message):
        """returns if the signature inputted is valid."""
        raise NotImplementedError

    def __str__(self):
        """returns only the name of the signing algorithm in accordance with the SIGN-ALG name."""
        return self.ALGNAME

class BlindingAlgorithm:
    def __init__(self, key):
        self.key = key

    def blind(self, message, blinding_factor):
        """returns the blinded value of the message."""
        raise NotImplementedError

    def unblind(self, message, blinding_factor):
        """returns the unblinded value of the message."""

    def __str__(self):
        """returns only the name of the blinding function in accordance with the HASH-ALG name."""
        return self.ALGNAME


class EncryptionAlgorithm:
    def __init__(self, key):
        self.key = key

    def encrypt(self, message):
        """returns the encryption of the plaintext."""
        raise NotImplementedError

    def decrypt(self, message):
        """returns the decryption of the ciphertext."""
        raise NotImplementedError
    
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
        raise NotImplementedError

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
    r"""An instance of the KeyPair which does RSA. It builds from the pycrypto RSA.

    First, create a public key and private key copy with known values.
    (p=61, q=53, n=pq=3233, e=17, d=2753)

    >>> simple_public_key = RSAKeyPair(n=3233L, e=17L)

    >>> simple_private_key = RSAKeyPair(n=3233L, e=17L, d=2753L)

    >>> simple_public_key.hasPrivate()
    False
    
    >>> simple_public_key.public()
    <Crypto.PublicKey.RSA.RSAobj... instance at 0x...>
    
    >>> simple_public_key.private()
    Traceback (most recent call last):
    CryptoError: Do not have private key

    >>> simple_public_key.size()
    11

    Print out the base64 value of the public key (n and e)
    >>> print simple_public_key
    DKE=,EQ==

    stringPrivate should return an empty string for a public key
    >>> simple_public_key.stringPrivate()
    ''

    >>> simple_public_key.toJson()
    '{"public":"DKE=,EQ==",\\n"private":""}'


    Now, compare the public key and private key together knowing the internals of the key
    >>> simple_public_key.key.n == simple_private_key.key.n
    True

    >>> simple_public_key.key.e == simple_private_key.key.e
    True

    Test the newPublicKeyPair function against simple_public_key
    >>> new_public_key = simple_public_key.newPublicKeyPair()
    >>> new_public_key.key.n == simple_public_key.key.n
    True
    >>> new_public_key.key.e == simple_public_key.key.e
    True

    Check to make sure we don't have the private key
    >>> new_public_key.hasPrivate()
    False

    Check the private key values. pycrypto's RSA only requires n, e, and d.
    >>> simple_private_key.key.n
    3233L
    >>> simple_private_key.key.e
    17L
    >>> simple_private_key.key.d
    2753L

    >>> print simple_private_key
    DKE=,EQ==

    >>> simple_private_key.stringPrivate()
    'CsE=,PQ==,NQ=='

    >>> simple_private_key.toJson()
    '{"public":"DKE=,EQ==",\\n"private":"CsE=,PQ==,NQ=="}'


    Test the other generation methods for private keys
    >>> key_2 = RSAKeyPair(n=3233L, e=17L, d=2753L, p=61L, q=53L)
    >>> key_3 = RSAKeyPair(n=3233L, e=17L, d=2753L, p=61L, q=53L, u=20L)
    >>> key_4 = RSAKeyPair(key=key_3.key)
    >>> key_5 = RSAKeyPair(key=simple_private_key.key)
   
    >>> simple_private_key.key.n == key_2.key.n == key_3.key.n == key_4.key.n
    True

    >>> simple_private_key.key.d == key_2.key.d == key_3.key.d == key_4.key.d
    True

    >>> simple_private_key.key.e == key_2.key.e == key_3.key.e == key_4.key.e
    True

    Test p, q, and u. When pycrypto makes the key, if we supply a p and q, u is created
    automatically.
    >>> key_2.key.p == key_3.key.p == key_4.key.p
    True
    >>> key_2.key.q == key_3.key.q == key_4.key.q
    True
    >>> key_2.key.u == key_3.key.u == key_4.key.u
    True
    
    """ 
    def __init__(self, key=None, p=None, q=None, e=None, d=None, n=None, u=None):
        self.key = key

        if not key: # we weren't passed in a key. Have to figure it out ourselves. yay!
            #this function builds just the parts of the tuple contstruct uses
            li = [n, e]
            if d:
                li.append(d)
            if p and q:
                li.extend((p, q))
            if u:
                li.append(u)
                
            from Crypto.PublicKey import RSA
            self.key = RSA.construct(tuple(li))


    def hasPrivate(self):
        return self.key.has_private()

    def public(self):
        return self.key.publickey()

    def private(self):
        if not self.hasPrivate():
            raise CryptoError('Do not have private key')

        return self.key

    def keytype(self):
        def encode(key):
            return str(key)
        def decode(key):
            import base64
            l = key.split(',')
            try:
                n = base64.b64decode(l[0])
            except TypeError:
                raise TypeError(l[0])
            e = base64.b64decode(l[1])
            return RSAKeyPair(n=n, e=e)
        class RSAKeyType:
            pass
        RSAKeyType.encode = encode
        RSAKeyType.decode = decode


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
   
    def toPython(self):
        return str(self) 

    def toJson(self):
        import json
        return json.write(dict(public=str(self),private=self.stringPrivate()))

    def key_id(self, digestAlgorithm):
        return digestAlgorithm().update(str(self)).digest()

    def newPublicKeyPair(self):
        return RSAKeyPair(self.key.publickey())

    def __eq__(self,other):
        return self.key == other.key

def decodeRSAKeyPair(key):
    import base64

    l = key.split(',')
    n = number.bytes_to_long(base64.b64decode(l[0]))
    e = number.bytes_to_long(base64.b64decode(l[1]))
    return RSAKeyPair(n=n, e=e)

def createRSAKeyPair(N):
    """Creates an RSA keypair of size N."""
    from Crypto.PublicKey import RSA

    _r.verifyEntropy(N)
    rsaKey = RSA.generate(N, _r.get_bytes)
    return RSAKeyPair(key=rsaKey)


class RSAEncryptionAlgorithm(EncryptionAlgorithm):
    r"""Performs RSA encryption
    >>> private = RSAKeyPair(n=3233L, e=17L, d=2753L, p=61L, q=53L)
    >>> public = private.newPublicKeyPair()

    >>> public.hasPrivate()
    False

    >>> priv_enc = RSAEncryptionAlgorithm(private)
    >>> pub_enc = RSAEncryptionAlgorithm(public)

    >>> print priv_enc
    RSAEncryptionAlgorithm
    >>> print pub_enc
    RSAEncryptionAlgorithm

    >>> pub_enc.encrypt(14L)
    2549L

    >>> priv_enc.decrypt(2549L)
    14L

    >>> pub_enc.decrypt(2549L)
    Traceback (most recent call last):
    ...
    CryptoError: Do not have private key

    >>> pub_enc.encrypt('0')
    '\x02p'

    >>> priv_enc.decrypt('\x02p')
    '0'
    """
    from Crypto.PublicKey import RSA

    ALGNAME = 'RSAEncryptionAlgorithm'

    def __init__(self, key):
        if not isinstance(key, RSAKeyPair):
            raise CryptoError('key not RSAKeyPair type!. key.__class__: %s' % key.__class__)
        
        EncryptionAlgorithm.__init__(self, key)
        
    def encrypt(self, message):
        try:
            return self.key.public().encrypt(message, '')[0]
        except PyCryptoRSAError, reason:
            raise CryptoError(reason)
    
    def decrypt(self, message):
        try:
            return self.key.private().decrypt(message)
        except PyCryptoRSAError, reason:
            raise CryptoError(reason)
        

class RSABlindingAlgorithm(BlindingAlgorithm):
    r"""Performs RSA blinding
    >>> private = RSAKeyPair(n=3233L, e=17L)

    >>> blind = RSABlindingAlgorithm(private)

    >>> print blind
    RSABlindingAlgorithm

    Test a blinding. This does not work for some reason. The answer is almost certainly wrong as well.
    >>> blinded, factor = blind.blind(154L, 1001L)

    >>> blinded
    '\tC'

    >>> factor == 1001L
    True

    >>> blind.unblind(blinded, factor)
    '\x0bw'

    >>> blinded, factor = blind.blind('\x9a', '\x03\xe9')

    >>> blinded
    '\tC'
    
    >>> blind.unblind(blinded)
    '\x0bw'
    """

    ALGNAME = 'RSABlindingAlgorithm'

    def __init__(self, key, blinding_factor=None):
        BlindingAlgorithm.__init__(self, key)
        self.blinding_factor = blinding_factor

    def blind(self, message, blinding_factor=None):
        """returns the blinding of the input with the key and the blinding factor."""
        if blinding_factor:
            self.blinding_factor = blinding_factor
            
        elif not self.blinding_factor:
            # self.key.size returns the size of the key - 1, which is acceptable
            self.blinding_factor = _r.getRandomNumber(self.key.size())

        else:
            pass #self.blinding_factor is already set

        if isinstance(message, types.LongType):
            message = number.long_to_bytes(message)

        try:
            return self.key.public().blind(message, self.blinding_factor), self.blinding_factor
        except PyCryptoRSAError, reason:
            raise CryptoError(reason)

    def unblind(self, message, blinding_factor=None):
        """returns the unblinded value of the input."""
        if blinding_factor:
            self.blinding_factor = blinding_factor

        # change the input to a bytestream if a long number
        if isinstance(message, types.LongType):
            message = number.long_to_bytes(message)

        try:
            return self.key.public().unblind(message, self.blinding_factor)
        except PyCryptoRSAError, reason:
            raise CryptoError(reason)
        

    
class RSASigningAlgorithm(SigningAlgorithm):
    """An implementation of the RSA signing algorithm.
    >>> private = createRSAKeyPair(1024)
    >>> public = private.newPublicKeyPair()

    >>> public.hasPrivate()
    False

    >>> message = _r.getRandomString(1022)
    
    >>> signer = RSASigningAlgorithm(private)
    >>> verifier = RSASigningAlgorithm(public)

    >>> print signer
    RSASigningAlgorithm
    >>> print verifier
    RSASigningAlgorithm

    >>> signature = signer.sign(message)

    >>> verifier.verify(message, signature)
    True

    If the signature is missing the first byte, it cannot pass
    >>> signature = signature[1:] 

    >>> verifier.verify(message, signature)
    False

    >>> message = _r.getRandomString(1025)

    >>> signer.sign(message)
    Traceback (most recent call last):
      ...
    CryptoError: Ciphertext too large

    >>> verifier.verify(message, signature)
    False
    """

    ALGNAME = 'RSASigningAlgorithm'

    def __init__(self, key):
        SigningAlgorithm.__init__(self, key)

    def sign(self, message):
        """returns the signature of the message with the key."""
        try:
            key = self.key.private()
            result = key.sign(message, '')[0]

            # if the message was a bytestream, return a bytestream
            if isinstance(message, types.StringType):
                return number.long_to_bytes(result)

            return result
        except PyCryptoRSAError, reason:
            raise CryptoError(reason)

    def verify(self, message, signature):
        """returns if the signature of the input is valid."""
        try:
            return self.key.public().verify(message, (number.bytes_to_long(signature),))
        except PyCryptoRSAError, reason:
            raise CryptoError(reason)

class SHA256HashingAlgorithm(HashingAlgorithm):

    ALGNAME='SHA256HashingAlgorithm'

    def __init__(self, input=None):
        self.reset() # setup self.hash. We reset empty since HashingAlgorithm.__init__ will update!

        HashingAlgorithm.__init__(self, input)

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

# We need a copy of the error from Crypto.PublicKey.RSA, so import, make a copy, and delete the module
import Crypto.PublicKey.RSA as quickRSA
PyCryptoRSAError = quickRSA.error
del quickRSA

if __name__=='__main__':
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
