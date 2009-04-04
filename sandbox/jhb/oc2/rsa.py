"""RSA module

!!! This is just a playground, for understanding some bits and pieces,
this is not at all serious crypto production code!!!



Module for calculating large primes, and RSA encryption, decryption,
signing and verification. Includes generating public and private keys.
"""

__author__ = "Sybren Stuvel, Marloes de Boer and Ivo Tamboer"
__date__ = "2004-11-17"

# NOTE: Python's modulo can return negative numbers. We compensate for
# this behaviour using the abs() function

import math
import sys
import random    # For picking semi-random numbers
import types

# Get os.urandom PRNG
import os
try:
    raise Exception
    os.urandom(1)
    def getRandomBytes(howMany):
        return stringToBytes(os.urandom(howMany))
    grbname = 'urandom'        
except:

    def getRandomBytes(howMany):
        bits = howMany * 8
        number = random.getrandbits(bits)
        return numberToBytes(number)
        pass
    grbname = 'randint'        

def log(x, base = 10):
    return math.log(x) / math.log(base)

def gcd(a,b):
    a, b = max(a,b), min(a,b)
    while b:
        a, b = b, a % b
    return a

def bytes2int(bytes):
    """Converts a list of bytes or a string to an integer

    >>> (128*256 + 64)*256 + + 15
    8405007
    >>> l = [128, 64, 15]
    >>> bytes2int(l)
    8405007
    """

    #if not (type(bytes) is types.ListType or type(bytes) is types.StringType):
    #    raise TypeError("You must pass a string or a list")

    # Convert byte stream to integer
    integer = 0
    for byte in bytes:
        integer *= 256
        if type(byte) is types.StringType: byte = ord(byte)
        integer += byte

    return integer

def int2bytes(number):
    """Converts a number to a string of bytes
    
    >>> bytes2int(int2bytes(123456789))
    123456789
    """

    if not (type(number) is types.LongType or type(number) is types.IntType):
        raise TypeError("You must pass a long or an int")

    string = ""

    while number > 0:
        string = "%s%s" % (chr(number & 0xFF), string)
        number /= 256
    
    return string



def ceil(x):
    """Returns int(math.ceil(x))"""

    return int(math.ceil(x))


def encrypt_int(message, ekey, n):
    """Encrypts a message using encryption key 'ekey', working modulo
    n"""

    if type(message) is types.IntType:
        message = long(message)
    elif type(message) is types.LongType:
        pass
    elif type(message) is types.StringType:
        message = long(bytes2int(message))
    
    if not type(message) is types.LongType:
        raise TypeError("You must pass a long or an int, not %s" % type(message))
    
    return pow(message, ekey, n)

def decrypt_int(cyphertext, dkey, n):
    """Decrypts a cypher text using the decryption key 'dkey', working
    modulo n"""

    return encrypt_int(cyphertext, dkey, n)

def sign_int(message, dkey, n):
    """Signs 'message' using key 'dkey', working modulo n"""

    return decrypt_int(message, dkey, n)

def verify_int(signed, ekey, n):
    """verifies 'signed' using key 'ekey', working modulo n"""

    return encrypt_int(signed, ekey, n)

def blinding_int(m,secret,n):
    return (m * secret) % n


def encrypt(message, key):
    """Encrypts a string 'message' with the public key 'key'"""
    
    #return chopstring(message, key['e'], key['n'], encrypt_int)
    return encrypt_int(message,key['e'],key['n'])
def sign(message, key):
    """Signs a string 'message' with the private key 'key'"""
      
    #return chopstring(message, key['d'], key['p']*key['q'], decrypt_int)
    return decrypt_int(message,key['d'],key['n'])

def decrypt(cypher, key):
    """Decrypts a cypher with the private key 'key'"""

    #return gluechops(cypher, key['d'], key['p']*key['q'], decrypt_int)
    return decrypt_int(cypher,key['d'],key['n'])

def verify(cypher, key):
    """Verifies a cypher with the public key 'key'"""

    #return gluechops(cypher, key['e'], key['n'], encrypt_int)
    return encrypt_int(cypher,key['e'],key['n'])

def blind(message,secret,key):
    #return chopstring(message,secret,key['n'],blinding_int)
    return blinding_int(message,secret,key['n'])

def unblind(message,secret,key):
    #return gluechops(message,secret,key['n'],blinding_int)
    return blinding_int(message,secret,key['n'])


#import math

def bits(integer): #Gets number of bits in integer
   result = 0
   while integer:
      integer >>= 1
      result += 1
   return result


def invMod(a, b):
    c, d = a, b
    uc, ud = 1, 0
    while c != 0:
        #This will break when python division changes, but we can't use //
        #cause of Jython
        q = d / c
        c, d = d-(q*c), c
        uc, ud = ud - (q * uc), uc
    if d == 1:
        return ud % b
    return 0

