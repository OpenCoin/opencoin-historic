import messages,  simplejson, urllib, sys
from pprint import pformat


printmessages = 0

def printMessage(message):
    sys.stderr.write('\n')
    sys.stderr.write('-'*30)
    sys.stderr.write('\n\n')
    sys.stderr.write(pformat(message.getData(1))+'\n')

def printSection(header):
    if printmessages:
        out = """

####################################################################
   %s
####################################################################
        
        """ % header

        sys.stderr.write(out)


def createMessage(data):
    data = dict(simplejson.loads(str(data)))
    header = data['header']
    klass = getattr(messages,header)
    message = klass(data)
    return message

class Transport(object):

    def __call__(self,message):
        return ''

class HTTPTransport(object):
    
    def __init__(self,url):
        self.url = url
     
    def __call__(self,message):
        
        if printmessages:
            printMessage(message)
        
        response = urllib.urlopen(self.url,message.toString(True))
        reply =  createMessage(response.read())
        
        if printmessages:
            printMessage(reply)        
        
        return reply

class TestingHTTPTransport(object):
    
    def __init__(self,port,**kwargs):
        self.port = port
        self.kwargs = kwargs

    def __call__(self,message):
        import testutils
        testutils.run_once(self.port,**self.kwargs)
        transport = HTTPTransport('http://localhost:%s/' % self.port)
        return transport(message)


class BTTransport(object):

    def __init__(self,socket):
        self.stop = '\r\r+++STOP+++\r\r'
        self.lenstop = len(self.stop)
        self.socket = socket
        
    def __call__(self,message):
        self.send(message)
        return self.receive()
   
    def send(self,message):
        self.socket.send(message.toString(True)+self.stop)

    def receive(self):
        line=''
        while not line.endswith(self.stop):
            ch=self.socket.recv(1)
            line += ch

        received = line[:-self.lenstop]
        return createMessage(received)


class DirectTransport(object):

    def __init__(self,target,transport2=None):
        self.target = target
        self.transport2 = transport2

    def __call__(self,message):
    
        if printmessages:
            printMessage(message)
        
        if self.transport2:
            response = self.target(message,self.transport2)
        else:            
            response = self.target(message)
        
        if printmessages:
            printMessage(response)
        
        return response

class YieldTransport(object):

    def __init__(self,targetmethod,args):
        self.args = args
        self.targetmethod = targetmethod
        self.nextarg = None

    def __call__(self,message):
        gen = self.targetmethod(message)
        response = None
        for result in gen:
            if result != None:
                response = result
        return response            
                    
class TestTransport(object):

    def __init__(self, *args):
        self.results = list(args)
        self.debug = 0

    def __call__(self,message):
        if self.debug:
            import pdb; pdb.set_trace()
        result = self.results.pop(0)
        
        if type(result) == list or type(result) == tuple:
            method = result[0]
            args = list(result[1:])
            args.append(message)
            return method(*args)
        
        elif not isinstance(result,messages.Message) and callable(result):
            return result(message)        
        
        else:
            return result

