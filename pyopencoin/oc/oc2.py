"""
This some playground for me to understand some of the problems involved in getting
our system working.

This is basically taking Mathews ideas (as far as I understood them), adding a bit of 
my little ideas, and coming to the following idea:

- Protocols that are basically state machines (or workflow engines, me is coming
  from a plone background). So you have a protocol, which has a state and can consume messages.

- Messages are little objects that have a type and carry data. They can serialize themselves,
  e.g. to Json.

- Transports, that bascially reflect one side of a communication. They transport messages,
  and are hooked to protocols. A protocol writes to a transport, and the transport stuffs
  new messages into the the protocol when it gets some.

- Entities like Wallets. These will then do things, as triggered by the gui (no gui yet)

Testing is done by using a TestTransport, which basically can be connected to any other
transport (end) to manually communicate with the other side. Check the TestTransport 
for the use of send instead of write!

This alltogether should allow something along the line of:

    >>> w = Wallet()
    >>> tt = SimpleTestTransport() 
    
    Pass the wallets side transport to the wallet. With sendMoney it will
    immediately start to communicate
    >>> w.sendMoney(tt)

    See, it sends us (we are the other side, pretending to be a wallet
    receiving money) a message. These are no real messages at all
    >>> tt.read()
    <Message('sendMoney',[1, 2])>
    
    Any new messages, after we have been doing nothing?
    >>> tt.read()

    Nope, there weren't. Lets send some nonsense
    >>> tt.send('foobar')
    <Message('Please send a receipt',None)>

    Ok, the protocol does not like other message, but wanted us
    to send a receipt. If it insists...
    >>> tt.send('Receipt')
    <Message('Goodbye',None)>
    
   This was so fun, lets see if we can do some more?
    >>> tt.send('Another receipt')
    <Message('finished',None)>

    Ok, we are done
    
"""
#This is needed for the file to run on s60 
from __future__ import generators

# we also import json and urllib somewhere else in the file. We could do it 
# here, but s60 might slow down with unnecessary imports

######################## Protocols #########################

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


class Protocol:
    
    def __init__(self):
        'Set the initial state'
        
        self.state = self.start

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
    >>> issuer = None
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
            except:                
                error = 'no key for that denomination available'
        
        elif message.type == 'MINTING_KEY_FETCH_KEYID':                
            try:
                key = self.issuer.getKeyById(message.data)                
            except:                
                error = 'no such keyid'
        
        else:
            error = 'wrong question'

        if not error:            
            return Message('MINTING_KEY_PASS',key.toPython)
        else:
            return Message('MINTING_KEY_FAILURE',error)

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

########################## Messages ##############################

class Message:
    
    def __init__(self,type=None,data=None,jsontext=None):
        if jsontext:
            self.fromJson(jsontext)
        else:            
            self.type = type
            self.data = data
    
    def __repr__(self):
        return "<Message(%s,%s)>" % (repr(self.type),repr(self.data))

    def toJson(self):
        'serialize to json'

        import json
        return json.write([self.type,self.data])

    def fromJson(self,text):
        'serialize from json'

        import json
        out = json.read(text)
        if len(out) == 2:
            self.type = out[0]
            self.data = out[1]
        return self
    
############################# Transports ####################################

"""A transport has a write method, to which the protocol sends new data. The 
   transport send of this data, and delivers the response (or new data without
   a prior 'write') to the protocols newMessage method.

   This means that the protocol must be happy to be fed newMessages at any
   point in time.
  
   """


class Transport:

    def __init__(self):
        "Constructor. Override this"

    def setProtocol(self,protocol):
        "This sets the protocl instance that is used with this transport"
        self.protocol = protocol
        protocol.setTransport(self)

    def write(self,message):
        " The protocol will write into this"

    def newMessage(self,message):
        """Once data has been read (by whatever means) this method is called to 
        put in the new message to deliver it to the protocol"""
        self.protocol.newMessage(message)

    def start(self):
        """start the transport"""


class SocketServerTransport(Transport):
    """ No idea how to test this with a doctest

        So, please run testWalletServer.py then testClientServer.py in different 
        shells

    """
    def __init__(self,addr,port):
        self.addr = addr
        self.port = port
        self.debug = 0

    def start(self):
        """This is a prove that I have no  understanding of sockets. Whats
        a socket, whats a conn, when is it open, when closed?"""

        import socket
        self.runserver = 1
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        s.bind((self.addr, self.port))
        s.listen(1)
        self.socket = s
        self.init_conn()
        while self.runserver:
            data = self.conn.recv(2048)
            if len(data) == 0:
                self.init_conn()
                data = self.conn.recv(2048)
            data  = data.replace('\r','')
            try:
                m = Message(jsontext=data)
                self.newMessage(m)
            except Exception, e:
                try:
                    self.write(Message('WrongFormat',str(e)))
                except:
                    pass
        self.conn.close()

    def init_conn(self):
        conn, addr = self.socket.accept()
        self.conn = conn
        return conn

    def write(self,message):
        if self.debug:
            print message
        self.conn.send(message.toJson())
        if message.type == 'finished':
            self.conn.close()
           
            self.runserver = 0
            self.socket.close()
            #self.init_conn()
            #self.protocol.state = self.protocol.start


