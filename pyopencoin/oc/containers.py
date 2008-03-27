import base64
import json
import types

class Container(object):
    r"""A generic container, handles serializing
    
    >>> c = Container(foo='foo',bar='bar')
    
    Accessing c.foo should not work, as the container has no
    infos about its fields

    >>> c.foo
    Traceback (most recent call last):
    ...      
    AttributeError: 'Container' object has no attribute 'foo'
    
    Lets try again:
    >>> Container.fields = ['foo','bar']
    >>> c = Container(foo='foo',bar='bar')
    >>> c
    <Container(foo='foo',bar='bar')>

    Serialize human readable - its actually json. 
    >>> c.content_part()
    '[["foo","foo"],["bar","bar"]]'

    Serialize to json
    >>> j = c.toJson()
    >>> j
    '[["foo","foo"],["bar","bar"]]'

    Lets deserialize
    >>> c = Container()
    >>> c
    <Container(foo=None,bar=None)>
    
    >>> c.fromJson(j)
    <Container(foo='foo',bar='bar')>
    
    >>> c
    <Container(foo='foo',bar='bar')>

    Add a codec for bar
    >>> c.codecs['bar'] = {'encode':base64.encodestring,'decode':base64.decodestring}
   
    Lets look at the json now
    >>> j2 = c.toJson()
    >>> j2 
    '[["foo","foo"],["bar","YmFy\\n"]]'
    
    >>> c.fromJson(j2)
    <Container(foo='foo',bar='bar')>
    """

    fields = []
    codecs = {}
    content_id = 'Container'
    
    def __init__(self,**kwargs):
        """This would set up the data"""

        for field in self.fields:
            setattr(self,field,kwargs.get(field,None))
        self.content_id = self.__class__.__name__      

    def __repr__(self):
        arguments = ','.join(["%s=%s" %(field,repr(getattr(self,field))) for field in self.fields])
        return "<%s(%s)>" % (self.__class__.__name__,arguments)

    def __str__(self):
        return self.toJson()

    def encodeField(self,fieldname):
        '''returns the value of field in whatever string represnation'''

        encoder = self.codecs.get(fieldname,{}).get('encode',lambda x: x)
        return encoder(getattr(self,fieldname))

    def decodeField(self,fieldname,text):
        '''returns the value of field in whatever string represnation'''

        decoder = self.codecs.get(fieldname,{}).get('decode',lambda x: x)
        return decoder(text)        

    def setCodec(self,fieldname,encoder=None,decoder=None):

        donothing = lambda x: x
        if not encoder:
            encoder = donothing
        if not decoder:
            decoder = donothing
        
        self.codecs[fieldname] = {'encode':encoder,'decode':decoder}

    def toPython(self, extranames=False):
        return [(fieldname,self.encodeField(fieldname)) for fieldname in self.fields]

    def fromPython(self,data):
        i = 0
        for fieldname in self.fields:
            setattr(self,fieldname,self.decodeField(fieldname,data[i][1]))
            i += 1
        return self        

    def content_part(self):
        '''returns a human readable representation of the content'''

        return self.toJson(False)

        content = ';'.join(['"%s"="%s"' % t for t in self.toPython()])
        return "%s={%s}" % (self.content_id,content)

    def toJson(self, extranames=False):
        return json.write(self.toPython(extranames))

    def fromJson(self,text):
        return self.fromPython(json.read(text))

    def __eq__(self,other):
        #return self.__dict__== other.__dict__
        if hasattr(self, 'content_part') and hasattr(other, 'content_part'):
            return self.content_part() == other.content_part()
        else:
            return False


    def serialize(self):
        import pickle
        import base64

        return base64.b64encode(pickle.dumps(self))


def encodeTime(seconds):
    #FIXME: this breaks if we are greater than whatever the epoc is (usually 2038)
    import time
    # we have to be careful here. Each field must be atleast 2 characters long.
    instant = ['%02d' % k for k in time.gmtime(seconds)[:6]]
    return '-'.join(instant[:3]) + 'T' + ':'.join(instant[3:6]) + 'Z'

def decodeTime(s):
    #FIXME: this breaks if we are greater than whatever the epoc is (usually 2038)
    import time, calendar
    # FIXME: this probably supports reading incorrectly formatted times.
    struct = time.strptime(s, '%Y-%m-%dT%H:%M:%SZ')
    return calendar.timegm(struct)

def validateIntString(s):
    """Returns a string if s is a an encoding of the integer value of s with no spaces or leading/trailing zeros or decimal points."""
    if str(int(s)) == s:
        return s
    else:
        raise TypeError('Encoding of int "%s" is incorrect' % s)

def validateIntStringList(l):
    """Returns a list of strings if each element in the list passes validateIntString."""
    for s in l:
        validateIntString(s)

    return l

