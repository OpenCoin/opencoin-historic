"""
>>> from entities import Wallet, Issuer
>>> from transports import ServerTestTransport, ClientTest
>>> walletA = Wallet()
>>> walletB = Wallet()
>>> issuer = Issuer()
>>> issuer.createKeys(512)

>>> CDD.toJson(1)
'[["standard_version","http://opencoin.org/OpenCoinProtocol/1.0"],["currency_identifier","http://opencent.net/OpenCent"],["short_currency_identifier","OC"],["issuer_service_location","opencoin://issuer.opencent.net:8002"],["denominations",[1,2,5,10,20,50,100,200,500,1000]],["issuer_cipher_suite",["RSASigningAlgorithm","RSABlindingAlgorithm","SHA256HashingAlgorithm"]],["issuer_public_master_key","sloGu4+P4rslyC4RiAJrZbG0Z90FwEV88eW1JnNv7BDU33+uIhi2G0f/XL+AoUwmF1VsdhQhzEtGNVjnlx0TViWgqvrYX6AqB1/R3zYP9+JnuIIyHiyS+Z+Y3uoB0sLMD+dvHcDRo7cbb+ZNAvlcPoQ4Hb3+tuxwBMmVkZMaOu8=,AQAB"],["signature",[["keyprint","hxz5pRwS+RFp88qQliXYm3R5uNighktwxqEh4RMOuuk="],["signature","fmgREXeLvrziaPMFa4/KNR9aNda4DZPO+6noROTlbNVX+7ht2Gp/58t6V5eO9HUD2yOWLmVvOlLfVIwmC8PJDefRhMC7ZYt/5tw9ydtiD/zBJzzHGPnK6akB1l2/bkBHEQPXm0PmTFfY5qH069CK0HxzCOj7O6uYFOUqg9slQek="]]]]'

Lets test without having any keys in the mint

>>> t = ClientTest(issuer.giveMintingKey)
>>> walletA.fetchMintingKey(t,denomination='1')
Client <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
Server <Message('HANDSHAKE_ACCEPT',None)>
Client <Message('MINTING_KEY_FETCH_DENOMINATION','1')>
Server <Message('MINTING_KEY_FAILURE','no key for that denomination available')>
Client <Message('GOODBYE',None)>
Server <Message('GOODBYE',None)>
Client <Message('finished',None)>

Now, lets have a key

>>> now = 0; later = 1; much_later = 2
>>> pub1 = issuer.createSignedMintKey('1', now, later, much_later)
>>> t = ClientTest(issuer.giveMintingKey)
>>> walletA.fetchMintingKey(t,denomination='1')
Client <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
Server <Message('HANDSHAKE_ACCEPT',None)>
Client <Message('MINTING_KEY_FETCH_DENOMINATION','1')>
Server <Message('MINTING_KEY_PASS',[...])>
Client <Message('GOODBYE',None)>
Server <Message('GOODBYE',None)>
Client <Message('finished',None)>

Test the transfer token protocol

>>> t = ClientTest(issuer.listen)
>>> walletB.transferTokens(t,'myaccount',[],[1,2],type='redeem')
Client <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
Server <Message('HANDSHAKE_ACCEPT',None)>
Client <Message('TRANSFER_TOKEN_REQUEST',['...', 'myaccount', [], [1, 2], ['type', 'redeem']])>
Server <Message('TRANSFER_TOKEN_ACCEPT',3)>
Client <Message('GOODBYE',None)>
Server <Message('GOODBYE',None)>
Client <Message('finished',None)>


Test the coin spend protocol

>>> t = ClientTest(walletB.listen,clientnick='walletA',servernick='walletB')
>>> t2 = ClientTest(issuer.listen,clientnick='walletB',servernick='issuer')
>>> walletB.issuer_transport = t2
>>> walletA.sendCoins(t,amount=10,target='a book')
walletA <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
walletB <Message('HANDSHAKE_ACCEPT',None)>
walletA <Message('SUM_ANNOUNCE',['...', 3, 'a book'])>
walletB <Message('SUM_ACCEPT',None)>
walletA <Message('COIN_SPEND',['...', [1, 2], 'a book'])>
walletB <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
issuer <Message('HANDSHAKE_ACCEPT',None)>
walletB <Message('TRANSFER_TOKEN_REQUEST',['...', 'my account', [], [1, 2], ['type', 'redeem']])>
issuer <Message('TRANSFER_TOKEN_ACCEPT',3)>
walletB <Message('GOODBYE',None)>
issuer <Message('GOODBYE',None)>
walletB <Message('finished',None)>
walletB <Message('COIN_ACCEPT',None)>
walletA <Message('GOODBYE',None)>
walletB <Message('GOODBYE',None)>
walletA <Message('finished',None)>

"""

