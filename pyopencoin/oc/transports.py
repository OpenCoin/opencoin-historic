
"""A transport has a write method, to which the protocol sends new data. The 
   transport send of this data, and delivers the response (or new data without
   a prior 'write') to the protocols newMessage method.

   This means that the protocol must be happy to be fed newMessages at any
   point in time.
  
   """
from messages import Message

class Transport:

    def __init__(self):
        "Constructor. Override this"

    def setProtocol(self,protocol):
        "This sets the protocol instance that is used with this transport"
        self.protocol = protocol
        protocol.setTransport(self)

    def write(self,message):
        "The protocol will write into this"

    def newMessage(self,message):
        """Once data has been read (by whatever means) this method is called to 
        put in the new message to deliver it to the protocol"""
        if message:
            self.protocol.newMessage(message)

    def start(self):
        """start the transport"""

class SocketServerHandler:
    """SocketServerHandler accepts connections on a socket, makes a SocketServerTransport, and feeds the transport to function."""
    def __init__(self, addr, port, function):
        self.addr = addr
        self.port = port
        self.debug = False
        self.function = function

    def start(self):

        import socket
        self.runserver = True
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.addr, self.port))
        s.listen(5)
        self.socket = s

        while self.runserver:
            incoming_sock, incoming_addr = self.socket.accept()
            sst = SocketServerTransport(incoming_sock, self.debug)

            # TODO: Add in ability to use select, or spawn off a thread, or something

            self.function(sst)
            


class SocketServerTransport(Transport):
    """ No idea how to test this with a doctest

        So, please run testWalletServer.py then testClientServer.py in different 
        shells

    """
    def __init__(self, sock, debug=False):
        self.conn = sock
        self.debug = debug

    def start(self):

        read = ''
        data = self.conn.recv(2048)
        while data:
            data  = data.replace('\r','')
            read = read + data
                
            # Read through, trying to find a full message.
            position = 0
            found = 0
            quotes = False
            braces = 0
            for c in read:
                if c == '"':
                    quotes = not quotes

                elif c == '[':
                    if not quotes:
                        braces = braces + 1

                elif c == ']':
                    if not quotes:
                        braces = braces - 1
                        if braces == 0:
                            found = position
                            break

                position = position + 1

            if found:
                try:
                    m = Message(jsontext=read[:found + 1])
                except Exception, e:
                    raise
                else:
                    read = read[found + 1:]

                try:
                    if self.debug:
                        print m
                    self.newMessage(m)
                except Exception, e:
                    raise


            # The socket may already be closed. Check.
            if not self.conn:
                break

            # read more information
            data = self.conn.recv(2048)

        # No more data, the connection is closed. Close the socket
        if self.conn:
            self.conn.close()

        # TODO: Somehow signal death. Remove ourselves from a select or kill the thread?

    def write(self,message):
        if self.debug:
            print message

        if message:
            self.conn.send(message.toJson())

        if self.protocol.done:
            self.conn.close()
            self.conn = None
           

class SocketClientTransport(Transport):
    """
    >>> import entities
    >>> #w = entities.Wallet()
    >>> #sct = SocketClientTransport('copycan.org',12008)
    >>> #w.sendMoney(sct)

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
        if message:
            self.socket.send(message.toJson())

        if message.type == 'GOODBYE': # FIXME: We need to use the protocol stuff, or somehow know what we mean to do.
            self.socket.close()
            self.socket = None
            return
        
        else:            
            print 'Message.type: %s' % message.type
            read = ''
            data = self.socket.recv(2048)
            while data:
                data = data.replace('\r','')
                read = read + data
                
                # Read through, trying to find a full message.
                position = 0
                found = 0
                quotes = False
                braces = 0
                for c in read:
                    if c == '"':
                        quotes = not quotes

                    elif c == '[':
                        if not quotes:
                            braces = braces + 1

                    elif c == ']':
                        if not quotes:
                            braces = braces - 1
                            if braces == 0:
                                found = position
                                break

                    position = position + 1

                if found:
                    try:
                        m = Message(jsontext=read[:found + 1])
                    except Exception, e:
                        raise
                    else:
                        # Remove the message from read
                        read = read[found + 1:]

                    try:
                        if self.debug:
                            print m
                        self.newMessage(m)
                    except Exception, e:
                        raise

                    #FIXME: We need to restart looking for messages if we had found it!

                # read more information
                if self.socket:
                    data = self.socket.recv(2048)
                else:
                    data = ''

        

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
    >>> from entities import Wallet
    >>> w = Wallet()
    >>> st = SimpleTestTransport()
    >>> w.sendMoney(st)
    >>> st.send('foo')
    <Message('sendMoney',[1, 2])>
    """
    def __init__(self):
        self.messages = []

    def write(self,message):
        if message:
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

        self.newMessage(Message(type,data))
        return self.read()


