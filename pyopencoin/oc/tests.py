"""
>>> from entities import Wallet, Issuer
>>> from transports import ServerTestTransport
>>> walletA = Wallet()
>>> walletB = Wallet()
>>> issuer = Issuer()
>>> issuer.createKeys(512)

Lets test without having any keys in the mint

>>> t = ServerTestTransport(walletA.fetchMintingKey,denomination='1')
>>> issuer.giveMintingKey(t)
Client <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
Server <Message('HANDSHAKE_ACCEPT',None)>
Client <Message('MINTING_KEY_FETCH_DENOMINATION','1')>
Server <Message('MINTING_KEY_FAILURE','no key for that denomination available')>
Client <Message('GOODBYE',None)>
Server <Message('GOODBYE',None)>
Client <Message('finished',None)>

Now, lets have a key

>>> pub1 = issuer.createSignedMintKey('1','now','later','much later')
>>> t = ServerTestTransport(walletA.fetchMintingKey,denomination='1')
>>> issuer.giveMintingKey(t)
Client <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
Server <Message('HANDSHAKE_ACCEPT',None)>
Client <Message('MINTING_KEY_FETCH_DENOMINATION','1')>
Server <Message('MINTING_KEY_PASS',[...])>
Client <Message('GOODBYE',None)>
Server <Message('GOODBYE',None)>
Client <Message('finished',None)>


Test the coin spend protocol

>>> t = ServerTestTransport(walletA.sendCoins,amount=10,target='a book')
>>> walletB.listen(t)
Client <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
Server <Message('HANDSHAKE_ACCEPT',None)>
Client <Message('SUM_ANNOUNCE',['...', 3, 'a book'])>
Server <Message('SUM_ACCEPT',None)>
Client <Message('COIN_SPEND',['...', [1, 2], 'a book'])>
Server <Message('COIN_ACCEPT',None)>
Client <Message('GOODBYE',None)>
Server <Message('GOODBYE',None)>
Client <Message('finished',None)>
"""


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
