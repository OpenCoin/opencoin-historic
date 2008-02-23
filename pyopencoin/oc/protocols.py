"""
Protocol have states, which are basically methods that consume messages, do
something and return messages. The states are just methods, and one state
might change the state of its protocol to another state. 

A protocol writes to a transport, using Transport.write. It receives messages
from the transport with Protocol.newMessage.

A state (a protocol method) returns messages, it does not write directly back
to a transport (XXX not sure about this, what if a state needs to communicate
with another enity). Instead newMessage by default writes back to the transport.
(XXX maybe the transport could take the returned message, and write it up its own,
ah write method?)

Before returning the message, the state should set the protocols state to the next
state (sounds a bit ackward, its easy, check the states code)
"""

from messages import Message
import containers    

class Protocol:
    """A protocol ties messages and actions togehter, it is basically one side
       of an interaction. E.g. when A exchanges a coin with B, A would use the
       walletSenderProtocol, and B the walletRecipientProtocol."""

    def __init__(self):
        'Set the initial state'
        
        self.state = self.start
        self.result = None

    def setTransport(self,transport):
        'get the transport we are working with'
        
        self.transport = transport
        
    def start(self,message):
        'this should be the initial state of the protocol'
       
        pass

    def goodbye(self,message):
        self.state = self.finish
        return Message('GOODBYE')

    def finish(self,message):
        'always the last state. There can be other final states'        
        return Message('finished')
                    
    def newMessage(self,message):
        'this is used by a transport to pass on new messages to the protocol'

        out = self.state(message)
        self.transport.write(out)
        return out

    def newState(self,method):
        self.state = method

    def initiateHandshake(self,message):    
        self.newState(self.firstStep)
        return Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})


class answerHandshakeProtocol(Protocol):


    def __init__(self,**mapping):
        Protocol.__init__(self)
        self.mapping = mapping

    def start(self,message):

        if message.type == 'HANDSHAKE':
            if message.data['protocol'] == 'opencoin 1.0':
                self.newState(self.dispatch)
                return Message('HANDSHAKE_ACCEPT')
            else:
                self.newState(self.goodbye)
                return Message('HANDSHAKE_REJECT','did not like the protocol version')
        else:
            return Message('PROTOCOL_ERROR','please do a handshake')


    def dispatch(self,message):        
        self.result = message
        nextprotocol = self.mapping[message.type]
        self.transport.setProtocol(nextprotocol)
        m = nextprotocol.newMessage(message)
        #print 'here ', m
        #return m

############################### Spending coins (w2w) ########################################


class CoinSpendSender(Protocol):
    """
    >>> from tests import coins
    >>> coin1 = coins[0][0]
    >>> coin2 = coins[1][0]
    >>> css = CoinSpendSender([coin1,coin2],'foobar')
    >>> css.state(Message(None))
    <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
    >>> css.state(Message('HANDSHAKE_ACCEPT'))
    <Message('SUM_ANNOUNCE',['...', 3, 'foobar'])>
    >>> css.state(Message('SUM_ACCEPT'))
    <Message('COIN_SPEND',['...', [[(...)], [(...)]], 'foobar'])>
    >>> css.state(Message('COIN_ACCEPT'))
    <Message('GOODBYE',None)>
    >>> css.state(Message('Really?'))
    <Message('finished',None)>
    """
    def __init__(self,coins,target):

        self.coins = coins
        self.amount = sum(coins)
        self.target = target
        
        import crypto,base64
        id = crypto.Random().getRandomString(128) #XXX is that a good enough id?
        self.transaction_id = base64.b64encode(id)

        Protocol.__init__(self)
        self.state = self.initiateHandshake

    def firstStep(self,message):       
        self.state = self.spendCoin
        return Message('SUM_ANNOUNCE',[self.transaction_id,
                                       self.amount,
                                       self.target])


    def spendCoin(self,message):
        if message.type == 'SUM_ACCEPT':
            self.state = self.goodbye            
            jsonCoins = [c.toPython() for c in self.coins]
            return Message('COIN_SPEND',[self.transaction_id,
                                         jsonCoins,
                                         self.target])

    def goodbye(self,message):
        if message.type == 'COIN_ACCEPT':
            self.state = self.finish
            return Message('GOODBYE')