class SocketClientTransport(Transport):
    'Commented out while offline'
    """
    >>> w = Wallet()
    >>> sct = SocketClientTransport('copycan.org',12008)
    >>> w.sendMoney(sct)

    """
    def __init__(self,addr,port):
        self.addr = addr
        self.port = port
        self.debug = 0

    def start(self):
        import socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.addr, self.port))
        
    def write(self,message):   
        self.socket.send(message.toJson())
        if message.type == 'finished':
            self.socket.close()
            return
        else:            
            data = self.socket.recv(2048)
            if self.debug:
                print message
            self.newMessage(Message(jsontext=data))
            
        

class HTTPClientTransport(Transport): 
    'doctest disabled while offline'
    """To use if the other side is reachable via http.

    >>> import urllib
    >>> t = HTTPClientTransport('https://opencoin.org/Members/jhb/testresponse')

    This is for testing only
    >>> t.messages = []
    >>> t.newMessage = t.messages.append 

    Now write a message
    >>> m = Message('TestMessage',{'foo':'bar'})
    >>> t.write(m)

    Look what we've got
    >>> t.messages[0]
    <Message('TestResponse',{'everything': 'good'})>
    """

    def __init__(self,url):
        self.url = url

    def write(self,message):
        import urllib
        data = message.toJson()
        response = urllib.urlopen(self.url,data).read()
        self.newMessage(Message(jsontext=response))

class SimpleTestTransport(Transport):
    """
    >>> w = Wallet()
    >>> st = SimpleTestTransport()
    >>> w.sendMoney(st)
    >>> st.send('foo')
    <Message('sendMoney',[1, 2])>
    """
    def __init__(self):
        self.messages = []
        self.write = self.messages.append

    def read(self):
        'return one buffered message. Returns None if there are not any'
        if self.messages:
            return self.messages.pop(0)
        else:
            return None

        
    def send(self,type,data=None):
        """a shortcut for doing 
         
          transport.write(Message("foo",[somedata,..]))
          transport.read()
        
        instead just 

          transport.send("foo",[somedata,...])"""

        self.newMessage(Message(type,data))
        return self.read()
      
class TestingTransport(Transport):
    """
    # This class does nothing good right now, pretty much ignore it #
    
    Some tricking around to be able to test other transports. This one 
    connects to another Transport, assuming that we manually read and write
    data, while the other side behaves like a 'real' transport.
    
    Note that on a TestingTransport you have the convinience method of 
    'send'.

    >>> w = Wallet()
    >>> ct = HTTPClientTransport('http://opencoin.org/testwallet')

    >>> tt = TestingTransport() 
    >>> tt.connect(ct)
    
    >>> w.sendMoney(ct)
    >>> tt.read()
    <Message('sendMoney',[1, 2])>
    
    >>> tt.read()

    >>> tt.send('foobar')
    <Message('Please send a receipt',None)>

    >>> tt.send('Receipt')
    <Message('Goodbye',None)>
    
    >>> tt.send('Another receipt')
    <Message('finished',None)>

    """

    def __init__(self):
        self.messages = []

    def connect(self,otherTransport):
        'This will hook up with another Transport, directly feeding into it'
        
        self.other = otherTransport

        #Just a hack, does nothing clever yet. Instead of replacing the write,
        #it should do something that actually uses it. Now idea yet how to do
        # it
        self.other.write = self.newMessage

    def write(self,message):
        'directly pass on the message to the other transport'

        self.other.newMessage(message)

    def send(self,type,data=None):
        """a shortcut for doing 
         
          transport.write(Message("foo",[somedata,..]))
          transport.read()
        
        instead just 

          transport.send("foo",[somedata,...])"""

        self.write(Message(type,data))
        return self.read()

    def newMessage(self,message):
        'We store messages, so that we than can read them'
        self.messages.append(message)

    def read(self):
        'return one buffered message. Returns None if there are not any'
        if self.messages:
            return self.messages.pop(0)
        else:
            return None

    def send(self,type,data=None):
        """a shortcut for doing 
         
          transport.write(Message("foo",[somedata,..]))
          transport.read()
        
        instead just 

          transport.send("foo",[somedata,...])"""

        self.write(Message(type,data))
        return self.read()


######################## Entities ##################################



class Wallet:
    "Just a testwallet. Does nothing, really"

    def __init__(self):
        self.coins = []

    def sendMoney(self,transport):
        "Sends some money to the given transport."

        protocol = WalletSenderProtocol(self)
        transport.setProtocol(protocol)
        transport.start()        
        #Trigger execution of the protocol
        protocol.newMessage(Message(None))    

    def receiveMoney(self,transport):
        protocol = WalletRecipientProtocol(self)
        transport.setProtocol(protocol)
        transport.start()


    

def _test():

    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()


