from __future__ import generators

######################## Protocolls #########################

class Protocol:
    
    def __init__(self):
        self.state = self.start

    def start(self,message):
       pass

    def finish(self,message):
        return Message('finished')
                    


class WalletSenderProtocol(Protocol):
    """
    >>> sp = WalletSenderProtocol(None)
    >>> rp = WalletRecipientProtocol(None)
   
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
        self.wallet = wallet
        Protocol.__init__(self)

    def start(self,message):
        self.state = self.waitForReceipt
        return Message('sendMoney',[1,2])

    def waitForReceipt(self,message):
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


class Message:
    
    def __init__(self,type,data=None):
        self.type = type
        self.data = data
    
    def __repr__(self):
        return "<Message(%s,%s)>" % (repr(self.type),repr(self.data))

    
############################# Transports ####################################

"""Idea: there are always two transports involved when two entities communicate,
   both respresenting the ends of a transport channel. For testing we give
   the tested entity a 'real' transport, and use ourselves a dummy transport
   
   a transport gets connected to a protocols message handler, the protocol is
   connected to the entity"""


class DummyTransport:
    """
    >>> sp = WalletSenderProtocol(None)
    >>> t = DummyTransport(sp)

    It starts with sending some money
    >>> t.newMessage(Message(None))
    <Message('sendMoney',[1, 2])>
    
    >>> t.newMessage(Message('Foo'))
    <Message('Please send a receipt',None)>

    Lets give it a receipt
    >>> t.newMessage(Message('Receipt'))
    <Message('Goodbye',None)>

    >>> t.newMessage(Message('Bla'))
    <Message('finished',None)>

    >>> t.newMessage(Message('Bla'))
    <Message('finished',None)>

    """
    def __init__(self,protocol):
        self.protocol = protocol

    def newMessage(self,message):
        return self.protocol.state(message)

class TestTransport:
    
    def __init__(self,messages=[]):
        self.messages = []
        self.add2Messages(messages)

    def add2Messages(self,messages):
        new = [Message(m) for m in messages]
        self.messages.extend(new)


    def read(self,onlyone=0):
        if not self.messages:
            return None
        elif onlyone:
            return self.messages.pop(0)
        else:
            messages = self.messages
            self.messages = []
            return messages

    def write(self,message):
        '''not needed, because we access the protocolRunner directly, never readin
        out what the protocol wrote back'''
        pass

######################## Entities ##################################



class Wallet:

    def __init__(self):
        self.coins = []

    def sendMoney(self,transport):
        """Send some money to the other wallet on transport
        >>> w = Wallet()
        >>> t = TestTransport()
        >>> output = w.sendMoney(t)

        >>> output.next()
        <Message('sendMoney',[1, 2])>

        >>> output.next()
        <Message('Please send a receipt',None)>

        >>> output.next()
        <Message('Please send a receipt',None)>

        >>> t.add2Messages(['Receipt'])
        >>> output.next()
        <Message('Goodbye',None)>
        
        >>> output.next()
        <Message('finished',None)>

        """
        protocol = WalletSenderProtocol(self)
        return self.getProtocolRunner(protocol,transport)
   
    def getProtocolRunner(self,protocol,transport):
        '''repeatedly get a new message from the transport, stuff it into
         the protocols state, which outputs a message, send the message back into the 
         transport, until we actually get a Message('finished') from the protocol'''

        while 1:
            message = transport.read(1)
            if not message:
                message = Message(None)
            output = protocol.state(message)
            if output.type in ['finished','failure']:                
                yield output
                break
            else:
                transport.write(output)
                yield output
    

def _test():

    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()