class CoinSpendRecipient(Protocol):
    """
    >>> import entities
    >>> from tests import coins
    >>> coin1 = coins[0][0].toPython() # Denomination of 1
    >>> coin2 = coins[1][0].toPython() # Denomination of 2
    >>> w = entities.Wallet()
    >>> csr = CoinSpendRecipient(w)
    >>> csr.state(Message('SUM_ANNOUNCE',['123',3,'a book']))
    <Message('SUM_ACCEPT',None)>
    >>> csr.state(Message('COIN_SPEND',['123', [coin1, coin2], 'a book']))
    <Message('COIN_ACCEPT',None)>
    >>> csr.state(Message('Goodbye',None))
    <Message('GOODBYE',None)>
    >>> csr.state(Message('foobar'))
    <Message('finished',None)>

    TODO: Add PROTOCOL_ERROR checking
    """
    
    def __init__(self,wallet,issuer_transport = None):
        self.wallet = wallet
        self.issuer_transport = issuer_transport
        Protocol.__init__(self)

    def start(self,message):
        if message.type == 'SUM_ANNOUNCE':
            self.transaction_id = message.data[0]
            self.sum = message.data[1]
            self.target = message.data[2]
            #get some feedback from interface somehow
            action = self.wallet.confirmReceiveCoins('the other wallet id',self.sum,self.target)
            if action == 'reject':
                self.state = self.goodby                
                return Message('SUM_REJECT')
            else:
                self.action = action
                self.state = self.handleCoins
                return Message('SUM_ACCEPT')
        else:
            self.state = self.goodbye
            return Message('Expected something else')

    def handleCoins(self,message):
        if message.type == 'COIN_SPEND':
            
            #be conservative
            result = Message('COIN_REJECT','default')
            
            transaction_id,coins,target  = message.data
            try:
                coins = [containers.CurrencyCoin().fromPython(c) for c in coins]
            except:
                return Message('PROTOCOL_ERROR', 'send again')
            
            if transaction_id != self.transaction_id:
                result = Message('COIN_REJECT','transaction_id')
            
            elif sum(coins) != self.sum:
                result = Message('COIN_REJECT','wrong sum')
            
            elif target != self.target:
                result = Message('COIN_REJECT','wrong target')
            
            elif self.action in ['redeem','exchange','trust']:
                out = self.wallet.handleIncomingCoins(coins,self.action,target)
                if out:
                    result = Message('COIN_ACCEPT')
        self.state = self.goodbye
        return result


############################### Transfer tokens  ########################################

class TransferTokenSender(Protocol):
    """
    >>> tts = TransferTokenSender('my account',[],[1,2],type='redeem')
    >>> tts.state(Message(None))
    <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
    >>> tts.state(Message('HANDSHAKE_ACCEPT'))
    <Message('TRANSFER_TOKEN_REQUEST',['...', 'my account', [], [1, 2], ['type', 'redeem']])>
    >>> tts.state(Message('TRANSFER_TOKEN_ACCEPT',3))
    <Message('GOODBYE',None)>

    """

    
    def __init__(self,target,blanks,coins,**kwargs):
        import base64
        from crypto import _r as Random
        id = Random.getRandomString(128) #XXX is that a good enough id?
        self.transaction_id = base64.b64encode(id)

        self.target = target
        self.blanks = blanks
        self.coins = coins
        self.kwargs = kwargs

        Protocol.__init__(self)
        self.state = self.initiateHandshake
   
    def firstStep(self,message):
        data = [self.transaction_id,
                self.target,
                self.blanks,
                self.coins]
        for item in self.kwargs.items():
            data.append(list(item))                
        self.state = self.goodbye
        return Message('TRANSFER_TOKEN_REQUEST',data)

    def goodbye(self,message):
        if message.type == 'TRANSFER_TOKEN_ACCEPT':
            self.result = 1
        else:
            self.result = 0
        self.state = self.finish
        return Message('GOODBYE')


class TransferTokenRecipient(Protocol):
    """
    >>> ttr = TransferTokenRecipient()
    >>> ttr.state(Message('TRANSFER_TOKEN_REQUEST',['...', 'my account', [], [1, 2], ['type', 'redeem']]))
    <Message('TRANSFER_TOKEN_ACCEPT',3)>
    """
    def start(self,message):
        transaction_id,target,blanks,coins = message.data[:4]

        self.state = self.goodbye
        return Message('TRANSFER_TOKEN_ACCEPT',sum(coins))