def validateOptionsList(l):
    """Validates an options list is a list of (key, val) pairs of strings."""
    import types
    if not isinstance(l, types.ListType):
        raise TypeError('Not a valid options list')
    d = {}
    try:
        for key, val in l:
            if key in d:
                raise TypeError('Not a valid options list')
            if not isinstance(key, types.StringType):
                raise TypeError('Not a valid options list')
            if not isinstance(val, types.StringType):
                raise TypeError('Not a valid options list')
            d[key] = val
    except ValueError:
        raise TypeError('Not a valid options list')

    if not 'version' in d:
        raise TypeError('Not a valid options list')

    return l
        

class Signature(Container):
    """The signature container (a combination of the keyprint and signature fields.
    
    >>> s = Signature(keyprint='0',signature='*')
    >>> s.toJson()
    '[["keyprint","MA=="],["signature","Kg=="]]'
    >>> s == Signature().fromJson(s.toJson())
    True
    """
    fields = ['keyprint',
              'signature']

    codecs = {'keyprint':{'encode':base64.b64encode, 'decode':base64.b64decode},
              'signature':{'encode':base64.b64encode, 'decode':base64.b64decode}}
    

class ContainerWithSignature(Container):
    """A container with an optional signature field.

    To activate the Json-ing of the signature, supply an argument which is true to
    the function.

    >>> class TestContainer(ContainerWithSignature):
    ...     fields = ['string', 'number']
    ...     codecs = {'number':{'encode':base64.b64encode, 'decode':base64.b64decode}}

    >>> signature = Signature(keyprint='0', signature='*')

    >>> test1 = TestContainer(string='hello', number='@')
    >>> test1_j = test1.content_part()
    >>> test1_j
    '[["string","hello"],["number","QA=="]]'

    >>> test1.toPython(False)
    [('string', 'hello'), ('number', 'QA==')]

    >>> test2 = TestContainer().fromPython(test1.toPython(False))
    >>> test2 == test1
    True

    >>> test3 = TestContainer().fromJson(test1_j)
    >>> test3 == test1
    True

    Check to make sure toJson fails if we force it to use the signature and we don't
    have it
    >>> test4_j = test1.toJson()
    Traceback (most recent call last):
    ...
    AttributeError: 'NoneType' object has no attribute 'toPython'

    >>> test1.content_part() == test1_j
    True

    >>> test5 = TestContainer(string='hello', number='@', signature=signature)
    >>> test5_j = test5.toJson()
    >>> test5_j
    '[["string","hello"],["number","QA=="],["signature",[["keyprint","MA=="],["signature","Kg=="]]]]'

    >>> test5.toPython()
    [('string', 'hello'), ('number', 'QA=='), ['signature', [('keyprint', 'MA=='), ('signature', 'Kg==')]]]
    >>> TestContainer().fromPython(test5.toPython()).toPython()
    [('string', 'hello'), ('number', 'QA=='), ['signature', [('keyprint', 'MA=='), ('signature', 'Kg==')]]]

    >>> test6 = TestContainer().fromJson(test1.content_part())
    >>> test6.signature = signature
    >>> test6 == test5
    True

    >>> test5.content_part() == test1_j
    True
    
    TODO: Add verify_signature checking
    """
    def __init__(self, **kwargs):
        Container.__init__(self,**kwargs)
        self.jsontext = None
        self.signature = kwargs.get('signature')


    def toPython(self, extranames=True):
        if not extranames:
            return [(fieldname,self.encodeField(fieldname)) for fieldname in self.fields]
        else:
            fields = [(fieldname, self.encodeField(fieldname)) for fieldname in self.fields]
            fields.append(['signature', self.signature.toPython()])
            return fields

    def fromPython(self, data):
        i = 0
        for fieldname in self.fields:
            setattr(self,fieldname,self.decodeField(fieldname,data[i][1]))
            i += 1
        
        if len(data) - 1 == len(self.fields) and data[i][0] == 'signature':
            s = Signature()
            self.signature = s.fromPython(data[i][1])
            
        return self

    def toJson(self, extranames=True):
        return json.write(self.toPython(extranames))

    def fromJson(self,text):
        return self.fromPython(json.read(text))

    def verifySignature(self, signature_algorithm, hashing_algorithm, key):

        content_part = self.content_part()
        hasher = hashing_algorithm(content_part)
        signer = signature_algorithm(key)
        
        if hashing_algorithm(str(key)).digest() != self.signature.keyprint:
            return False
        
        return signer.verify(hasher.digest(), self.signature.signature)

############################ CDD ####################################

