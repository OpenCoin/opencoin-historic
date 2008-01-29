
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
    >>> import entities
    >>> w = entities.Wallet()
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
    >>> from entities import Wallet
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
    Client <Message('Goodbye',None)>
    Server <Message('Goodbye',None)>
    Client <Message('finished',None)>
    """


    def __init__(self,callback):
        self.callback = callback

    def start(self):
        clienttransport = ClientTestTransport(self)
        self.callback(clienttransport)

    def write(self,message):
        print 'Server', message
        if message.type != 'finished':
            self.other.newMessage(message)


class ClientTestTransport(Transport):
    
    def __init__(self,other=None):
        if other:
            #Lets connect the two
            self.other = other
            other.other = self

    def write(self,message):
        print 'Client', message
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

if __name__ == "__main__":
    import doctest
    doctest.testmod()
