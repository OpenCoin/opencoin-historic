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
        import urllib2, urllib
        response = urllib2.urlopen(self.url,message.toString(True))
        return createMessage(response.read())
        
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
                    

