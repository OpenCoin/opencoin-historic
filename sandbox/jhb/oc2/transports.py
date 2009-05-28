import messages,  simplejson

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
        import  urllib
        response = urllib.urlopen(self.url,message.toString(True))
        return createMessage(response.read())

import sys

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
        
        if type(result) == type([]) or type(result) == type(()):
            method = result[0]
            args = list(result[1:])
            args.append(message)
            return method(*args)
        
        elif not isinstance(result,messages.Message) and callable(result):
            return result(message)        
        
        else:
            return result

