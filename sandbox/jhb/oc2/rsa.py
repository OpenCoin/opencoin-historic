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

RANDOM_DEV="/dev/urandom"
testing = False
has_broken_randint = False

try:
    #random.randint(1, 10000000000000000000000000L)
    1+1
    pass
except:
    has_broken_randint = True
    print "This system's random.randint() can't handle large numbers"
    print "Random integers will all be read from %s" % RANDOM_DEV


def log(x, base = 10):
    return math.log(x) / math.log(base)

def gcd(a,b):
    a, b = max(a,b), min(a,b)
    while b:
        a, b = b, a % b
    return a

def gcd_old(p, q):
    """Returns the greatest common divisor of p and q


    >>> gcd(42, 6)
    6
    """
    if p<q: return gcd(q, p)
    if q == 0: return p
    return gcd(q, abs(p%q))

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


def read_random_int(nbits):
    """Reads a random integer from RANDOM_DEV of approximately nbits
    bits rounded up to whole bytes"""
    #print nbits    
    nbytes  = ceil(nbits/8)
    
    bytes = []
    for i in range(nbytes):
        bytes.append(random.randint(0,255))        
    return bytes2int(bytes)

    if len(randomdata) != nbytes:
        raise Exception("Unable to read enough random bytes")

    return bytes2int(randomdata)

def ceil(x):
    """Returns int(math.ceil(x))"""

    return int(math.ceil(x))
    
def randint(minvalue, maxvalue):
    """Returns a random integer x with minvalue <= x <= maxvalue"""
    # Safety - get a lot of random data even if the range is fairly
    # small
    min_nbits  = 32

    # The range of the random numbers we need to generate
    range      = maxvalue - minvalue

    # Which is this number of bytes
    rangebytes = ceil(log(range, 2) / 8)

    # Convert to bits, but make sure it's always at least min_nbits*2
    rangebits  = max(rangebytes * 8, min_nbits * 2)
    
    # Take a random number of bits between min_nbits and rangebits
    nbits      = random.randint(min_nbits, rangebits)
    
    return (read_random_int(nbits) % range) + minvalue

def fermat_little_theorem(p):
    """Returns 1 if p may be prime, and something else if p definitely
    is not prime"""

    a = randint(1, p-1)
    return fast_exponentiation(a, p-1, p)

def jacobi(a, b):
    """Calculates the value of the Jacobi symbol (a/b)
    """

    if a == 0: return 0
    if a == 1: return 1

    if a % 2 == 0:
        if (b**2-1)/8 % 2 == 0:
            return jacobi(a/2, b)
        return -jacobi(a/2, b)
    
    if (a-1) * (b-1) / 4 % 2 == 0:
        return jacobi(b % a, a)

    return -jacobi(b % a, a)

def jacobi_witness(x, n):
    """Returns False if n is an Euler pseudo-prime with base x, and
    True otherwise.
    """

    j = jacobi(x, n) % n
    f = fast_exponentiation(x, (n-1)/2, n)

    if j == f: return False
    return True

def randomized_primality_testing(n, k):
    """Calculates whether n is composite (which is always correct) or
    prime (which is incorrect with error probability 2**-k)

    Returns False if the number if composite, and True if it's
    probably prime.
    """

    q = 0.5        # Property of the jacobi_witness function

    # t = int(math.ceil(k / log(1/q, 2)))
    t = ceil(k / log(1/q, 2))
    for i in range(t+1):
        x = randint(1, n-1)
        if jacobi_witness(x, n): return False
    
    return True

def is_prime(number):
    """Returns True if the number is prime, and False otherwise.

    >>> is_prime(42)
    0
    >>> is_prime(41)
    1
    """

    """
    if not fermat_little_theorem(number) == 1:
        # Not prime, according to Fermat's little theorem
        return False
    """

    if randomized_primality_testing(number, 5):
        # Prime, according to Jacobi
        return True
    
    # Not prime
    return False

    
def getprime(nbits):
    """Returns a prime number of max. 'math.ceil(nbits/8)*8' bits. In
    other words: nbits is rounded up to whole bytes.

    >>> p = getprime(8)
    >>> is_prime(p-1)
    0
    >>> is_prime(p)
    1
    >>> is_prime(p+1)
    0
    """

    nbytes  = int(math.ceil(nbits/8))

    while True:
        integer = read_random_int(nbits)

        # Make sure it's odd
        integer |= 1

        # Test for primeness
        if is_prime(integer): break

        # Retry if not prime

    return integer

