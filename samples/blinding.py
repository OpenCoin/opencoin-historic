""" ########################################################################
    Short introduction to RSA encryption, signature and blinding.
    License:    GPL
    Copyright:  Nils Toedtmann 2007 <nils@opencoin.net>
                Joerg Baach <mail1@baach.de>
    Version:    2007-11-25-04
    ########################################################################

    Preliminary note you may or may not skip:

    All calculations will be executed modulo some natural number N. Maths 
    calls the set {0,..,N-1} together with the operations +, - and * the 
    "ring of residues modulo N". These operations are the same as for 
    integers plus the "mod" operation (ok, i simplify a bit ;-)

    A number is invertible modulo N (= you can divide by it modulo N) iff
    it is coprime to N (= y and N have no common divisor). But in contrast 
    to +, - and *, the division is quite different. So telling python 
    
        x_divided_by_y_modulo_N = x / y % N

    does not work. We use a slightly altered "extended euclidian algorithm"
    (usually used to compute the GCD of two numbers) for division mod N
    (see devide below)
    
    ########################################################################
    RSA 1: KEY GENERATION

    Bob (key owner) selects two random primes (~1024bits) and calculates 
    their product (~2048bits, "RSA key size") which will be our modulus N. 
    Except key generation *all* computations will be %N.
    
    >>> p = 37
    >>> q = 61
    >>> N = p* q

    The key pair are two numbers <N such that

        public_key * secret_key == 1  modulo   (p-1)*(q-1)

    It is unfeasible without knowing the factorization of N, but knowing
    p and q just select a random public_key and invert it. If it turns out
    to be not coprime to (p-1)(q-1), select an other public_key.
    
    >>> public_key  = 101
    >>> secret_key  = divide(1,public_key,(p-1)*(q-1))

    ########################################################################
    RSA 2: ENCRYPTION

    Alice (sender) select's Message <N to send. Fetches Bob's public key 
    (including the modulus N) and encrypts with it.

    >>> cleartext  = 1465
    >>> ciphertext = cleartext**public_key % N

    Bob (receiver) decrypts using his secret key. Should gain ClearText.
    
    >>> decryptedtext = ciphertext**secret_key  %N
    >>> decryptedtext == cleartext
    True

    ########################################################################
    RSA 3: SIGNATURE

    Bob (signer) select's Message <N (usually the hash of a longer text) and 
    signs it using his secret key.
    
    >>> message = 755
    >>> signature = message**secret_key %N

    Alice (verifier) verifies using Bob's public key. Should gain Message.

    >>> verified_signature = signature**public_key %N
    >>> verified_signature == message
    True


    ########################################################################
    RSA 4: BLIND SIGNATURE

    Alice (requester) selects a blank <N she wants the issuer to sign and a 
    random number ("blinder") for blinding. She creates the blind and keeps 
    the blinder secret: 

    >>> blank = 12
    >>> blinder = 101
    >>> blind = blank * (blinder**public_key) %N

    Bob (issuer) signs the blind with his secret key
    
    >>> signature_of_blind = blind**secret_key %N

    Alice unblinds the signed blind
    
    >>> unblinded_signature_of_blind= divide( signature_of_blind, blinder, N )

    If somebody had the requester's blank *and* the issuer's secret key, 
    he could have directly computed this:
    
    >>> signature_of_blank = blank**secret_key %N
    >>> unblinded_signature_of_blind == signature_of_blank 
    True

    Alice uses the ususal signature verification algorithm: 
    
    >>> (unblinded_signature_of_blind**public_key %N) == blank
    True
"""


from eea import divide


def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
