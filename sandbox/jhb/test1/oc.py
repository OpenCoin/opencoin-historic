from __future__ import generators
from parsing import decodeHumanReadable,encodeHumanReadable
import json, md5


class Container(object):
    
    elements = ()
    signature = (None,None)

    def __init__(self,**kwargs):
        for element in self.elements:
            if kwargs.has_key(element):
                setattr(self,element,kwargs[element])

    def decodeHR(self,text):
        data = self._decodeData(text)
        for key,value in data:
            if key in self.elements:
                setattr(self,key,value)

    def encodeHR(self):
        content = self.getContentPart()
        signature_lines = [['signature',self.signature[1]]]
        return "{\n%s\n%s}" % (content,self._encodeData(signature_lines))

    def getContentPart(self):
        return self._encodeData(self.getData())

    def getData(self):
        return [(element,getattr(self,element)) for element in self.elements]

    def _encodeData(self,data):
        m = max([len(l[0]) for l in data])
        format = (" %%-%ss = %%s" % m)
        out = []
        for l in data:
            out.append(format % (l[0].replace('_',' '),l[1]))
            out.append('\n')
        return ''.join(out)

    def _decodeData(self,text):
        tmp = [line.strip() for line in text.strip().split('\n')]
        tmp = tmp[tmp.index('{')+1:tmp.index('}')]
        tmp = [[e.strip() for e in line.split(' = ')] for line in tmp if line]
        tmp = [[l[0].replace(' ','_'),l[1]] for l in tmp]
        return tmp


                 
    def sign(self,key):
        self.signature = (md5.new(key).hexdigest(),
                          md5.new(self.getContentPart()).hexdigest())
        return self.signature
        

class CurrencyDescriptionDocument(Container):
    """
    set up a cdd:

    >>> cdd = CurrencyDescriptionDocument(
    ...  standard_version          = 'http://opencoin.org/OpenCoinProtocol/1.0',
    ...  currency_identifier       = 'http://opencent.net/OpenCent',
    ...  short_currency_identifier = 'OC',
    ...  issuer_service_location   = 'opencoin://issuer.opencent.net:8002',
    ...  denominations             = '(1, 2, 5, 10, 20, 50, 100, 200, 500, 1000)',  #list of strings seperated by commas
    ...  issuer_cipher_suite       = 'HASH-ALG, SIGN-ALG, BLINDING-ALG',
    ...  issuer_public_master_key  = 'acbd18db4cc2f85cedef654fccc4a4d8')

    >>> cdd.standard_version
    'http://opencoin.org/OpenCoinProtocol/1.0'

    sign the cdd
    >>> cdd.sign('foo')
    ('acbd18db4cc2f85cedef654fccc4a4d8', '68bc78932e3c1cc5d99e1bbc0d527f46')

    check if the encoding still works
    >>> text = cdd.encodeHR()
    >>> cdd.decodeHR(text)
    >>> text2 = cdd.encodeHR()
    >>> text == text2
    True

    """

    elements =  ('standard_version', 
                 'currency_identifier', 
                 'short_currency_identifier', 
                 'issuer_service_location', 
                 'denominations', 
                 'issuer_cipher_suite', 
                 'issuer_public_master_key')


class Message:
    """
    Setup a message

        >>> m = Message('TESTMESSAGE',dict(foo='bar'))

    Check if encoding is roundtrip

        >>> text = m.encode()
        >>> m.decode(text) #doctest: +ELLIPSIS
        <__main__.Message instance at 0x...>
        >>> text2 = m.encode()
        >>> text == text2
        True

    and if the data is still valid

        >>> m.type
        'TESTMESSAGE'

        >>> m.data
        {'foo': 'bar'}
    """
    def __init__(self,type=None,data=None):
        self.type = type
        self.data = data

    def encode(self):
        return json.write([self.type,self.data])

    def decode(self,text):
        out = json.read(text)
        if len(out) == 2:
            self.type = out[0]
            self.data = out[1]
        return self            



class Wallet:
    """T
    >>> t1 = TestTransport()
    >>> t2 = TestTransport()
    >>> t1.connect(t2)
    >>> w1 = Wallet()
    >>> w2 = Wallet()
    >>> w1.connect(t1)
    >>> w2.connect(t2)
    >>> w1.sendMoney()
    >>> w2.receiveMoney()
    >>> w1.transport.receive()[0].type
    'Received'
    
    """

    def connect(self,transport):
        self.transport = transport

    def sendMoney(self):
        self.transport.send('ONE',1)

    def receiveMoney(self):
        messages = self.transport.receive()
        self.transport.send('Received',messages[0].data)

    def testProtocol(self):
        out = None
        while not out:
            yield 'foo'


class Protocoll:


    def write(self,type,data):
        pass
    
    def read(self):
        pass

class WalletSendMoney(Protocoll):

    def __init__(self):
        self.states = {'start':[self.sendmoney,self.abort]}
        self.state=None

    def sendmoney(self):
        self.state = 'waitforreceipt'
        return ('SENDMONEY',[1,2])

    def yourreceipt(self):
        receipt = self.read()
        return ('OK')

    def abot(self):
        self.state = 'aborted'
        
class WalletGetMoney(Protocoll):
    
    def __init__(self):
        self.states = {'start':[self.hello,self.abort]}
        self.state=None

    def start(self):
        self.write('HELLO')
        self.read()
                
    def abort(self):
        self.state = 'aborted'


class Proto2:
    
    def __init__(self):
        self.state = self.start

    def start(self,message):
       pass

    def finish(self,message):
        return Message('finished')


class WalletSender(Proto2):

    def start(self,message,data):
        self.state = self.waitForReceipt
        return Message('sendMoney',[1,2])

    def waitForReceipt(self,message,data):
        if message == 'Receipt':
            self.state=self.finish
            return Message('Goodbye')
        else:
            return Message('Please send a receipt')



class WalletRecipient(Proto2):

    def start(self,message,data):
        self.state=self.finish
        return Message('Receipt')

    def Goodbye(self,message,data):
        self.state = finish
        return Message('Goodbye')


class Message2:
    
    def __init__(self,type,data=None):
        self.type = type
        self.data = data

def test_wallets():
    """
    
    >>> ws = WalletSender()
    >>> wr = WalletRecipient()
    >>> m1 = ws.state(None,None)
    >>> m2 = wr.state(*m1)
    >>> m3 = ws.state(*m2)
    >>> m3
    """



class Transport:

    def send(self,type,data):
       return ''

    def receive(self):
        return ''

class TestTransport(Transport):

    def __init__(self):
        self.readbuffer = []

    def connect(self,other): 
        self.other = other
        other.other = self

    def send(self,type,data):
        self.other.readbuffer.append(Message(type,data).encode())
     
    def receive(self):
        messages = [Message().decode(m) for m in self.readbuffer]
        self.readbuffer = []
        return messages

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()