def are_relatively_prime(a, b):
    """Returns True if a and b are relatively prime, and False if they
    are not.

    >>> are_relatively_prime(2, 3)
    1
    >>> are_relatively_prime(2, 4)
    0
    """

    d = gcd(a, b)
    return (d == 1)

def find_p_q(nbits):
    """Returns a tuple of two different primes of nbits bits"""

    print 'finding p'
    p = getprime(nbits)
    while True:
        print 'finding q'
        q = getprime(nbits)
        if not q == p: break
    
    return (p, q)

def extended_euclid_gcd(a, b):
    """Returns a tuple (d, i, j) such that d = gcd(a, b) = ia + jb
    """

    if b == 0:
        return (a, 1, 0)

    q = abs(a % b)
    r = long(a / b)
    (d, k, l) = extended_euclid_gcd(b, q)

    return (d, l, k - l*r)

# Main function: calculate encryption and decryption keys
def calculate_keys(p, q, nbits):
    """Calculates an encryption and a decryption key for p and q, and
    returns them as a tuple (e, d)"""

    n     = p * q
    phi_n = (p-1) * (q-1)

    while True:
        print 'c'
        # Make sure e has enough bits so we ensure "wrapping" through
        # modulo n
        e = getprime(max(8, nbits/2))
        if are_relatively_prime(e, n) and are_relatively_prime(e, phi_n): break

    (d, i, j) = extended_euclid_gcd(e, phi_n)

    if not d == 1:
        raise Exception("e (%d) and phi_n (%d) are not relatively prime" % (e, phi_n))

    if not (e * i) % phi_n == 1:
        raise Exception("e (%d) and i (%d) are not mult. inv. modulo phi_n (%d)" % (e, i, phi_n))

    return (e, i)


def gen_keys(nbits):
    """Generate RSA keys of nbits bits. Returns (p, q, e, d).
    """

    while True:
        print 'find'
        (p, q) = find_p_q(nbits)
        print 'calculate'
        (e, d) = calculate_keys(p, q, nbits)

        # For some reason, d is sometimes negative. We don't know how
        # to fix it (yet), so we keep trying until everything is shiny
        if d > 0: break

    return (p, q, e, d)

def encrypt_int(message, ekey, n):
    """Encrypts a message using encryption key 'ekey', working modulo
    n"""

    if type(message) is types.IntType:
        return encrypt_int(long(message), ekey, n)

    if not type(message) is types.LongType:
        raise TypeError("You must pass a long or an int")

    #if math.floor(log(message, 2)) > math.floor(log(n, 2)):
    #    raise OverflowError("The message is too long")

    return fast_exponentiation(message, ekey, n)

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

def chopstring(message, key, n, funcref):
    """Splits 'message' into chops that are at most as long as n,
    converts these into integers, and calls funcref(integer, key, n)
    for each chop.

    Used by 'encrypt' and 'sign'.
    """

    msglen = len(message)
    mbits  = msglen * 8
    #nbits  = int(math.floor(log(n, 2)))
    nbits = 1024
    nbytes = nbits / 8
    blocks = msglen / nbytes

    if msglen % nbytes > 0:
        blocks += 1

    cypher = []
    
    for bindex in range(blocks):
        offset = bindex * nbytes
        block  = message[offset:offset+nbytes]
        value  = bytes2int(block)
        cypher.append(funcref(value, key, n))

    return cypher[0]

def gluechops(chops, key, n, funcref):
    """Glues chops back together into a string.  calls
    funcref(integer, key, n) for each chop.

    Used by 'decrypt' and 'verify'.
    """
    message = ""
    chops = [chops]
    
    for cpart in chops:
        mpart = funcref(cpart, key, n)
        message += int2bytes(mpart)
    
    return message

def encrypt(message, key):
    """Encrypts a string 'message' with the public key 'key'"""
    
    return chopstring(message, key['e'], key['n'], encrypt_int)

def sign(message, key):
    """Signs a string 'message' with the private key 'key'"""
    
    return chopstring(message, key['d'], key['p']*key['q'], decrypt_int)

def decrypt(cypher, key):
    """Decrypts a cypher with the private key 'key'"""

    return gluechops(cypher, key['d'], key['p']*key['q'], decrypt_int)

def verify(cypher, key):
    """Verifies a cypher with the public key 'key'"""

    return gluechops(cypher, key['e'], key['n'], encrypt_int)

def blind(message,secret,key):
    return chopstring(message,secret,key['n'],blinding_int)

