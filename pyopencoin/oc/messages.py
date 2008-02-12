class Message:
    
    def __init__(self,type=None,data=None,jsontext=None):
        if jsontext:
            self.fromJson(jsontext)
        else:            
            self.type = type
            self.data = data
    
    def __repr__(self):
        return "<Message(%s,%s)>" % (repr(self.type),repr(self.data))

    def toJson(self):
        'serialize to json'

        import json
        return json.write([self.type,self.data])

    def fromJson(self,text):
        'serialize from json'

        import json
        out = json.read(text)
        if len(out) == 2:
            self.type = out[0]
            self.data = out[1]
        return self

    def __eq__(self,other):
        return repr(self)==repr(other)

if __name__ == "__main__":
    import doctest
    doctest.testmod()    

