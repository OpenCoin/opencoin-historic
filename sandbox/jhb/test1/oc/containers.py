"""Containers are used to hold all kinds of information, e.g. coins, blanks, certificates,
cdd, etc.

They are required to be transportable in messages. Therefore they should be able to serialize 
to json.

    >>> cdd = CDD(standard_version = 'http://opencoin.org/OpenCoinProtocol/1.0',
    ...           currency_identifier = 'http://opencent.net/OpenCent', 
    ...           short_currency_identifier = 'OC', 
    ...           issuer_service_location = 'opencoin://issuer.opencent.net:8002', 
    ...           denominations = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000], 
    ...           issuer_cipher_suite = ['sha-256', 'rsa', 'rsa'], 
    ...           issuer_public_master_key = 'foobar')
    >>> data = cdd.toPython()
    >>> cdd2 = CDD().fromPython(data)
    >>> cdd2 == cdd
    True
    
    >>> j = cdd.toJson()
    >>> j
    '["http://opencoin.org/OpenCoinProtocol/1.0","http://opencent.net/OpenCent","OC","opencoin://issuer.opencent.net:8002",[1,2,5,10,20,50,100,200,500,1000],["sha-256","rsa","rsa"],"foobar"]'

    >>> cdd3 = CDD().fromJson(j)
    >>> cdd3 = cdd
"""
import json
class Container(object):

    fields = []


    def __init__(self,**kwargs):
        """This would set up the data"""
        for field in self.fields:
            setattr(self,field,kwargs.get(field,None))

    def __repr__(self):
        arguments = ','.join(["%s=%s" %(field,getattr(self,field)) for field in self.fields])
        return "<CDD(%s)>" % arguments

    def __eq__(self,other):
        for field in self.fields:
            if getattr(self,field) != getattr(other,field):
                return False
        return True                

    def toPython(self):
        return [getattr(self,field) for field in self.fields]


    def fromPython(self,data):
        i = 0
        for field in self.fields:
            setattr(self,field,data[i])
            i += 1
        return self        


    def toJson(self):
        return json.write(self.toPython())

    def fromJson(self,text):
        return self.fromPython(json.read(text))
        
        

class CDD(Container):

    fields = ['standard_version', 
              'currency_identifier', 
              'short_currency_identifier', 
              'issuer_service_location', 
              'denominations', 
              'issuer_cipher_suite', 
              'issuer_public_master_key']


    
if __name__ == "__main__":
    import doctest
    doctest.testmod()