class CurrencyDescriptionDocument(ContainerWithSignature):
    """The CurrencyDescriptionDocument container

    Lets test a bit
    >>> import crypto
    >>> ics = crypto.CryptoContainer(signing=crypto.RSASigningAlgorithm,
    ...                              blinding=crypto.RSABlindingAlgorithm,
    ...                              hashing=crypto.SHA256HashingAlgorithm)
    
    >>> cdd = CDD(standard_identifier = 'http://opencoin.org/OpenCoinProtocol/1.0',
    ...           currency_identifier = 'http://opencent.net/OpenCent', 
    ...           short_currency_identifier = 'OC', 
    ...           issuer_service_location = 'opencoin://issuer.opencent.net:8002', 
    ...           denominations = ['1', '2', '5', '10', '20', '50', '100', '200', '500', '1000'], 
    ...           issuer_cipher_suite = ics, 
    ...           options = [['version', '0']],
    ...           issuer_public_master_key = crypto.RSAKeyPair(e=17L,n=3233L))

    >>> j = cdd.content_part()
    >>> j
    '[["standard_identifier","http://opencoin.org/OpenCoinProtocol/1.0"],["currency_identifier","http://opencent.net/OpenCent"],["short_currency_identifier","OC"],["issuer_service_location","opencoin://issuer.opencent.net:8002"],["denominations",["1","2","5","10","20","50","100","200","500","1000"]],["issuer_cipher_suite",["RSASigningAlgorithm","RSABlindingAlgorithm","SHA256HashingAlgorithm"]],["options",[["version","0"]]],["issuer_public_master_key","DKE=,EQ=="]]'
 
    >>> cdd2 = CDD().fromJson(j)
    >>> cdd2 == cdd
    True

    >>> sig = Signature(keyprint=']', signature='V')
    >>> cdd2.signature = sig

    >>> cdd2.toJson()
    '[["standard_identifier","http://opencoin.org/OpenCoinProtocol/1.0"],["currency_identifier","http://opencent.net/OpenCent"],["short_currency_identifier","OC"],["issuer_service_location","opencoin://issuer.opencent.net:8002"],["denominations",["1","2","5","10","20","50","100","200","500","1000"]],["issuer_cipher_suite",["RSASigningAlgorithm","RSABlindingAlgorithm","SHA256HashingAlgorithm"]],["options",[["version","0"]]],["issuer_public_master_key","DKE=,EQ=="],["signature",[["keyprint","XQ=="],["signature","Vg=="]]]]'
    
    
    >>> from tests import CDD as test_cdd

    >>> test_j = test_cdd.toJson()

    >>> test_cdd2 = CDD().fromJson(test_j)
    >>> test_cdd2 == test_cdd
    True

    >>> test_cdd2.signature == test_cdd.signature
    True

    >>> test_cdd3 = CDD().fromPython(test_cdd.toPython())
    >>> test_cdd3 == test_cdd
    True

    >>> test_cdd.verify_self()
    True
    """

    from crypto import encodeCryptoContainer, decodeCryptoContainer, decodeRSAKeyPair
    
    fields = ['standard_identifier', 
              'currency_identifier', 
              'short_currency_identifier', 
              'issuer_service_location', 
              'denominations', 
              'issuer_cipher_suite', 
              'options',
              'issuer_public_master_key']

    codecs = {'issuer_cipher_suite':{'encode':encodeCryptoContainer,'decode':decodeCryptoContainer},
              'issuer_public_master_key':{'encode':str, 'decode':decodeRSAKeyPair},
              'denominations':{'encode':list, 'decode':validateIntStringList},
              'options':{'encode':list, 'decode':validateOptionsList}}


    def __init__(self,**kwargs):
        ContainerWithSignature.__init__(self, **kwargs)
        self.keytype = kwargs.get('keytype', None)

    def verify_self(self):
        """Verifies the self-signed certificate."""
        import crypto        

        if 'version' not in dict(self.options):
            return False # required option
        ics = self.issuer_cipher_suite
        return self.verifySignature(ics.signing,
                                    ics.hashing,
                                    self.issuer_public_master_key)


CDD = CurrencyDescriptionDocument


