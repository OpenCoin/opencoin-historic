"""
>>> from entities import Wallet, Issuer
>>> from transports import ServerTestTransport, ClientTest
>>> walletA = Wallet()
>>> walletB = Wallet()
>>> issuer = Issuer()
>>> issuer.createKey(keylength=512)

>>> CDD.toJson()
'[["standard_version","http://opencoin.org/OpenCoinProtocol/1.0"],["currency_identifier","http://opencent.net/OpenCent"],["short_currency_identifier","OC"],["issuer_service_location","opencoin://issuer.opencent.net:8002"],["denominations",[1,2,5,10,20,50,100,200,500,1000]],["issuer_cipher_suite",["RSASigningAlgorithm","RSABlindingAlgorithm","SHA256HashingAlgorithm"]],["issuer_public_master_key","sloGu4+P4rslyC4RiAJrZbG0Z90FwEV88eW1JnNv7BDU33+uIhi2G0f/XL+AoUwmF1VsdhQhzEtGNVjnlx0TViWgqvrYX6AqB1/R3zYP9+JnuIIyHiyS+Z+Y3uoB0sLMD+dvHcDRo7cbb+ZNAvlcPoQ4Hb3+tuxwBMmVkZMaOu8=,AQAB"],["signature",[["keyprint","hxz5pRwS+RFp88qQliXYm3R5uNighktwxqEh4RMOuuk="],["signature","fmgREXeLvrziaPMFa4/KNR9aNda4DZPO+6noROTlbNVX+7ht2Gp/58t6V5eO9HUD2yOWLmVvOlLfVIwmC8PJDefRhMC7ZYt/5tw9ydtiD/zBJzzHGPnK6akB1l2/bkBHEQPXm0PmTFfY5qH069CK0HxzCOj7O6uYFOUqg9slQek="]]]]'

Lets test without having any keys in the mint

>>> t = ClientTest(issuer.giveMintingKey)
>>> walletA.fetchMintingKey(t,denominations=['1'])
Client <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
Server <Message('HANDSHAKE_ACCEPT',None)>
Client <Message('MINTING_KEY_FETCH_DENOMINATION',[['1'], '0'])>
Server <Message('MINTING_KEY_FAILURE',[['1', 'Unknown denomination']])>
Client <Message('GOODBYE',None)>
Server <Message('GOODBYE',None)>
Client <Message('finished',None)>

Now, lets have a key

>>> now = 0; later = 1; much_later = 2
>>> pub1 = issuer.createSignedMintKey('1', now, later, much_later)
>>> t = ClientTest(issuer.giveMintingKey)
>>> walletA.fetchMintingKey(t,denominations=['1'])
Client <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
Server <Message('HANDSHAKE_ACCEPT',None)>
Client <Message('MINTING_KEY_FETCH_DENOMINATION',[['1'], '0'])>
Server <Message('MINTING_KEY_PASS',[[...]])>
Client <Message('GOODBYE',None)>
Server <Message('GOODBYE',None)>
Client <Message('finished',None)>

Test the transfer token protocol
>>> issuer = makeIssuer()
>>> t = ClientTest(issuer.listen)
>>> coin1 = coins[0][0] # denomination of 1
>>> coin2 = coins[1][0] # denomination of 2
>>> walletB.coins = [coin1, coin2]
>>> walletB.transferTokens(t,'myaccount',[],[coin1, coin2],type='redeem')
Client <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
Server <Message('HANDSHAKE_ACCEPT',None)>
Client <Message('TRANSFER_TOKEN_REQUEST',['...', 'myaccount', [], [[(...)], [(...)]], [['type', 'redeem']]])>
Server <Message('TRANSFER_TOKEN_ACCEPT',['...', []])>
Client <Message('GOODBYE',None)>
Server <Message('GOODBYE',None)>
Client <Message('finished',None)>


Test the coin spend protocol.

>>> issuer = makeIssuer()
>>> t = ClientTest(walletB.listen,clientnick='walletA',servernick='walletB')
>>> t2 = ClientTest(issuer.listen,clientnick='walletB',servernick='issuer')
>>> walletB.issuer_transport = t2
>>> walletA.coins=[coin1]
>>> walletA.sendCoins(t, target='a book', amount=1)
walletA <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
walletB <Message('HANDSHAKE_ACCEPT',None)>
walletA <Message('SUM_ANNOUNCE',['...', '1', 'a book'])>
walletB <Message('SUM_ACCEPT',None)>
walletA <Message('COIN_SPEND',['...', [[(...)]], 'a book'])>
walletB <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
issuer <Message('HANDSHAKE_ACCEPT',None)>
walletB <Message('TRANSFER_TOKEN_REQUEST',['...', 'my account', [], [[(...)]], [['type', 'redeem']]])>
issuer <Message('TRANSFER_TOKEN_ACCEPT',['...', []])>
walletB <Message('GOODBYE',None)>
issuer <Message('GOODBYE',None)>
walletB <Message('finished',None)>
walletB <Message('COIN_ACCEPT',None)>
walletA <Message('GOODBYE',None)>
walletB <Message('GOODBYE',None)>
walletA <Message('finished',None)>


>>> coinB.validate_with_CDD_and_MintKey(CDD,mint_key1)
True
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

#IS private key, CDD
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

#contains private mint keys!
keys512 = makeKeys512() 

def addSignature(cont, hash_alg, sign_alg, signing_key, keyprint):
    from containers import Signature
    hasher = hash_alg(cont.content_part())
    signer = sign_alg(signing_key)
    signature = Signature(keyprint=keyprint,
                          signature=signer.sign(hasher.digest()))
    cont.signature = signature
    return cont

def makeMintKeys():
    """makes MintKeys of denomination 1, 2, and 5.
    >>> import base64
    >>> mintkey1, mintkey2, mintkey5, mintkey10 = makeMintKeys()
    
    >>> base64.b64encode(mintkey1.signature.signature)
    'l6viHZFCZSlYVRVXrawzb7MYPmgVbkuCbjot5giOiGWJ7PuiTUOFd5O/CTf5QRX6snrzQhLqImQ414Z2vNChcVBBu1zIslQ9Pxti1WW9EA0Z8akeQoWG11S4eqbwvbBHStO1uB6vGQAkR9g1zJvS+NG3vzF/vYnADtD5CQ4bpvg='

    >>> base64.b64encode(mintkey2.signature.signature)
    'iVcVpYvER6702tkYvqqdiOuugMKqhHAwln1jDLTk1sGyZPr0y5b1V/qqgYpJUBayZM/hRtWlN4NxiRQbISjU1ZGAZTmARYfU+MigCXbATZXaS1GjZjx2/gIZnTFHF9T6N6elTKTmqQdV0ZExjWZmHDmco0alwOKK9n+ta5o7pvs='
    
    >>> base64.b64encode(mintkey5.signature.signature)
    'IJmSiWPoNOt+kMZle3Z/4Fex17l4D8Hq1tr1l01MCGWHS1+6syOxIIJ2giSQmPQlZRrTwRrbUOEblGs9K0G+e4OlbzB5CywDo6z9FDWSSnXqlEEEt4tYzzsAjqvhjPq3/i182J5sucb70ea+vrIj7Kll5V9JYAxMocgd16dXwDc='
    
    >>> base64.b64encode(mintkey10.signature.signature)
    'nx5Jthxo4QMPTmyEui/TVyKyDxjCnhhJLeAbgYyl5tkk+VNNzdkBd7Ry/wCv5ijs8lSUTkPaQt/d3AVHlMxSTF93/5y1/vl47hFpAyclXlMkqagGuGrFSsnQYYqEnhnCcaAl6i9rBGcrQh4YYFA3fIVkkVa/fL2aIYpPpoMvKcg='
    """
    from containers import MintKey
    import copy
    from calendar import timegm

    hash_alg = CDD.issuer_cipher_suite.hashing
    sign_alg = CDD.issuer_cipher_suite.signing
    blind_alg = CDD.issuer_cipher_suite.blinding
                                                  
    def makeMintKey(denomination, public, private):
        mintKey = MintKey(key_identifier=public.key_id(hash_alg),
                          currency_identifier='http://opencent.net/OpenCent',
                          denomination=denomination,
                          not_before=timegm((2008,1,1,0,0,0)),
                          key_not_after=timegm((2008,2,1,0,0,0)),
                          coin_not_after=timegm((2008,4,1,0,0,0)),
                          public_key=public)
        addSignature(mintKey, hash_alg, sign_alg, CDD_private, CDD.signature.keyprint)

        return mintKey

    private0 = keys512[0]
    public0 = private0.newPublicKeyPair()
    mintKey0 = makeMintKey(1, public0, private0)

    private1 = keys512[1]
    public1 = private1.newPublicKeyPair()
    mintKey1 = makeMintKey(2, public1, private1)

    private2 = keys512[2]
    public2 = private2.newPublicKeyPair()
    mintKey2 = makeMintKey(5, public2, private2)  

    private3 = keys512[3]
    public3 = private3.newPublicKeyPair()
    mintKey3 = makeMintKey(10, public3, private3)  

    return (mintKey0, mintKey1, mintKey2, mintKey3)

mintKeys = makeMintKeys()

def makeCoins():
    """makes coins for testing
    >>> coins = makeCoins()

    >>> coins[0][0].validate_with_CDD_and_MintKey(CDD, mintKeys[0])
    True
    >>> coins[0][1].validate_with_CDD_and_MintKey(CDD, mintKeys[0])
    True

    >>> coins[1][0].validate_with_CDD_and_MintKey(CDD, mintKeys[1])
    True
    >>> coins[1][1].validate_with_CDD_and_MintKey(CDD, mintKeys[1])
    True
    >>> coins[1][2].validate_with_CDD_and_MintKey(CDD, mintKeys[1])
    True
    >>> coins[1][3].validate_with_CDD_and_MintKey(CDD, mintKeys[1])
    True
    >>> coins[1][4].validate_with_CDD_and_MintKey(CDD, mintKeys[1])
    True

    >>> coins[2][0].validate_with_CDD_and_MintKey(CDD, mintKeys[2])
    True
    >>> coins[2][1].validate_with_CDD_and_MintKey(CDD, mintKeys[2])
    True
    
    >>> coins[3][0].validate_with_CDD_and_MintKey(CDD, mintKeys[3])
    True
    """ 
    from containers import CurrencyCoin

    hash_alg = CDD.issuer_cipher_suite.hashing
    sign_alg = CDD.issuer_cipher_suite.signing
    
    def makeCoin(serial, private_key, mint_key):
        coin = CurrencyCoin(standard_identifier=CDD.standard_version,
                            currency_identifier=CDD.currency_identifier,
                            denomination=mint_key.denomination,
                            key_identifier=mint_key.key_identifier,
                            serial=serial)
        coin.signature = sign_alg(private_key).sign(hash_alg(coin.content_part()).digest())
        return coin
     
    private0 = keys512[0]
    mintKey0 = mintKeys[0] # Denomination of 1
    
    coin0 = (makeCoin('abcdefghijklmnopqrstuvwxyz', private0, mintKey0),
             makeCoin('xxxxxxxxxxxxxxxxxxxxxxxxxx', private0, mintKey0))

    private1 = keys512[1]
    mintKey1 = mintKeys[1] # Denomination of 2

    coin1 = (makeCoin('abcdefghijklmnopqrstuvwxyz', private1, mintKey1),
             makeCoin('aaaaaaaaaaaaaaaaaaaaaaaaaa', private1, mintKey1),
             makeCoin('bbbbbbbbbbbbbbbbbbbbbbbbbb', private1, mintKey1),
             makeCoin('cccccccccccccccccccccccccc', private1, mintKey1),
             makeCoin('dddddddddddddddddddddddddd', private1, mintKey1))

    private2 = keys512[2]
    mintKey2 = mintKeys[2] # Denomination of 5

    coin2 = (makeCoin('abcdefghijklmnopqrstuvwxyz', private2, mintKey2),
             makeCoin('xxxxxxxxxxxxxxxxxxxxxxxxxx', private2, mintKey2),
             makeCoin('aaaaaaaaaaaaaaaaaaaaaaaaaa', private2, mintKey2))
    
    private3 = keys512[3]
    mintKey3 = mintKeys[3] # Denomination of 10

    coin3 = (makeCoin('abcdefghijklmnopqrstuvwxyz', private3, mintKey3),)

    return (coin0, coin1, coin2, coin3)

coins = makeCoins()


#summary of containers
is_private_key = CDD_private
CDD = CDD
mint_private_key1 = keys512[0]
mint_private_key2 = keys512[1]
mint_private_key3 = keys512[2]
mint_key1 = mintKeys[0]
mint_key2 = mintKeys[1]
mint_key3 = mintKeys[2] #denomination of 5
coinA = coins[0][0] # mint_key1
coinB = coins[0][1] # mint_key1
coinC = coins[1][0] # mint_key2


#entities
import entities

def makeIssuer():
    '''
    >>> issuer = makeIssuer()
    '''
    issuer = entities.Issuer()
    issuer.signedKeys = {1:[mint_key1],
                         2:[mint_key2]}
    issuer.keyids = {mint_key1.key_identifier:mint_key1, 
                     mint_key2.key_identifier:mint_key2}

    issuer.mint.addMintKey(mint_key1, CDD.issuer_cipher_suite.signing)
    issuer.mint.addMintKey(mint_key2, CDD.issuer_cipher_suite.signing)

    issuer.mint.privatekeys = {mint_key1.key_identifier: mint_private_key1,
                               mint_key2.key_identifier: mint_private_key2}

    issuer.keys = is_private_key
    issuer.cdd = CDD
    return issuer

if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
