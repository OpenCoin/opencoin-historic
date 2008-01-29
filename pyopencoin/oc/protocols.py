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

    def goodby(self,message):
        return Message('GOODBY')

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
                self.newState(self.goodby)
                return Message('HANDSHAKE_REJECT','did not like the protocol version')
        else:
            return Message('PROTOCOL_ERROR','please do a handshake')


    def dispatch(self,message):        
        self.result = message
        nextprotocol = self.mapping[message.type]
        self.transport.setProtocol(nextprotocol)
        return nextprotocol.newMessage(message)

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


class fetchMintingKeyProtocol(Protocol):
    """
    Used by a wallet to fetch the mints keys, needed when 
    creating blanks
       
    ??? Should it be suitable to fetch more than one denomination at a time?
    Maybe all the keys?

    Lets fetch by denomination

    >>> fmp = fetchMintingKeyProtocol(denomination=2)
    >>> fmp.state(Message(None))
    <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>

    >>> fmp.state(Message('HANDSHAKE_ACCEPT'))
    <Message('MINTING_KEY_FETCH_DENOMINATION',2)>

    >>> fmp.state(Message('MINTING_KEY_PASS','foobar'))
    <Message('GOODBYE',None)>


    And now by keyid

    >>> fmp = fetchMintingKeyProtocol(keyid='abc')
    >>> fmp.state(Message(None))
    <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>

    >>> fmp.state(Message('HANDSHAKE_ACCEPT'))
    <Message('MINTING_KEY_FETCH_KEYID','abc')>

    >>> fmp.state(Message('MINTING_KEY_PASS','foobar'))
    <Message('GOODBYE',None)>


    Lets have some problems a failures (we set the state
    to getKey to resuse the fmp object and save a couple
    of line)

    >>> fmp.newState(fmp.getKey)
    >>> fmp.state(Message('MINTING_KEY_FAILURE',))
    <Message('GOODBYE',None)>
   
    Now lets break something
    
    >>> fmp.newState(fmp.getKey)
    >>> fmp.state(Message('FOOBAR'))
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
            self.keycert = message.data
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
    >>> gmp = giveMintingKeyProtocol(issuer)
    
    >>> gmp.state(Message('HANDSHAKE',{'protocol': 'opencoin 1.0'}))
    <Message('HANDSHAKE_ACCEPT',None)>

    >>> gmp.state(Message('MINTING_KEY_FETCH_DENOMINATION',2))
    <Message('MINTING_KEY_PASS','foobar')>

    >>> gmp.newState(gmp.giveKey)
    >>> gmp.state(Message('MINTING_KEY_FETCH_KEYID','abc'))
    <Message('MINTING_KEY_PASS','foobar')>

    >>> gmp.newState(gmp.giveKey)
    >>> gmp.state(Message('bla','blub'))
    <Message('MINTING_KEY_FAILURE','wrong question')>

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
                self.newState(self.goodby)
                return Message('HANDSHAKE_REJECT','did not like the protocol version')
        else:
            return Message('PROTOCOL_ERROR','please do a handshake')


    def giveKey(self,message):
    
        self.newState(self.goodby)

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
            return Message('MINTING_KEY_PASS',key.toPython)
        else:
            return Message('MINTING_KEY_FAILURE',error)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