############################### Mint key exchange ########################################



class fetchMintingKeyProtocol(Protocol):
    """
    Used by a wallet to fetch the mints keys, needed when 
    creating blanks
       
    ??? Should it be suitable to fetch more than one denomination at a time?
    Maybe all the keys?

    Lets fetch by denomination

    >>> fmp = fetchMintingKeyProtocol(denomination=1)
    >>> fmp.state(Message(None))
    <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>

    >>> fmp.state(Message('HANDSHAKE_ACCEPT'))
    <Message('MINTING_KEY_FETCH_DENOMINATION',1)>

    >>> from tests import mintKeys
    >>> mintKey = mintKeys[0]
    >>> fmp.state(Message('MINTING_KEY_PASS',mintKey.toPython()))
    <Message('GOODBYE',None)>


    And now by keyid

    >>> fmp = fetchMintingKeyProtocol(keyid='sj17RxE1hfO06+oTgBs9Z7xLut/3NN+nHJbXSJYTks0=')
    >>> fmp.state(Message(None))
    <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>

    >>> fmp.state(Message('HANDSHAKE_ACCEPT'))
    <Message('MINTING_KEY_FETCH_KEYID','sj17RxE1hfO06+oTgBs9Z7xLut/3NN+nHJbXSJYTks0=')>

    >>> fmp.state(Message('MINTING_KEY_PASS',mintKey.toPython()))
    <Message('GOODBYE',None)>


    Lets have some problems a failures (we set the state
    to getKey to reuse the fmp object and save a couple
    of lines)

    >>> fmp.newState(fmp.getKey)
    >>> fmp.state(Message('MINTING_KEY_FAILURE',))
    <Message('GOODBYE',None)>
   
    Now lets break something
    
    >>> fmp.newState(fmp.getKey)
    >>> fmp.state(Message('FOOBAR'))
    <Message('PROTOCOL_ERROR','send again')>

    >>> fmp.newState(fmp.getKey)
    >>> fmp.state(Message('MINTING_KEY_PASS', ["foo"]))
    <Message('PROTOCOL_ERROR','send again')>
    
    """
    
    
    def __init__(self,denomination=None,keyid=None):
        
        self.denomination = denomination
        self.keyid = keyid
        self.keycert = None

        Protocol.__init__(self)

    def start(self,message):
        self.newState(self.requestKey)
        return Message('HANDSHAKE',{'protocol':'opencoin 1.0'})

    def requestKey(self,message):
        """Completes handshake, asks for the minting keys """

        if message.type == 'HANDSHAKE_ACCEPT':
            
            if self.denomination:
                self.newState(self.getKey)
                return Message('MINTING_KEY_FETCH_DENOMINATION',self.denomination)
            elif self.keyid:
                self.newState(self.getKey)
                return Message('MINTING_KEY_FETCH_KEYID',self.keyid) 

        elif message.type == 'HANDSHAKE_REJECT':
            self.newState(self.finish)
            return Message('GOODBYE')

        else:
            return Message('PROTOCOL ERROR','send again')

    def getKey(self,message):
        """Gets the actual key"""

        if message.type == 'MINTING_KEY_PASS':
            try:
                self.keycert = containers.MintKey().fromPython(message.data)
            except Exception, reason:
                return Message('PROTOCOL_ERROR','send again')
            
            self.newState(self.finish)
            return Message('GOODBYE')
                

        elif message.type == 'MINTING_KEY_FAILURE':
            self.reason = message.data
            self.newState(self.finish)
            return Message('GOODBYE')
        
        else:
            return Message('PROTOCOL_ERROR','send again')



