"""
>>> 
>>> 
"""



import simplejson




class Field(object):
    def __init__(self,name,signing=True,default=''):
        self.name = name
        self.signing = signing
        self.default = default

    def getencoded(self,object):
        value = getattr(object,self.name,self.default)
        return value

    def setdecoded(self,object,data):
        setattr(object,self.name,data)

class SubitemField(Field):
    
    def __init__(self,name,signing=True,default='',klass=dict):
        Field.__init__(self,name=name,signing=signing,default=default)
        self.klass = klass


    def getencoded(self,object):
        out = []
        for item in getattr(object,self.name):
            out.append(item.getData())
        return out       
        
    def setdecoded(self,object,data):
        value = []
        for item in data:
            value.append(self.klass(item))
        setattr(object,self.name,value)     

              

class Container(object):   
    fields = []
    def __init__(self,data={}):
        if type(data) == type(''):
            data = simplejson.loads(data)
        if type(data) != type({}):
            data = dict(data)
        for field in self.fields:
            if data.has_key(field.name):
                field.setdecoded(self,data[field.name])
            else:               
                setattr(self,field.name,field.default)
        setattr(self,'signature',data.get('signature',''))
        

    def getData(self,signingOnly=False,signature=False):
        certdata = []
        for field in self.fields:
            if signingOnly and not field.signing:
                continue
            certdata.append((field.name,field.getencoded(self)))
        if signature:
            certdata.append(('signature',self.signature))
        return certdata

    def toString(self,signature=False):
        #encoding stuff should be here as well
        return simplejson.dumps(self.getData(signature=signature))
        


class Token(Container):
    fields = [
        Field('currency'),
        Field('amount')
    ]

class Message(Container):
    fields = [
        Field('subject'),
        SubitemField('tokens',klass=Token)
    ]        
class Tests(object):
     """
    >>> t = Token()
    >>> t.currency='opencent'
    >>> t.amount = 2
    >>> t.toString()
    '[["currency", "opencent"], ["amount", 2]]'
    >>> t.toString(signature=True)
    '[["currency", "opencent"], ["amount", 2], ["signature", ""]]'
    >>> t.getData()
    [('currency', 'opencent'), ('amount', 2)]
    >>> t2 = Token(t.getData())
    >>> t2.getData()
    [('currency', 'opencent'), ('amount', 2)]
    >>> t.signature = 'mysignature'
    >>> t.toString(signature=True)
    '[["currency", "opencent"], ["amount", 2], ["signature", "mysignature"]]'
    >>> m = Message()
    >>> m.subject = 'test'
    >>> m.tokens = [t,t2]
    >>> m.toString()
    '[["subject", "test"], ["tokens", [[["currency", "opencent"], ["amount", 2]], [["currency", "opencent"], ["amount", 2]]]]]'
    >>> m.getData()
    [('subject', 'test'), ('tokens', [[('currency', 'opencent'), ('amount', 2)], [('currency', 'opencent'), ('amount', 2)]])]
    >>> m2 = Message(m.getData())
    >>> m2.getData() == m.getData()
    True
    >>> m2.toString() == m2.toString()
    True
    """


if __name__ == "__main__":
    import doctest,sys
    if len(sys.argv) > 1 and sys.argv[-1] != '-v':
        name = sys.argv[-1]
        gb = globals()
        verbose = '-v' in sys.argv 
        doctest.run_docstring_examples(gb[name],gb,verbose,name)
    else:        
        doctest.testmod(optionflags=doctest.ELLIPSIS)