def powMod(base, power, modulus):
    nBitScan = 5

    """ Return base**power mod modulus, using multi bit scanning
    with nBitScan bits at a time."""

    #TREV - Added support for negative exponents
    negativeResult = False
    if (power < 0):
        power *= -1
        negativeResult = True

    exp2 = 2**nBitScan
    mask = exp2 - 1

    # Break power into a list of digits of nBitScan bits.
    # The list is recursive so easy to read in reverse direction.
    nibbles = None
    while power:
        nibbles = int(power & mask), nibbles
        power = power >> nBitScan

    # Make a table of powers of base up to 2**nBitScan - 1
    lowPowers = [1]
    for i in xrange(1, exp2):
        lowPowers.append((lowPowers[i-1] * base) % modulus)

    # To exponentiate by the first nibble, look it up in the table
    nib, nibbles = nibbles
    prod = lowPowers[nib]

    # For the rest, square nBitScan times, then multiply by
    # base^nibble
    while nibbles:
        nib, nibbles = nibbles
        for i in xrange(nBitScan):
            prod = (prod * prod) % modulus
        if nib: prod = (prod * lowPowers[nib]) % modulus

    #TREV - Added support for negative exponents
    if negativeResult:
        prodInv = invMod(prod, modulus)
        #Check to make sure the inverse is correct
        if (prod * prodInv) % modulus != 1:
            raise AssertionError()
        return prodInv
    return prod


def getUnblinder(n):
    while 1:
        r = getRandomNumber(0,n) 
        if  gcd(r, n) == 1: #relative prime
            break
    return r            


def generate(bits):  #needed
    #return (dummypub,dummypriv)
    p = getRandomPrime(bits/2, False)
    q = getRandomPrime(bits/2, False)
    t = (p-1)*(q-1)
    n = p * q
    
    while 1:
        e = getRandomNumber(17,t-1)  #getRandomNumber, ungerade < (p-1)*(q-1), coprime(e,(p-1)*(q-1)), e.g. gcd == 1
        e = e % 2 == 0 and e-1 or e    
        if  gcd(e,t) == 1:
            break            
    d = invMod(e, t)
    keys =  ( {'e': e, 'n': n}, {'d': d, 'n': n} )
    return keys

gen_pubpriv_keys = generate

def getRandomPrime(bits, display=False): 
    if bits < 10:
        raise AssertionError()
    #The 1.5 ensures the 2 MSBs are set
    #Thus, when used for p,q in RSA, n will have its MSB set
    #
    #Since 30 is lcm(2,3,5), we'll set our test numbers to
    #29 % 30 and keep them there
    low = (2L ** (bits-1)) * 3/2
    high = 2L ** bits - 30
    p = getRandomNumber(low, high)
    p += 29 - (p % 30)
    while 1:
        if display: print ".",
        p += 30
        if p >= high:
            p = getRandomNumber(low, high)
            p += 29 - (p % 30)
        if isPrime(p, display=display):
            return p

#Pre-calculate a sieve of the ~100 primes < 1000:
def makeSieve(n):
    sieve = range(n)
    for count in range(2, int(math.sqrt(n))):
        if sieve[count] == 0:
            continue
        x = sieve[count] * 2
        while x < len(sieve):
            sieve[x] = 0
            x += sieve[count]
    sieve = [x for x in sieve[2:] if x]
    return sieve

sieve = makeSieve(1000)

def isPrime(n, iterations=5, display=False):
    #Trial division with sieve
    for x in sieve:
        if x >= n: return True
        if n % x == 0: return False
    #Passed trial division, proceed to Rabin-Miller
    #Rabin-Miller implemented per Ferguson & Schneier
    #Compute s, t for Rabin-Miller
    if display: print "*",
    s, t = n-1, 0
    while s % 2 == 0:
        s, t = s/2, t+1
    #Repeat Rabin-Miller x times
    a = 2 #Use 2 as a base for first iteration speedup, per HAC
    for count in range(iterations):
        v = powMod(a, s, n)
        if v==1:
            continue
        i = 0
        while v != n-1:
            if i == t-1:
                return False
            else:
                v, i = powMod(v, 2, n), i+1
        a = getRandomNumber(2, n)
    return True

def lcm(a, b):
    #This will break when python division changes, but we can't use // cause
    #of Jython
    return (a * b) / gcd(a, b)

def getRandomNumber(low, high):
    if low >= high:
        raise AssertionError()
    howManyBits = numBits(high)
    howManyBytes = numBytes(high)
    lastBits = howManyBits % 8
    while 1:
        bytes = getRandomBytes(howManyBytes)
        if lastBits:
            bytes[0] = bytes[0] % (1 << lastBits)
        n = bytesToNumber(bytes)
        if n >= low and n < high:
            return n



