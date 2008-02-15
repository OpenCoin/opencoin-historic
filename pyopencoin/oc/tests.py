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

if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