class MintKey(ContainerWithSignature):
    """The MintKey container.

    The MintKey container holds everything (almost?) everything required to verify a
    Token.

    TODO: Some test go here. Things to test

    >>> from calendar import timegm
    >>> from tests import CDD, CDD_private, addSignature
    >>> import crypto, copy
    >>> private, public = crypto.createRSAKeyPair(512)
    >>> key_id = public.key_id(CDD.issuer_cipher_suite.hashing)

    >>> mintKey = MintKey(key_identifier=key_id,
    ...                   currency_identifier='http://opencent.net/OpenCent',
    ...                   denomination="1",
    ...                   not_before=timegm((2008,1,1,0,0,0)),
    ...                   key_not_after=timegm((2008,2,1,0,0,0)),
    ...                   token_not_after=timegm((2008,4,1,0,0,0)),
    ...                   public_key=public)
                          
    >>> hash_alg = CDD.issuer_cipher_suite.hashing
    >>> sign_alg = CDD.issuer_cipher_suite.signing
    
    >>> def addSignatureAndVerify(mintKey, CDD, signing_key):
    ...     ics = CDD.issuer_cipher_suite
    ...     mintKey = addSignature(mintKey, ics.hashing, ics.signing,
    ...                     signing_key, mintKey.key_identifier)
    ...     return mintKey.verify_with_CDD(CDD)

    >>> mintKey = addSignature(mintKey, hash_alg, sign_alg, CDD_private, CDD.signature.keyprint) 

    >>> mintKey.verify_with_CDD(CDD)
    True

    >>> mintKey.toJson()
    '[["key_identifier","..."],["currency_identifier","http://opencent.net/OpenCent"],["denomination","1"],["not_before","2008-01-01T00:00:00Z"],["key_not_after","2008-02-01T00:00:00Z"],["token_not_after","2008-04-01T00:00:00Z"],["public_key","..."],["signature",[["keyprint","hxz5pRwS+RFp88qQliXYm3R5uNighktwxqEh4RMOuuk="],["signature","..."]]]]'

    Well, we are going to test that verify_with_CDD works now. We've already
    built helper a helper function, addSignatureAndVerify. The reason
    we have it is because if we modify the fields, the signature checking will
    fail. So we have to have an incorrect field and a correct signature, to make
    sure we are testing only one error condition at a time.
    >>> mintKey2 = copy.deepcopy(mintKey)
    >>> mintKey2.signature.signature = "foo"
    >>> mintKey2.verify_with_CDD(CDD)
    False

    >>> mintKey3 = copy.deepcopy(mintKey)
    >>> mintKey3.signature.keyprint = "foo"
    >>> mintKey3.verify_with_CDD(CDD)
    False

    >>> mintKey4 = copy.deepcopy(mintKey)
    >>> mintKey4.key_identifier = "foo"
    >>> addSignatureAndVerify(mintKey2, CDD, CDD_private)
    False

    >>> mintKey5 = copy.deepcopy(mintKey)
    >>> mintKey5.public_key = "foo"
    >>> addSignatureAndVerify(mintKey2, CDD, CDD_private)
    False

    >>> mintKey6 = copy.deepcopy(mintKey)
    >>> mintKey6.currency_identifier = "foo"
    >>> addSignatureAndVerify(mintKey6, CDD, CDD_private)
    False

    >>> mintKey7 = copy.deepcopy(mintKey)
    >>> mintKey7.denomination = "1.4"
    >>> addSignatureAndVerify(mintKey7, CDD, CDD_private)
    False

    >>> mintKey8 = copy.deepcopy(mintKey)
    >>> mintKey8.signature = None
    >>> mintKey8.verify_with_CDD(CDD)
    False

    Just to make sure we didn't mess up something on the way...
    >>> mintKey.verify_with_CDD(CDD)
    True

    >>> mintKey == MintKey().fromPython(mintKey.toPython())
    True

    Okay. We'll test verify_time now. It returns (can_mint, can_redeem)
    The tuple input to timegm is (year, month, day, hour, minute, second).
    The h/m/s is the same as on a normal clock. h/m/s is in 24 hour time
    with the day starting at 0:0:0 and the end of the day 24:0:0. I think
    that day1 24:0:0 is the same as day2 0:0:0.
    >>> mintKey.verify_time(timegm((2007,12,1,0,0,0)))
    (False, False)

    >>> mintKey.verify_time(timegm((2008,1,1,0,0,0)))
    (True, True)

    >>> mintKey.verify_time(timegm((2008,2,1,0,0,0)))
    (True, True)

    >>> mintKey.verify_time(timegm((2008,2,1,0,0,1)))
    (False, True)

    >>> mintKey.verify_time(timegm((2008,4,1,0,0,0)))
    (False, True)

    >>> mintKey.verify_time(timegm((2008,4,1,0,0,1)))
    (False, False)
    """

    fields = ['key_identifier', 
              'currency_identifier', 
              'denomination', 
              'not_before', 
              'key_not_after', 
              'token_not_after',
              'public_key']

    from crypto import decodeRSAKeyPair

    codecs = {'key_identifier':{'encode':base64.b64encode,'decode':base64.b64decode},
              'public_key':{'encode':str,'decode':decodeRSAKeyPair},
              'not_before':{'encode':encodeTime,'decode':decodeTime},
              'key_not_after':{'encode':encodeTime,'decode':decodeTime},
              'token_not_after':{'encode':encodeTime,'decode':decodeTime},
              'denomination':{'encode':str,'decode':validateIntString}}

    def __init__(self, **kwargs):
        ContainerWithSignature.__init__(self, **kwargs)
        self.keytype = kwargs.get('keytype', None)
        if self.denomination and not isinstance(self.denomination, types.StringType):
            raise Exception('Tried to set a denomination that was not a string')

    def verify_with_CDD(self, currency_description_document):
        """verify_with_CDD verifies the mint key against the CDD ensuring valid values 
        matching the CDD and the signature validity.i
           
        It assumes the CDD is valid. If not, some tests here willl pass (notably the
        signature keyprint check)
        """

        cdd = currency_description_document

        if not self.signature:
            return False # if we have no signature, we are not valid (or verifiable)

        if self.signature.keyprint != cdd.signature.keyprint:
            return False # if they aren't the same master key, it isn't valid

        if self.denomination not in cdd.denominations:
            return False # if we are not a denomination, we aren't valid

        if self.currency_identifier != cdd.currency_identifier:
            return False # we have to be using the same currency identifier

        if self.key_identifier != cdd.issuer_cipher_suite.hashing(str(self.public_key)).digest():
            return False # the key identifier is not valid

        signing, hashing = cdd.issuer_cipher_suite.signing, cdd.issuer_cipher_suite.hashing
        return self.verifySignature(signing, hashing, cdd.issuer_public_master_key)
        
    def verify_time(self, time):
        """Whether the container is valid at time. Returns a tuple of (can_mint, can_redeem)."""

        can_mint = time >= self.not_before and time <= self.key_not_after
        can_redeem = time >= self.not_before and time <= self.token_not_after

        return (can_mint, can_redeem)


