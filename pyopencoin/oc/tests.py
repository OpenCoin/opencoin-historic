"""
>>> from entities import Wallet, Issuer
>>> from transports import ServerTestTransport, ClientTest
>>> walletA = Wallet()
>>> walletB = Wallet()
>>> issuer = Issuer()
>>> issuer.createKeys(512)

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


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