################# These two are for real testing ######################

class ServerTest(Transport):
    
    def __init__(self, other=None, autocontinue=1, autoprint='message'):
        self.buffer = None
        self.autocontinue = autocontinue
        self.autoprint = autoprint
        self.log = []

        if other:
            #Lets connect the two
            self.other = other
            other.other = self

    def write(self,message):
        if message:
            l = '%s %s' % (self.nick, message)
            if self.autoprint == 'message':
                print '%s %s' % (self.nick, message)
            elif self.autoprint == 'json':
                print '%s: %s' % (self.nick, message.toJson())
                
            self.log.append((self.nick,message))
            if message.type != 'finished':
                if self.autocontinue: 
                    #print 'transport'
                    self.other.newMessage(message)
                else:
                    self.buffer = message

    def next(self):
        if self.buffer:
            m = self.buffer
            self.buffer = None
            self.other.newMessage(m)
    

    def printlog(self):
        print '\n'.join(['%s: %s' % (l[0],l[1].toJson()) for l in self.log])
            

class ClientTest(ServerTest):
    """
    >>> from entities import Wallet
    >>> client = Wallet()
    >>> server = Wallet()
    >>> t = ClientTest(server.receiveMoney,clientnick='walletA',servernick='walletB')
    >>> client.sendMoney(t)
    walletA <Message('sendMoney',[1, 2])>
    walletB <Message('Receipt',None)>
    walletA <Message('GOODBYE',None)>
    walletB <Message('GOODBYE',None)>



    """
        
    def __init__(self, callback, clientnick=None, servernick=None, autocontinue=1, autoprint='message', **kwargs):
        self.callback = callback
        self.kwargs = kwargs
        self.nick=clientnick or 'Client'
        self.servernick = servernick or 'Server'
        self.log = []

        self.autocontinue = autocontinue
        self.buffer = None
        self.autoprint = autoprint

    def start(self):
        servertransport = ServerTest(self,autoprint=self.autoprint)
        servertransport.nick = self.servernick
        kwargs = self.kwargs
        self.callback(servertransport,**kwargs)

   
class SocketClientTest(Transport):

    """
    >>> from entities import Wallet
    >>> client = Wallet()
    >>> server = Wallet()
    >>> t = SocketClientTest('127.0.0.1',3456,server.receiveMoney)
    >>> #client.sendMoney(t)


    """


    def __init__(self,addr,port,callback,**kwargs):
        self.kwargs = kwargs
        self.addr = addr
        self.port = port
        self.callback = callback
        self.debug = 1
        
    def start(self):
        # Okay. This doesn't work for a few reasons.
        # servertransport gets set up as the transport to use. The socket is not opened at this time though.
        servertransport = SocketServerTransport(self.addr,self.port)
        
        # We try to connect to the socket. It fails becuase the socket isn't open
        import socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.addr, self.port))

        # We never get here.
        kwargs = self.kwargs
        self.callback(servertransport,**kwargs)

        # Okay. To fix this, we have to do a few things. ServerSocketTransport is written using blocking
        # sockets. And it never yields. That means that once we start a ServerSocketTransport, or a 
        # SocketClientTest we never give back control for the other side. It works great with tests using
        # different python instances or threads. It doesn't work, however if we don't have those things
        # setup to use.

        # Now, to fix this, you can stick a SocketServerTransport in it's own thread. Once you set it off,
        # it should work find. However, to make sure you don't do anything weird, add a timeout to the
        # socket on listen and remove the loop, so it doens't continue forever. And also, you should
        # probably throw in something to make sure the thread is closed before you can continue, if python
        # allows things like that.

        # - Mathew
        
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



