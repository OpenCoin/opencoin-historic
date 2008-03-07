
"""
We need something way better. Prefereably serializing to Json.

What are the core objects we need to serialize:

Entities
Containers
Keypairs

maybe we should cerealizer, and override methods / supply __getstate__ that follows
the json format?

"""



def serialize(obj):
    import pickle,base64
    return base64.b64encode(pickle.dumps(obj))    


def deserialize(data):
    """
    >>> import tests
    >>> i = tests.makeIssuer()
    >>> s = serialize(i)
    >>> i2 = deserialize(s)
    >>> i2.signedKeys = i.signedKeys
    """
    import pickle,base64
    return pickle.loads(base64.b64decode(data))

import json,entities,containers

"lets write <Class json>"
class MyJsonWriter(json.JsonWriter):
    def _write(self, obj):
        try:
            json.JsonWriter._write(self,obj)
        except json.WriteException:
            if isinstance(obj,entities.Entity) or isinstance(obj,containers.Container):
                self._append("%s %s>" % (str(obj.__class__)[:-1],obj.toJson()))
            else:
                raise WriteException, "Cannot write in JSON: %s" % repr(obj)            
       

class MyJsonReader(json.JsonReader):

    def _read(self):
        self._eatWhitespace()
        peek = self._peek()
        if peek is None:
            raise ReadException, "Nothing to read: '%s'" % self._generator.all()
        if peek == '{':
            return self._readObject()
        elif peek == '[':
            return self._readArray()
        elif peek == '"':
            return self._readString()
        elif peek == '-' or peek.isdigit():
            return self._readNumber()
        elif peek == 't':
            return self._readTrue()
        elif peek == 'f':
            return self._readFalse()
        elif peek == 'n':
            return self._readNull()
        elif peek == '/':
            self._readComment()
            return self._read()
        elif peek == '<':
            self._readClass()
        else:
            raise ReadException, "Input is not valid JSON: '%s'" % self._generator.all()
        

    def _readClass(self):
        pass






if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