class CurrencyBase(Container):
    """The base class for the currency types.
    
    Test the adding of currencies
    >>> b = CurrencyBase(standard_identifier = 'http://opencoin.org/OpenCoinProtocol/1.0',
    ...                 currency_identifier = 'http://opencent.net/OpenCent',
    ...                 denomination = '1',
    ...                 key_identifier = 'keyid',
    ...                 serial = '1')

    #>>> b.value
    #1
    >>> import copy
    >>> c = copy.copy(b)
    >>> b + c
    2
    >>> sum([b,c])
    2

    Test that going from a python copy works
    >>> d = CurrencyBase().fromPython(b.toPython())
    >>> b + c + d
    3

    Test proper encoding/decoding of key_identifier and serial
    >>> b = CurrencyBase(standard_identifier = 'http://opencoin.org/OpenCoinProtocol/1.0',
    ...                 currency_identifier = 'http://opencent.net/OpenCent',
    ...                 denomination = '1',
    ...                 key_identifier = 'a',
    ...                 serial = 'b')

    >>> j = b.toJson()
    >>> j
    '[["standard_identifier","http://opencoin.org/OpenCoinProtocol/1.0"],["currency_identifier","http://opencent.net/OpenCent"],["denomination","1"],["key_identifier","YQ=="],["serial","Yg=="]]'

    >>> b == CurrencyBase().fromJson(j)
    True
    
    """
    
    fields = ['standard_identifier', 
              'currency_identifier', 
              'denomination', 
              'key_identifier', 
              'serial']

    # signature codec is in place for CurrencyCoin
    codecs = {'key_identifier':{'encode':base64.b64encode,'decode':base64.b64decode},
              'serial':{'encode':base64.b64encode,'decode':base64.b64decode},
              'denomination':{'encode':str,'decode':validateIntString}}


    def __init__(self, **kwargs):
        Container.__init__(self, **kwargs)

    def __add__(self,other):
        val = self.getValue()
        if type(other) == type(self) and self.sameCurrency(other):
            return val + other.getValue()
        elif type(other) == int:
            return val + other
        else:
            raise NotImplementedError
            

    __radd__ = __add__ 

    def getValue(self):
        try:
            return int(self.denomination)
        except Exception:
            pass  

    def sameCurrency(self, other):
        """Verifies the two objects are the same currency."""
        if self.standard_identifier != other.standard_identifier:
            return False

        if self.currency_identifier != other.currency_identifier:
            return False

        return True


    def validate_with_CDD_and_MintKey(self, currency_description_document, mint_key):
        """Validates the currency with the cdd and mint key. Also verifies mint_key (for my safety)."""

        cdd = currency_description_document

        if not mint_key.verify_with_CDD(cdd):
            return False

        if self.standard_identifier != cdd.standard_identifier:
            return False

        if self.currency_identifier != mint_key.currency_identifier:
            return False

        if self.denomination != mint_key.denomination:
            return False

        if self.key_identifier != mint_key.key_identifier:
            return False

        return True # Everything checks out

    