class giveMintingKeyProtocol(Protocol):
    """An issuer hands out a key. The other side of fetchMintingKeyProtocol.
    >>> from entities import Issuer
    >>> issuer = Issuer()
    >>> issuer.createKeys(512)
    >>> now = 0; later = 1; much_later = 2
    >>> pub1 = issuer.createSignedMintKey('1', now, later, much_later)
    >>> gmp = giveMintingKeyProtocol(issuer)
    
    >>> gmp.state(Message('HANDSHAKE',{'protocol': 'opencoin 1.0'}))
    <Message('HANDSHAKE_ACCEPT',None)>

    >>> m = gmp.state(Message('MINTING_KEY_FETCH_DENOMINATION','1'))
    >>> m == Message('MINTING_KEY_PASS',pub1.toPython())
    True

    >>> gmp.newState(gmp.giveKey)
    >>> m = gmp.state(Message('MINTING_KEY_FETCH_KEYID',pub1.key_identifier))
    >>> m == Message('MINTING_KEY_PASS',pub1.toPython())
    True

    >>> gmp.newState(gmp.giveKey)
    >>> gmp.state(Message('MINTING_KEY_FETCH_DENOMINATION','2'))
    <Message('MINTING_KEY_FAILURE','no key for that denomination available')>
   

    >>> gmp.newState(gmp.giveKey)
    >>> gmp.state(Message('MINTING_KEY_FETCH_KEYID','non existient id'))
    <Message('MINTING_KEY_FAILURE','no such keyid')>

    >>> gmp.newState(gmp.giveKey)
    >>> gmp.state(Message('bla','blub'))
    <Message('MINTING_KEY_FAILURE','wrong question')>

    TODO: Add PROTOCOL_ERROR checking (when the coins don't undo)
    """

    def __init__(self,issuer):
        
        self.issuer = issuer
        Protocol.__init__(self)


    def start(self,message):

        if message.type == 'HANDSHAKE':
            if message.data['protocol'] == 'opencoin 1.0':
                self.newState(self.giveKey)
                return Message('HANDSHAKE_ACCEPT')
            else:
                self.newState(self.goodbye)
                return Message('HANDSHAKE_REJECT','did not like the protocol version')
        else:
            return Message('PROTOCOL_ERROR','please do a handshake')


    def giveKey(self,message):
    
        self.newState(self.goodbye)

        error = None
        if message.type == 'MINTING_KEY_FETCH_DENOMINATION':
            try:
                key = self.issuer.getKeyByDenomination(message.data)            
            except 'KeyFetchError':                
                error = 'no key for that denomination available'
        
        elif message.type == 'MINTING_KEY_FETCH_KEYID':                
            try:
                key = self.issuer.getKeyById(message.data)                
            except 'KeyFetchError':                
                error = 'no such keyid'
        
        else:
            error = 'wrong question'

        if not error:            
            return Message('MINTING_KEY_PASS',key.toPython())
        else:
            return Message('MINTING_KEY_FAILURE',error)

############################### For testing ########################################

class WalletSenderProtocol(Protocol):
    """
    This is just a fake protocol, just showing how it works

    >>> sp = WalletSenderProtocol(None)
   
    It starts with sending some money
    >>> sp.state(Message(None))
    <Message('sendMoney',[1, 2])>
    
    >>> sp.state(Message('Foo'))
    <Message('Please send a receipt',None)>

    Lets give it a receipt
    >>> sp.state(Message('Receipt'))
    <Message('Goodbye',None)>

    >>> sp.state(Message('Bla'))
    <Message('finished',None)>

    >>> sp.state(Message('Bla'))
    <Message('finished',None)>

    """

    def __init__(self,wallet):
        'we would need a wallet for this to work'

        self.wallet = wallet
        Protocol.__init__(self)

    def start(self,message):
        'always set the new state before returning'
        
        self.state = self.waitForReceipt
        return Message('sendMoney',[1,2])

    def waitForReceipt(self,message):
        'after sending we need a receipt'

        if message.type == 'Receipt':
            self.state=self.finish
            return Message('Goodbye')
        else:
            return Message('Please send a receipt')

class WalletRecipientProtocol(Protocol):

    def __init__(self,wallet=None):
        self.wallet = wallet
        Protocol.__init__(self)

    def start(self,message):
        if message.type == 'sendMoney':
            if self.wallet:
                self.wallet.coins.extend(message.data)
            self.state=self.Goodbye
            return Message('Receipt')
        else:
            return Message('Please send me money, mama')

    def Goodbye(self,message):
        self.state = self.finish
        return Message('Goodbye')

if __name__ == "__main__":
    import doctest,sys
    if len(sys.argv) > 1 and sys.argv[-1] != '-v':
        name = sys.argv[-1]
        gb = globals()
        verbose = '-v' in sys.argv 
        doctest.run_docstring_examples(gb[name],gb,verbose,name)
    else:        
        doctest.testmod(optionflags=doctest.ELLIPSIS)