def generateCDD():
    import crypto, containers, base64
    ics = crypto.CryptoContainer(signing=crypto.RSASigningAlgorithm,
                                 blinding=crypto.RSABlindingAlgorithm,
                                 hashing=crypto.SHA256HashingAlgorithm)

    keystring = 'sloGu4+P4rslyC4RiAJrZbG0Z90FwEV88eW1JnNv7BDU33+uIhi2G0f/XL+AoUwmF1V' + \
                'sdhQhzEtGNVjnlx0TViWgqvrYX6AqB1/R3zYP9+JnuIIyHiyS+Z+Y3uoB0sLMD+dvHc' + \
                'DRo7cbb+ZNAvlcPoQ4Hb3+tuxwBMmVkZMaOu8=,AQAB,AiF/ORhzAKN5xRV/0h8tR07' + \
                'DOAZ0/iIWZxF2g5oXeTuOP4lX/EJNUrAehe4nzEWLovW7UQHWkYlIsnR4d966D2VGMe' + \
                'UigesAQXO7gq3EewXq2su8Pexh7XDJ1bQlh0HO0sc3DMznc12lM46Doc5bAYm0hPChS' + \
                'ThWrJUE6N4lMhk=,ujW93T/IqikcIMJHdQUDRqVdClYNreRBz+P/vgzrRZqCVnB9x+d' + \
                'kLu5VdPzJKDoeOkaD7AGDyOJJFNSS3w8gMw==,9TJPF5RSdm/u2L0RSaehwrS4IOEUi' + \
                'oBZapb1aQUeohzDgAytuBjp1xywmsYmNEKHXy04qwInKiCPA7blgqdOVQ=='

    private_key = crypto.RSAKeyPair(input=[base64.b64decode(i) for i in keystring.split(',')])
    
    public_key = private_key.newPublicKeyPair()

    cdd = containers.CDD(standard_version='http://opencoin.org/OpenCoinProtocol/1.0',
                         currency_identifier = 'http://opencent.net/OpenCent',
                         short_currency_identifier = 'OC',
                         issuer_service_location = 'opencoin://issuer.opencent.net:8002',
                         denominations = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000],
                         issuer_cipher_suite = ics,
                         issuer_public_master_key = public_key)

    signature = containers.Signature(keyprint=ics.hashing(str(public_key)).digest(),
                                     signature=ics.signing(private_key).sign(ics.hashing(cdd.content_part()).digest()))

    cdd.signature = signature

    return private_key, cdd

CDD_private, CDD = generateCDD()