class CurrencyBlank(CurrencyBase):
    """CurrencyBlank is a blank without signature. It can blind and unblind.

    Pieces of this container are messy. It fills its own fields (serial), it
    holds additional information (blind_factor), and it passes that information
    on to the blind algorithm it stores.

    Everything in the case of a quick turnaround is easy. You create a blank,
    generate a serial, blind the blank, [receive the signed blind], unblind the
    signature, and make a new coin.
    
    Allowing testing however means that we need to be able to give a blind_factor.
    We also need to be able to stop the transaction partway after sending the
    signed blank, reset the software, and continue the transaction. With this in
    mind, 

    >>> blank = CurrencyBlank(standard_identifier='http://OpenCoin/1.0/',
    ...                       currency_identifier='http://OpenCent',
    ...                       denomination='1',
    ...                       key_identifier='cent')

    >>> blank.toJson()
    Traceback (most recent call last):
    ...
    TypeError: b2a_base64...

    >>> blank.serial = '123'

    >>> blank.toJson()
    '[["standard_identifier","http://OpenCoin/1.0/"],["currency_identifier","http://OpenCent"],["denomination","1"],["key_identifier","Y2VudA=="],["serial","MTIz"]]'

    >>> blank.serial = None
    >>> blank.generateSerial()
    >>> base64.b64encode(blank.serial)
    '...'

    >>> blank.generateSerial()
    Traceback (most recent call last):
    ...
    Exception: Cannot generate a new serial when the serial is set.
    
    
    Snippet of code from MintKey doctest. Figure out how to use it here
    >>> from calendar import timegm
    >>> from tests import CDD, CDD_private, keys512, addSignature
    >>> import crypto, copy

    >>> def addSignatureAndVerify(mintKey, CDD, signing_key):
    ...     ics = CDD.issuer_cipher_suite
    ...     mintKey = addSignature(mintKey, ics.hashing, ics.signing,
    ...                     signing_key, mintKey.key_identifier)
    ...     return mintKey.verify_with_CDD(CDD)
    
    >>> private1 = keys512[0]
    >>> public1 = private1.newPublicKeyPair()
                          
    >>> hash_alg = CDD.issuer_cipher_suite.hashing
    >>> sign_alg = CDD.issuer_cipher_suite.signing
    >>> blind_alg = CDD.issuer_cipher_suite.blinding
    
    >>> mintKey1 = MintKey(key_identifier=public1.key_id(hash_alg),
    ...                   currency_identifier='http://opencent.net/OpenCent',
    ...                   denomination='1',
    ...                   not_before=timegm((2008,1,1,0,0,0)),
    ...                   key_not_after=timegm((2008,2,1,0,0,0)),
    ...                   token_not_after=timegm((2008,4,1,0,0,0)),
    ...                   public_key=public1)
    >>> mintKey1 = addSignature(mintKey1, hash_alg, sign_alg, CDD_private, CDD.signature.keyprint) 

    >>> mintKey1.verify_with_CDD(CDD)
    True

    >>> private5 = keys512[1]
    >>> public5 = private5.newPublicKeyPair()
    >>> mintKey5 = MintKey(key_identifier=public5.key_id(hash_alg),
    ...                   currency_identifier='http://opencent.net/OpenCent',
    ...                   denomination='5',
    ...                   not_before=timegm((2008,1,1,0,0,0)),
    ...                   key_not_after=timegm((2008,2,1,0,0,0)),
    ...                   token_not_after=timegm((2008,4,1,0,0,0)),
    ...                   public_key=public5)
    >>> mintKey5 = addSignature(mintKey5, hash_alg, sign_alg, CDD_private, CDD.signature.keyprint) 

    >>> mintKey5.verify_with_CDD(CDD)
    True
    
    FIXME XXX A blank references a standard identifier, and a CDD uses a standard version!
    >>> blank = CurrencyBlank(standard_identifier=CDD.standard_identifier,
    ...                       currency_identifier=CDD.currency_identifier,
    ...                       denomination='1',
    ...                       key_identifier=mintKey1.key_identifier,
    ...                       serial='abcdefghijklmnopqrstuvwxyz')

    >>> blank.toJson()
    '[["standard_identifier","http://opencoin.org/OpenCoinProtocol/1.0"],["currency_identifier","http://opencent.net/OpenCent"],["denomination","1"],["key_identifier","sj17RxE1hfO06+oTgBs9Z7xLut/3NN+nHJbXSJYTks0="],["serial","YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo="]]'

    >>> blank.content_part() == blank.toJson()
    True

    >>> blind_value = blank.blind_blank(CDD, mintKey1, blind_factor='blind factor')
    >>> base64.b64encode(blind_value)
    'FtDSI1eT2FsXK+R/zJVk9mGTRan4KQsogVmSMFts3kVrdV4y3mkIuYEaZ3B0ZP491rqR0QtIlVEAYf8sQNgbhQ=='
    
    Do some magic as the mint
    >>> blind_sig = sign_alg(private1).sign(blind_value)
    >>> base64.b64encode(blind_sig)
    'ZEDz4RHVwUByR+QXwgZcNeIyg9T3hAgxl0taabVKjbv0DbxTmHYK9fgqlCtBSAvmNntk03DMKrIPpaLuAV3UcA=='

    >>> clear_sig = blank.unblind_signature(blind_sig)
    >>> base64.b64encode(clear_sig)
    'HIck+fim0TkjVupU1AeKpuSGN1CxLnDmT2jpBHMZSgdpYhKE90XoAsQVznljEn4NTXvRs5cXslWUNvcUeAuv2A=='

    Check for the same signature
    >>> clear_sig == sign_alg(private1).sign(hash_alg(blank.content_part()).digest())
    True

    >>> coin = blank.newCoin(clear_sig) # perform seperate testing
    >>> coin.validate_with_CDD_and_MintKey(CDD, mintKey1)
    True

    >>> coin.toJson()
    '[["standard_identifier","http://opencoin.org/OpenCoinProtocol/1.0"],["currency_identifier","http://opencent.net/OpenCent"],["denomination","1"],["key_identifier","sj17RxE1hfO06+oTgBs9Z7xLut/3NN+nHJbXSJYTks0="],["serial","YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo="],["signature","HIck+fim0TkjVupU1AeKpuSGN1CxLnDmT2jpBHMZSgdpYhKE90XoAsQVznljEn4NTXvRs5cXslWUNvcUeAuv2A=="]]'

    >>> coin2 = blank.newCoin(clear_sig, CDD, mintKey1)
    
    Test newCoin failures... newCoin performs a check if given a CDD
    or a MintKey. if it does not validate, it will raise an Exception.
    If we only give a MintKey or a CDD, it attempts to perform the
    validation, although it will fail. This is to prevent any accidents
    in arguments where the coin will not be checked when we want it to.
    >>> coin3 = blank.newCoin(clear_sig, CDD, mintKey5)
    Traceback (most recent call last):
    BlankError: New coin does not validate!

    >>> coin4 = blank.newCoin(clear_sig, CDD)
    Traceback (most recent call last):
    AttributeError: ...

    >>> coin5 = blank.newCoin(clear_sig, mint_key=mintKey1)
    Traceback (most recent call last):
    AttributeError: ...

    Test other blank functions.
    >>> blank2 = CurrencyBlank(standard_identifier=CDD.standard_identifier,
    ...                       currency_identifier=CDD.currency_identifier,
    ...                       denomination='1',
    ...                       key_identifier=mintKey1.key_identifier,
    ...                       serial='abcdefghijklmnopqrstuvwxyz')
    >>> blank2.setBlind(blind_alg, mintKey1.public_key, 'blind factor')
    >>> base64.b64encode(blank2.unblind_signature(blind_sig))
    'HIck+fim0TkjVupU1AeKpuSGN1CxLnDmT2jpBHMZSgdpYhKE90XoAsQVznljEn4NTXvRs5cXslWUNvcUeAuv2A=='

    >>> blank3 = CurrencyBlank(standard_identifier=CDD.standard_identifier,
    ...                       currency_identifier=CDD.currency_identifier,
    ...                       denomination='1',
    ...                       key_identifier=mintKey1.key_identifier,
    ...                       serial='abcdefghijklmnopqrstuvwxyz',
    ...                       blind_factor='blind factor')
    >>> blank3.setBlind(blind_alg, mintKey1.public_key)
    >>> base64.b64encode(blank3.unblind_signature(blind_sig))
    'HIck+fim0TkjVupU1AeKpuSGN1CxLnDmT2jpBHMZSgdpYhKE90XoAsQVznljEn4NTXvRs5cXslWUNvcUeAuv2A=='

    And this is the normal and standard way to make a blank and blind
    >>> blank4 = CurrencyBlank(standard_identifier=CDD.standard_identifier,
    ...                       currency_identifier=CDD.currency_identifier,
    ...                       denomination='1',
    ...                       key_identifier=mintKey1.key_identifier)
    >>> blank4.generateSerial()
    >>> blind_value4 = blank4.blind_blank(CDD, mintKey1)
    >>> base64.b64encode(blind_value4)
    '...'

    The blind_factor can be used to recreate a blank
    >>> from Crypto.Util import number
    >>> base64.b64encode(number.long_to_bytes(blank4.blind_factor))
    '...'

    """

    def __init__(self, **kwargs):
        CurrencyBase.__init__(self, **kwargs)
        self.blind_factor = kwargs.get('blind_factor', None)

    def generateSerial(self): 
        from crypto import _r as Random
        if self.serial:
            raise Exception('Cannot generate a new serial when the serial is set.')
        
        self.serial = Random.getRandomString(128)

    def blind_blank(self, cdd, mint_key, blind_factor=None):
        """Returns the blinded value of the hash of the coin for signing."""

        if self.blind_factor: # we only allow blind_factors to be passed in.
            raise Exception('CurrencyBlank already has a blind factor')

        self.blinding = cdd.issuer_cipher_suite.blinding(mint_key.public_key)
        hashing = cdd.issuer_cipher_suite.hashing(self.content_part())

        # Note: we pass in blind_factor. If None, the blind_factor will be automaticall generated
        self.blind_value, self.blind_factor = self.blinding.blind(hashing.digest(), blind_factor)
        return self.blind_value

    def unblind_signature(self, signature):
        """Returns the unblinded value of the blinded signature."""
            
        return self.blinding.unblind(signature)

    def setBlind(self, blind_alg, key, blind_factor=None):
        """setBlind is used to set the state of self.blinding without performing the blinding.
        It is similar to blind_blank except that it does not perform any blinding itself.
        """
        
        if blind_factor:
            self.blind_factor = blind_factor

        self.blinding = blind_alg(key, self.blind_factor)
        
    def newCoin(self, signature, currency_description_document=None, mint_key=None):
        """Returns a coin using the unblinded signature.
        Performs tests if currency_description_document and mint_key are provided.
        """
        coin = CurrencyCoin(standard_identifier = self.standard_identifier, 
                            currency_identifier = self.currency_identifier, 
                            denomination = self.denomination, 
                            key_identifier = self.key_identifier,
                            serial = self.serial,
                            signature = signature)
        
        
        # if only one is provided, we have an error. Purposefully use an 'or' for the test to get an exception later
        if currency_description_document or mint_key:
            if not coin.validate_with_CDD_and_MintKey(currency_description_document, 
                                                         mint_key):
                raise BlankError('New coin does not validate!')
        
        return coin

