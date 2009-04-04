import simplejson, datetime, binascii

################################### Fields ##################################

class Field(object):
    def __init__(self,name,signing=True,default=''):
        self.name = name
        self.signing = signing
        self.default = default

    def getencoded(self,object,allData=False):
        value = getattr(object,self.name,self.default)
        return value

    def setdecoded(self,object,data):
        setattr(object,self.name,data)

class DateField(Field):

    format = '%d.%m.%Y %H:%M:%S'

    def getencoded(self,object,allData=False):
        value = getattr(object,self.name,self.default)
        if not value:
            value = datetime.datetime.now()
        return value.strftime(self.format)

    def setdecoded(self,object,data):
        dt = datetime.datetime.strptime(data,self.format)
        setattr(object,self.name,dt)

        

class BinaryField(Field):
    
    def getencoded(self,object,allData=False):
        value = getattr(object,self.name,self.default)
        return binascii.b2a_base64(value).strip()

    def setdecoded(self,object,data):
        setattr(object,self.name,binascii.a2b_base64(data))
     
    
class OneItemField(Field):
    
    def __init__(self,name,signing=True,default='',klass=dict):
        Field.__init__(self,name=name,signing=signing,default=default)
        self.klass = klass


    def getencoded(self,object,allData=False):
        value = getattr(object,self.name)
        if value:
            value = value.getData(allData=allData)
        else:
            value = self.default
        return  value
        
    def setdecoded(self,object,data):
        #import pdb; pdb.set_trace()
        setattr(object,self.name,self.klass(data))




class SubitemsField(Field):
    
    def __init__(self,name,signing=True,default='',klass=dict):
        Field.__init__(self,name=name,signing=signing,default=default)
        self.klass = klass


    def getencoded(self,object,allData=False):
        out = []
        for item in getattr(object,self.name):
            if item == None:
                out.append('')
            else:                
                out.append(item.getData(allData=allData))
        return out       
        
    def setdecoded(self,object,data):
        value = []
        for item in data:
            if item == '':
                value.append(None)
            else:
                value.append(self.klass(item))
        setattr(object,self.name,value)     


################################### Containers ##################################
              

class Container(object):   
    
    fields = []

    def __init__(self,data={}):
        self.fromData(data)

    def __xrepr__(self):
        return "<%s(%s)>" % (self.__class__.__name__,self.getData(True))

    def __xstr__(self):
        return self.toString()

    def fromData(self,data):

        if data == None:
            return

        if type(data) == type(''):
            data = simplejson.loads(data)

        if type(data) != type({}):
            data = dict(data)
        for field in self.fields:
            if data.has_key(field.name):
                field.setdecoded(self,data[field.name])
            else:               
                setattr(self,field.name,field.default)


    def getData(self,allData=False):
        certdata = []
        for field in self.fields:
            if not (allData or field.signing):
                continue
            certdata.append((field.name,field.getencoded(self,allData=allData)))
        return certdata

    def toString(self,allData=False):
        return simplejson.dumps(self.getData(allData=allData))