######################### old stuff #############################################

class ServerTestTransport(Transport):
    """ 
    This is really really weird. We test two entities,
    they write to each other, and we can see the whole
    conversation. 

    XXX need a way to inject somewhere....
    maybe if we had a servertransport.test(server.callback) method
    that would yield every so often...

    >>> from entities import Wallet
    >>> client = Wallet()
    >>> server = Wallet()
    >>> t = ServerTestTransport(client.sendMoney)
    >>> server.receiveMoney(t)
    Client <Message('sendMoney',[1, 2])>
    Server <Message('Receipt',None)>
    Client <Message('GOODBYE',None)>
    Server <Message('GOODBYE',None)>
    """

    def __init__(self,callback,**kwargs):
        self.callback = callback
        self.kwargs = kwargs
        self.log = []

    def start(self):
        clienttransport = ClientTestTransport(self)
        kwargs = self.kwargs
        self.callback(clienttransport,**kwargs)

    def write(self,message):
        if message:
            l = 'Server %s' % message 
            print l
            self.log.append(l)
            if message.type != 'finished':
                #print 'transport'
                self.other.newMessage(message)

    def printlog(self):
        print '\n'.join(self.log)

class ClientTestTransport(Transport):
    
    def __init__(self,other=None):
        if other:
            #Lets connect the two
            self.other = other
            other.other = self

    def write(self,message):
        if message:
            l = 'Client %s' %message
            print l
            self.other.log.append(l)
            if message.type != 'finished':
                #print 'transport'
                self.other.newMessage(message)


class ServerTestTransport2(Transport):
    """ 
    
    >>> from entities import Wallet
    >>> client = Wallet()
    >>> server = Wallet()
    >>> t = ServerTestTransport2(client.sendMoney)
    >>> server.receiveMoney(t)
    >>> ct = t.clienttransport
    >>> m = ct.buffer
    >>> m
    <Message('sendMoney',[1, 2])>

    >>> t.newMessage(m)
    >>> m2 = t.buffer
    >>> m2
    <Message('Receipt',None)>

    XXX in the end the ServerTestTransport could be simplified - it
    does not really need the client on the other side. 

    >>> w2 = Wallet()
    >>> tt = SimpleTestTransport()
    >>> w2.listen(tt)
   
    XXX All nice, but how do I get the listen method to switch after the handshake?
    """

    def __init__(self,callback):
        self.callback = callback
        self.buffer = None

    def start(self):
        self.clienttransport = ClientTestTransport2(self)
        self.callback(self.clienttransport)

    def write(self,message):
        self.buffer = message
        return
        if message.type != 'finished':
            self.other.newMessage(message)


class ClientTestTransport2(Transport):
    
    def __init__(self,other=None):
        if other:
            #Lets connect the two
            self.other = other
            other.other = self
        self.buffer = None

    def write(self,message):
        self.buffer = message
        return
        if message.type != 'finished':
            self.other.newMessage(message)



#Server will call start on the transport
#Should trigger client to start
#client writes message





class TestingTransport(Transport):
    """
    # This class does nothing good right now, pretty much ignore it #
    
    Some tricking around to be able to test other transports. This one 
    connects to another Transport, assuming that we manually read and write
    data, while the other side behaves like a 'real' transport.
    
    Note that on a TestingTransport you have the convinience method of 
    'send'.

    >>> from entities import Wallet
    >>> w = Wallet()
    >>> ct = HTTPClientTransport('http://opencoin.org/testwallet')

    >>> tt = TestingTransport() 
    >>> tt.connect(ct)
    
    >>> w.sendMoney(ct)
    >>> tt.read()
    <Message('sendMoney',[1, 2])>
    
    >>> tt.read()

    >>> #tt.send('foobar')
    <Message('PROTOCOL_ERROR','send again')>

    >>> tt.send('Receipt')
    <Message('GOODBYE',None)>

    >>> tt.send('Another receipt')

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

if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