def unblind(message,secret,key):
    return gluechops(message,secret,key['n'],blinding_int)


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
        r = randint(0,n) 
        if  are_relatively_prime(r,n):
            break
    return r            

def gen_pubpriv_keys_old(nbits):
    """Generates public and private keys, and returns them as (pub,
    priv).

    The public key consists of a dict {e: ..., , n: ....). The private
    key consists of a dict {d: ...., p: ...., q: ....).
    """
    #return (dummypub,dummypriv) 
    (p, q, e, d) = gen_keys(nbits)

    return ( {'e': e, 'n': p*q}, {'d': d, 'p': p, 'q': q} )



def generate(bits):
    p = getRandomPrime(bits/2, False)
    q = getRandomPrime(bits/2, False)
    t = lcm(p-1, q-1)
    n = p * q
    e = 3L  #Needed to be long, for Java
    d = invMod(e, t)
    p = p
    q = q
    #dP = key.d % (p-1)
    #dQ = key.d % (q-1)
    #qInv = invMod(q, p)
    return ( {'e': e, 'n': n}, {'d': d, 'p': p, 'q': q} )

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
    p = randint(low, high)
    p += 29 - (p % 30)
    while 1:
        if display: print ".",
        p += 30
        if p >= high:
            p = randint(low, high)
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
        a = randint(2, n)
    return True

def lcm(a, b):
    #This will break when python division changes, but we can't use // cause
    #of Jython
    return (a * b) / gcd(a, b)




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
    if 1:
        import time
        (pub,priv) =  gen_pubpriv_keys(1024)
        if 1:
            pass   
        if 0:                    
            (pub,priv) = ({'e': 3197601411731116245564574341873883965700807663084732800379376818822337768214254275271880556652543127861042149268538435129289119875433847550131501030387489L, 'n': 10010369815382334240798530070718437854966721919010883362239947723044651469296597049454697875962523892167961291050690952736009970933207150773523631818070845272169487515533531012017986671583117870935704791444203091193928433685036216475710517809854134259468721246954372989146266743601614235731605829521314456547427727170490340220674730134652649494795255568521600458207445549064461533102227417295842548674337715761362209701734789853469920681184060067484771558465649908138716260602630770402224385695023184536234858539880642604697788322269392260439339765412460944589951571879796455505538134420317166479947358156062601693631L}, {'q': 71965600310892660429596898829670710653460148180418095123381449844052583795523012040229068564004895983101524115981347946055591335247903874583493068435665706247560257067715751690858970054084093796406191757154228889454862489531588573733962647071944624542539072044760521321849853532919544810806179365743581833777L, 'p': 139099372090795607726534110588106724714748422622835743921578772078079056922772905042826722454890797681407412421239584468016215098928247799729322355221381502409668675456356288320338371140589835466925402699800592201081119770108520423450701555386146286042071274331899104700802281153510654832285005494641183409903L, 'd': 2303141903135405741196770316647349478451046851656460345238126953851335354457956582261071364112927329063172609648667594153989314522741915259780604774082900187421379799944807777478001765690017634728386784574675440128718738783220812396390380020488828055736972630556491383856716073773079586029351343732817861978611326631064317705218919924700761528865528832464733884127079042865050020476303293874373222849912706661252250304706695160160822827622086731394008802874568358702895903468129589361385276702313798198182238681153517515581052056557552995405472004415453043300567819425403784410663519000867938462388941313183838315329L})                    
        if 0:
            #full
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
            unblinder = getUnblinder(pub['n'])
            blinder = pow(invMod(unblinder, pub['n']), pub['e'],pub['n'])
            blinded = blind(message,blinder,pub)
            #print 'blinded', blinded
            #signedblind = sign(blinded,priv)
            signedblind = encrypt_int(blinded, priv['d'], priv['p']*priv['q'])
            #print 'signedblind', signedblind
            #unblinded = unblind(signedblind,unblinder,pub)
            unblinded = (signedblind * unblinder) % pub['n']
            #print 'unblinded', unblinded
            #print 'verified', message == verify(unblinded,pub)
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

      
        print '=' * 40
        times = []
        #blinding
        t = time.time()
        #message = 'f'*65
        message = 'c3ab8ff13720e8ad9047dd39466b3c8974e592c2fa383d4a3960714caef0c4f2'
        print len(message)
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

        
        
__all__ = ["gen_pubpriv_keys", "encrypt", "decrypt", "sign", "verify"]