def numberToBytes(n):
    howManyBytes = numBytes(n)
    bytes = createByteArrayZeros(howManyBytes)
    for count in range(howManyBytes-1, -1, -1):
        bytes[count] = int(n % 256)
        n >>= 8
    return bytes

def stringToBytes(s):
    bytes = createByteArrayZeros(0)
    bytes.fromstring(s)
    return bytes   


import array
def createByteArraySequence(seq):
    return array.array('B', seq)
def createByteArrayZeros(howMany):
    return array.array('B', [0] * howMany)
    
def bytesToNumber(bytes):
    total = 0L
    multiplier = 1L
    for count in range(len(bytes)-1, -1, -1):
        byte = bytes[count]
        total += multiplier * byte
        multiplier *= 256
    return total

import math
def numBits(n):
    if n==0:
        return 0
    s = "%x" % n
    return ((len(s)-1)*4) + \
    {'0':0, '1':1, '2':2, '3':2,
     '4':3, '5':3, '6':3, '7':3,
     '8':4, '9':4, 'a':4, 'b':4,
     'c':4, 'd':4, 'e':4, 'f':4,
     }[s[0]]
    return int(math.floor(math.log(n, 2))+1)

def numBytes(n):
    if n==0:
        return 0
    bits = numBits(n)
    return int(math.ceil(bits / 8.0))


fast_exponentiation = pow



dummypub = {
'e': 59343568823711559206614914329434374961303042335788099534897501357955675804133L, 
'n': 32793647770017443581051908007908006621376604150499221366839445678176407494654130256572721798731647281073382247358431120858829497973290288823842062554766872356043862368004460824686561544242774370448685624290963022007959843337482265073763255429596031300239158232169931316001844162136279539357507455710562227577L
}

dummypriv = {
'q': 3660876769483489857077409618418989781902917148342703560038011826242773069902176126219730148875372119227365538620396693688963051979724315365417720940740849L, 
'p': 8957867154497055858370988090953024497950216741166048812169220114248696092230327733254526217831517389137130597830562133311139440841609128753512364848094473L, 
'd': 12619589565384678078150569778102981741046267149118420445896125941979396328586657133712760591528167393457329828435758755256948329844592838106750783634900284025380032774546264335257012829516042607077111098646252442031819834114954318384114125879377117610343879752299012777002244350133926279173002674800640331117L}



# Do doctest if we're not imported
if __name__ == "__main__":
    import time
    t = time.time()
    (pub,priv) =  gen_pubpriv_keys(1024)
    print '=' * 40
    times = []
    #blinding
    #message = 'f'*65
    message = 'c3ab8ff13720e8ad9047dd39466b3c8974e592c2fa383d4a3960714caef0c4f2'
    #print 'cleartext ', message
    unblinder = getUnblinder(pub['n'])
    blinder = pow(invMod(unblinder, pub['n']), pub['e'],pub['n'])
    times.append(time.time() - t)
    t = time.time()
    
    blinded = blind(message,blinder,pub)
    times.append(time.time() - t)
    t = time.time()
    
    signedblind = encrypt_int(blinded, priv['d'], priv['p']*priv['q'])
    times.append(time.time() - t)
    t = time.time()
    
    unblinded = (signedblind * unblinder) % pub['n']
    times.append(time.time() - t)
    t = time.time()
    
    print 'verifyied', message == verify(unblinded,pub)
    times.append(time.time() - t)
    print sum(times) - times[2]

    if 1:
        #full
        t = time.time()
        message = 'serial '*5
        print 'cleartext ', message
        cypher = encrypt(message,pub)
        print 'cyphertext: ',cypher
        print 'decrypted', decrypt(cypher,priv)
        decrypt(cypher,priv)
        signed = sign(message,priv)
        print 'signed', signed
        print 'verified', message == verify(signed,pub)
        unblinder = getUnblinder(pub['n'])
        blinder = pow(invMod(unblinder, pub['n']), pub['e'],pub['n'])
        blinded = blind(message,blinder,pub)
        print 'blinded', blinded
        signedblind = sign(blinded,priv)
        signedblind = encrypt_int(blinded, priv['d'], priv['p']*priv['q'])
        print 'signedblind', signedblind
        unblinded = unblind(signedblind,unblinder,pub)
        unblinded = (signedblind * unblinder) % pub['n']
        print 'unblinded', unblinded
        print 'verified', message == verify(unblinded,pub)
        print time.time() - t
        
        
        print '=' * 40
        #no blinding
        t = time.time()
        message = 'serial '*5
        #print 'cleartext ', message
        cypher = encrypt(message,pub)
        #print 'cyphertext: ',cypher
        #print 'decrypted', decrypt(cypher,priv)
        decrypt(cypher,priv)
        signed = sign(message,priv)
        #print 'signed', signed
        #print 'verified', message == verify(signed,pub)
        print time.time() - t 

      

        
__all__ = ["gen_pubpriv_keys", "encrypt", "decrypt", "sign", "verify"]