def makeKeys512():
    """A helper function to generate specific rsa 512 bit keys.

    Used to generate keys we can use other places and have repeatable effects.
    Do not remove/change any of these. It will become messy.

    >>> import crypto, base64
    >>> hash_alg = crypto.SHA256HashingAlgorithm
    >>> keys = makeKeys512()
    
    >>> base64.b64encode(hash_alg(keys[0].stringPrivate()).digest())
    'S/z7RqJEz3PpvbGtA0UYLJ6HVLegvBiVgg8WEkU551w='
    
    >>> base64.b64encode(hash_alg(keys[1].stringPrivate()).digest())
    'YyGbBpAfgTMy8duw4B1lbeSmiGTvww/VkAjTOLqY+JA='
    
    >>> base64.b64encode(hash_alg(keys[2].stringPrivate()).digest())
    'EzEkB1Ji0fmeNbbBYLDSLh8PFKvTa7PfICJi5idh8jM='
    
    >>> base64.b64encode(hash_alg(keys[3].stringPrivate()).digest())
    '66Qd4kVWAaWj8fQMDDsGjA0+M6lMD77XIsV/QYO0KDE='
    
    >>> base64.b64encode(hash_alg(keys[4].stringPrivate()).digest())
    'g8HYpCtirVSjxjrY2myXbI1VGL95/H8fIE4lmorloGk='
    """
    import crypto, base64
    
    def makeKey(keystring):
        return crypto.RSAKeyPair(input=[base64.b64decode(i) for i in keystring.split(',')])
    
    keys = []
    s = 'rYVRng96lTEuiWcM3J6G1o3DqGtw4qbLH/PqSQ/FVe1JpCBG07QJ2QDVwnvgtFZc' + \
        'Iq0rGpB3TMukY4VGAtTp9w==,AQAB,UVV/Z0Y8IDhYZuFdvv+zllgG0SfjVun1pj' + \
        'mPpMV2qwpw2b7QpveBESZZhc8hct6JhGwdPv2RP38W9MEsKwb3AQ==,sIGnsjB85' + \
        'BQJFVev7kQXBYxHcWQrDzrzjyzAwp6NhYE=,+6ttoqGqAEEgbkE9aCrUH4k5mg1g' + \
        'IR3qqbyasAIXW3c='
    keys.append(makeKey(s))

    s = 'zBuIJ/ACheE6HpkB3BnwlsBs3tz21netK32qyne011ViCFX+IbAf/AzxqU8eZW9b' + \
        '1HBtgdFEdYplWaD2/ghZkQ==,AQAB,x5t1QHl8PinRiPLh2rqTixqMXjeCPqOzew' + \
        'De8jq3ZI2e56BWc0QpoHmFVYOPLC7aTuNLAMXRG1xy/3qBjN9GsQ==,0KaRUW+hT' + \
        '14heMy/ysBRq3cZGCXLXxlF8cIyvXpVPBM=,+m0I++1ewqqXzyQyg27uBPzt6M+t' + \
        'cIgaJqFk7AMpQEs='
    keys.append(makeKey(s))

    s = 'qQMxi5ZWvGNOSoWD2oQG/rcOYyu54JMPpShgClph5O+3MiEoKxUrxt6HKZ9XUfXO' + \
        '1nkAVM/p3D3AAKm8EghAWQ==,AQAB,Tc9mk/kW3Yxqkux9E7EM91+XhBixbq7F2S' + \
        'eJb7rErvzdu93lb133GoSutTgw04fZxLtCJmH5zCksYB0AxeoNwQ==,wcUPKrytT' + \
        'rxmjiySKK5C5gSmlH3zntNLKrQBEmgcwDU=,30qxhmW49MKN4vrjhaB4DHNLOAA7' + \
        'FR9BC4f42j1CDBU='
    keys.append(makeKey(s))

    keys.append(makeKey('iKRbuOcx0ZaonCW2174PGJ7NndVz2SsrviRFBI7iH1Ef2DAY' +
        '+mMQOkrZouSoERGx+qzfxxomsbdNAWWn9DE5qQ==,AQAB,KDCPedcmZAr4FNVS7i' +
        'nMruUmfSHnLRzxhL+OPUT5ZVQ8GLPUrwb5xu64iN1wA+GX3Ye4MBZnKTxBTztyqs' +
        'IeMQ==,o9YCYd6frBAkNn6GTi5Xdq+KWISbgSz2ATpQfYCw/ZM=,1YInKagsCHLs' +
        'Qxngi0XH1aCrI1Z82bCyEar4dENO0VM='))

    keys.append(makeKey('0LacqxKYf46SeT4fLOe4Ovar2ubneiQzUltTZ19r/RyyYBYi' +
        '+0FQlLApSQeYKIq1GBmPRZRC0PqrcJdO5d1P/Q==,AQAB,H7GbWN8aCUS9OWwVj9' +
        'wgPdP3hOZLgGC+6mKz556151mN4hDtscN4v0WoO7MVC19sPr9h8v7VQrCxabVE1k' +
        'BcAQ==,2HW624HBCsiylu4ivxbzH2jNt2wh4FosOjmqxa1qJbU=,9tahqi751CGj' +
        'p7jaihYBKeYl9dVPmZN2q81jhM7z7ik='))

    return keys

keys512 = makeKeys512() 

def addSignature(cont, hash_alg, sign_alg, signing_key, keyprint):
    from containers import Signature
    hasher = hash_alg(cont.content_part())
    signer = sign_alg(signing_key)
    signature = Signature(keyprint=keyprint,
                          signature=signer.sign(hasher.digest()))
    cont.signature = signature
    return cont

if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
