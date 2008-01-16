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

    Create a wallet
    >>> w = Wallet()

    Create http client transport (we want so send via http)
    >>> ct = HTTPClientTransport()

    Connect (does not do anything anyhow)
    >>> ct.connect('http://opencoin.org/testwallet')

    Create a TestingTransport so that we have something to work with
    >>> tt = TestingTransport() 
    >>> tt.connect(ct)
    
    Pass the wallets side transport to the wallet. With sendMoney it will
    immediately start to communicate
    >>> w.sendMoney(ct)

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

######################## Protocolls #########################

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

    def finish(self,message):
        'always the last state. There can be other final states'
        
        return Message('finished')
                    
    def newMessage(self,message):
        'this is used by a transport to pass on new messages to the protocol'

        out = self.state(message)
        self.transport.write(out)
        return out

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

    def __init__(self,wallet):
        self.wallet = wallet
        Protocol.__init__(self)

    def start(self,message):
        self.state=self.Goodbye
        return Message('Receipt')

    def Goodbye(self,message):
        self.state = finish
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
        pass

    def setProtocol(self,protocol):
        "This sets the protocl instance that is used with this transport"
        self.protocol = protocol
        protocol.setTransport(self)

    def connect(self,other):
        """Connect, whatever that means. Could be HTTP, Bluetooth, Local, xmpp"""

    def write(self):
        " The protocol will write into this"

    def newMessage(self,message):
        """Once data has been read (by whatever means) this method is called to 
        put in the new message to deliver it to the protocol"""
        self.protocol.newMessage(message)

 
class SocketTransport(Transport):
    "Something to do everything manually. So much not implemented..."

    def connect(self,port):
        'would open a local socket'

       
class HTTPClientTransport(Transport):
    """To use if the other side is reachable via http.

    >>> import urllib
    >>> t = HTTPClientTransport()
    >>> t.connect('https://opencoin.org/Members/jhb/testresponse')

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

    def connect(self,url):
        self.url = url

    def write(self,message):
        import urllib
        data = message.toJson()
        response = urllib.urlopen(self.url,data).read()
        self.newMessage(Message(jsontext=response))
       
class TestingTransport(Transport):
    """Some tricking around to be able to test other transports. This one 
    connects to another Transport, assuming that we manually read and write
    data, while the other side behaves like a 'real' transport.
    
    Note that on a TestingTransport you have the convinience method of 
    'send'.
    """

    def __init__(self):
        self.messages = []

    def connect(self,otherTransport):
        'This will hook up with another Transport, directly feeding into it'
        
        self.other = otherTransport

        #maybe a bit of a hack?
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


######################## Entities ##################################



class Wallet:
    "Just a testwallet. Does nothing, really"

    def __init__(self):
        self.coins = []

    def sendMoney(self,transport):
        "Sends some money to the given transport."

        protocol = WalletSenderProtocol(self)
        transport.setProtocol(protocol)
        
        #Trigger execution of the protocol
        protocol.newMessage(Message(None))    


#        #return self.getProtocolRunner(protocol,transport)
#   
#    def getProtocolRunner(self,protocol,transport):
#        '''repeatedly get a new message from the transport, stuff it into
#         the protocols state, which outputs a message, send the message back into the 
#         transport, until we actually get a Message('finished') from the protocol'''
#
#        while 1:
#            message = transport.read(1)
#            if not message:
#                message = Message(None)
#            output = protocol.state(message)
#            if output.type in ['finished','failure']:                
#                yield output
#                break
#            else:
#                transport.write(output)
#                yield output
    

def _test():

    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()