class BlankError(Exception):
    """BlankError is when a Blank cannot become a coin."""
    pass
        
class CurrencyCoin(CurrencyBase):
    """The CurrencyCoin. 

    >>> from tests import CDD, CDD_private, keys512, addSignature, mintKeys
    >>> import copy
    >>> from calendar import timegm

    >>> private = keys512[0]
    >>> public = private.newPublicKeyPair()
                          
    >>> hash_alg = CDD.issuer_cipher_suite.hashing
    >>> sign_alg = CDD.issuer_cipher_suite.signing
    >>> blind_alg = CDD.issuer_cipher_suite.blinding
    
    >>> mintKey = mintKeys[0]

    >>> signature = 'HIck+fim0TkjVupU1AeKpuSGN1CxLnDmT2jpBHMZSgdpYhKE90XoAsQVznljEn4NTXvRs5cXslWUNvcUeAuv2A=='

    >>> coin = CurrencyCoin(standard_identifier=CDD.standard_identifier,
    ...                     currency_identifier=CDD.currency_identifier,
    ...                     denomination='1',
    ...                     key_identifier=mintKey.key_identifier,
    ...                     serial='abcdefghijklmnopqrstuvwxyz',
    ...                     signature=base64.b64decode(signature))

    >>> coin.toJson()
    '[["standard_identifier","http://opencoin.org/OpenCoinProtocol/1.0"],["currency_identifier","http://opencent.net/OpenCent"],["denomination","1"],["key_identifier","sj17RxE1hfO06+oTgBs9Z7xLut/3NN+nHJbXSJYTks0="],["serial","YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo="],["signature","HIck+fim0TkjVupU1AeKpuSGN1CxLnDmT2jpBHMZSgdpYhKE90XoAsQVznljEn4NTXvRs5cXslWUNvcUeAuv2A=="]]'

    >>> coin.content_part()
    '[["standard_identifier","http://opencoin.org/OpenCoinProtocol/1.0"],["currency_identifier","http://opencent.net/OpenCent"],["denomination","1"],["key_identifier","sj17RxE1hfO06+oTgBs9Z7xLut/3NN+nHJbXSJYTks0="],["serial","YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo="]]'

    >>> coin2 = CurrencyCoin().fromJson(coin.toJson())
    >>> coin2 == coin
    True

    >>> coin.validate_with_CDD_and_MintKey(CDD, mintKey)
    True

    Check that a bad signature will fail
    >>> coin3 = copy.deepcopy(coin)
    >>> coin3.signature = 'foobar'
    >>> coin3.validate_with_CDD_and_MintKey(CDD, mintKey)
    False

    """
    
    def __init__(self, **kwargs):
        CurrencyBase.__init__(self, **kwargs)
        self.jsontext = None
        self.signature = kwargs.get('signature')

    # base64 encoding and decoding is hardcoded here in to/fromJson
    def toJson(self,extranames=1):
        if extranames:
            if self.jsontext:
                return self.jsontext
            else:
                data = self.toPython(forcesig=1)
                self.jsontext = json.write(data)
                return self.jsontext
        else:       
            return json.write(self.toPython(nosig=1))

    def fromJson(self,text):
        data = json.read(text)
        if len(data) == len(self.fields) + 1 and data[-1][0] == 'signature':
            self.jsontext = text
        return self.fromPython(data)

    def toPython(self,forcesig=None,nosig=None):
        data = CurrencyBase.toPython(self)
        if forcesig or (not nosig and self.signature):
            data.append(('signature',base64.b64encode(self.signature)))
        return data            

    def fromPython(self,data):
        CurrencyBase.fromPython(self,data)
        if len(data) == len(self.fields) + 1 and data[-1][0] == 'signature':
            self.signature = base64.b64decode(data[-1][1])
        return self            


    def validate_with_CDD_and_MintKey(self, currency_description_document, mint_key):

        if not CurrencyBase.validate_with_CDD_and_MintKey(self, currency_description_document, mint_key):
            return False

        key = mint_key.public_key
        signer = currency_description_document.issuer_cipher_suite.signing(key)
        hasher = currency_description_document.issuer_cipher_suite.hashing(self.content_part())

        if not signer.verify(hasher.digest(), self.signature):
            return False

        return True


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS) 

