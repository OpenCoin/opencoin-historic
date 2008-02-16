import base64,json

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

    def toPython(self):
        return [(fieldname,self.encodeField(fieldname)) for fieldname in self.fields]

    def fromPython(self,data):
        i = 0
        for fieldname in self.fields:
            setattr(self,fieldname,self.decodeField(fieldname,data[i][1]))
            i += 1
        return self        

    def content_part(self):
        '''returns a human readable representation of the content'''

        return self.toJson()

        content = ';'.join(['"%s"="%s"' % t for t in self.toPython()])
        return "%s={%s}" % (self.content_id,content)

    def toJson(self):
        return json.write(self.toPython())

    def fromJson(self,text):
        return self.fromPython(json.read(text))

    def __eq__(self,other):
        #return self.__dict__== other.__dict__
        return self.toJson() == other.toJson()


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
    >>> test1_j = test1.toJson()
    >>> test1_j
    '[["string","hello"],["number","QA=="]]'

    >>> test1.toPython()
    [('string', 'hello'), ('number', 'QA==')]

    >>> test2 = TestContainer().fromPython(test1.toPython())
    >>> test2 == test1
    True

    >>> test3 = TestContainer().fromJson(test1_j)
    >>> test3 == test1
    True

    Check to make sure toJson fails if we force it to use the signature and we don't
    have it
    >>> test4_j = test1.toJson(1)
    Traceback (most recent call last):
    ...
    AttributeError: 'NoneType' object has no attribute 'toPython'

    >>> test1.content_part() == test1_j
    True

    >>> test5 = TestContainer(string='hello', number='@', signature=signature)
    >>> test5_j = test5.toJson(1)
    >>> test5_j
    '[["string","hello"],["number","QA=="],["signature",[["keyprint","MA=="],["signature","Kg=="]]]]'

    This test is quirky and non-sensical with signatures
    #>>> test5.toPython()
    #>>> TestContainer().fromPython(test5.toPython()) <- this will be without signature :/

    >>> test6 = TestContainer().fromJson(test1.toJson())
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


    def toJson(self,signature=0):
        if signature:
            if self.jsontext:
                return self.jsontext
            else:
                data = self.toPython()
                data.append(['signature',self.signature.toPython()])
                self.jsontext = json.write(data)
                return self.jsontext
        else:       
            return json.write(self.toPython())

    def fromJson(self,text):
        data = json.read(text)
        if len(data) == len(self.fields) + 1 and data[-1][0] == 'signature':
            s = Signature()
            self.signature = s.fromPython(data[-1][1])
            self.jsontext = text
        return self.fromPython(data)



    def verifySignature(self, signature_algorithm, hashing_algorithm, key):

        content_part = self.content_part()
        hasher = hashing_algorithm(content_part)
        signer = signature_algorithm(key)
        
        if hashing_algorithm(str(key)).digest() != self.signature.keyprint:
            return False
        
        return signer.verify(hasher.digest(), self.signature.signature)

class CurrencyDescriptionDocument(ContainerWithSignature):
    """The CurrencyDescriptionDocument container

    Lets test a bit
    >>> import crypto
    >>> ics = crypto.CryptoContainer(signing=crypto.RSASigningAlgorithm,
    ...                              blinding=crypto.RSABlindingAlgorithm,
    ...                              hashing=crypto.SHA256HashingAlgorithm)
    
    >>> cdd = CDD(standard_version = 'http://opencoin.org/OpenCoinProtocol/1.0',
    ...           currency_identifier = 'http://opencent.net/OpenCent', 
    ...           short_currency_identifier = 'OC', 
    ...           issuer_service_location = 'opencoin://issuer.opencent.net:8002', 
    ...           denominations = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000], 
    ...           issuer_cipher_suite = ics, 
    ...           issuer_public_master_key = crypto.RSAKeyPair(e=17L,n=3233L))

    >>> j = cdd.toJson()
    >>> j
    '[["standard_version","http://opencoin.org/OpenCoinProtocol/1.0"],["currency_identifier","http://opencent.net/OpenCent"],["short_currency_identifier","OC"],["issuer_service_location","opencoin://issuer.opencent.net:8002"],["denominations",[1,2,5,10,20,50,100,200,500,1000]],["issuer_cipher_suite",["RSASigningAlgorithm","RSABlindingAlgorithm","SHA256HashingAlgorithm"]],["issuer_public_master_key","DKE=,EQ=="]]'
 
    >>> cdd2 = CDD().fromJson(j)
    >>> cdd2 == cdd
    True

    >>> sig = Signature(keyprint=']', signature='V')
    >>> cdd2.signature = sig

    >>> cdd2.toJson(1)
    '[["standard_version","http://opencoin.org/OpenCoinProtocol/1.0"],["currency_identifier","http://opencent.net/OpenCent"],["short_currency_identifier","OC"],["issuer_service_location","opencoin://issuer.opencent.net:8002"],["denominations",[1,2,5,10,20,50,100,200,500,1000]],["issuer_cipher_suite",["RSASigningAlgorithm","RSABlindingAlgorithm","SHA256HashingAlgorithm"]],["issuer_public_master_key","DKE=,EQ=="],["signature",[["keyprint","XQ=="],["signature","Vg=="]]]]'
    
    
    And now, lets play with a really signed CDD
    >>> private_key, public_key = crypto.createRSAKeyPair(1024)

    >>> public_key.hasPrivate()
    False
    
    >>> from tests import CDD as test_cdd

    >>> test_j = test_cdd.toJson(1)
    
    >>> test_cdd2 = CDD().fromJson(test_j)
    >>> test_cdd2 == test_cdd
    True

    >>> test_cdd2.signature == test_cdd.signature
    True

    >>> test_cdd.verify_self()
    True

    >>> test_cdd2.signature.keyprint = "Foo"
    >>> test_cdd2.verify_self()
    False
    """

    from crypto import encodeCryptoContainer, decodeCryptoContainer, decodeRSAKeyPair
    
    fields = ['standard_version', 
              'currency_identifier', 
              'short_currency_identifier', 
              'issuer_service_location', 
              'denominations', 
              'issuer_cipher_suite', 
              'issuer_public_master_key']

    codecs = {'issuer_cipher_suite':{'encode':encodeCryptoContainer,'decode':decodeCryptoContainer},
              'issuer_public_master_key':{'encode':str, 'decode':decodeRSAKeyPair}}


    def __init__(self,**kwargs):
        ContainerWithSignature.__init__(self, **kwargs)
        self.keytype = kwargs.get('keytype', None)

    def verify_self(self):
        """Verifies the self-signed certificate."""
        import crypto        
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
    >>> from tests import CDD, CDD_private
    >>> import crypto, copy
    >>> private, public = crypto.createRSAKeyPair(512)
    >>> key_id = public.key_id(CDD.issuer_cipher_suite.hashing)

    >>> mintKey = MintKey(key_identifier=key_id,
    ...                   currency_identifier='http://opencent.net/OpenCent',
    ...                   denomination=1,
    ...                   not_before=timegm((2008,1,1,0,0,0)),
    ...                   key_not_after=timegm((2008,2,1,0,0,0)),
    ...                   coin_not_after=timegm((2008,4,1,0,0,0)),
    ...                   public_key=public)
                          
    >>> hash_alg = CDD.issuer_cipher_suite.hashing
    >>> sign_alg = CDD.issuer_cipher_suite.signing
    
    >>> def addSignature(mintKey, hash_alg, sign_alg, signing_key, keyprint):
    ...     hasher = hash_alg(mintKey.content_part())
    ...     signer = sign_alg(signing_key)
    ...     signature = Signature(keyprint=keyprint,
    ...                           signature=signer.sign(hasher.digest()))
    ...     mintKey.signature = signature
    ...     return mintKey
    
    >>> def addSignatureAndVerify(mintKey, CDD, signing_key):
    ...     ics = CDD.issuer_cipher_suite
    ...     mintKey = addSignature(mintKey, ics.hashing, ics.signing,
    ...                     signing_key, mintKey.key_identifier)
    ...     return mintKey.verify_with_CDD(CDD)

    >>> mintKey = addSignature(mintKey, hash_alg, sign_alg, CDD_private, CDD.signature.keyprint) 

    >>> mintKey.verify_with_CDD(CDD)
    True

    >>> mintKey.toJson(1)
    '[["key_identifier","..."],["currency_identifier","http://opencent.net/OpenCent"],["denomination",1],["not_before","2008-01-01T00:00:00Z"],["key_not_after","2008-02-01T00:00:00Z"],["coin_not_after","2008-04-01T00:00:00Z"],["public_key","..."],["signature",[["keyprint","hxz5pRwS+RFp88qQliXYm3R5uNighktwxqEh4RMOuuk="],["signature","..."]]]]'

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


    Just to make sure we didn't mess up something on the way...
    >>> mintKey.verify_with_CDD(CDD)
    True
    """

    fields = ['key_identifier', 
              'currency_identifier', 
              'denomination', 
              'not_before', 
              'key_not_after', 
              'coin_not_after',
              'public_key']

    from crypto import decodeRSAKeyPair

    codecs = {'key_identifier':{'encode':base64.b64encode,'decode':base64.b64decode},
              'public_key':{'encode':str,'decode':decodeRSAKeyPair},
              'not_before':{'encode':encodeTime,'decode':decodeTime},
              'key_not_after':{'encode':encodeTime,'decode':decodeTime},
              'coin_not_after':{'encode':encodeTime,'decode':decodeTime}}

    def __init__(self, **kwargs):
        ContainerWithSignature.__init__(self, **kwargs)
        self.keytype = kwargs.get('keytype', None)

    def verify_with_CDD(self, currency_description_document):
        """verify_with_CDD verifies the mint key against the CDD ensuring valid values 
           matching the CDD and the signature validity."""

        cdd = currency_description_document

        if self.signature.keyprint != cdd.signature.keyprint:
            return False # if they aren't the same master key, it isn't valid

        if self.denomination not in cdd.denominations:
            return False # if we are not a denomination, we aren't valid

        if self.currency_identifier != cdd.currency_identifier:
            return False # we have to be using the same currency identifier

        if self.key_identifier != cdd.issuer_cipher_suite.hashing(str(self.public_key)).digest():
            return False # the key identifier is not valid

        if self.signature:
            signing, hashing = cdd.issuer_cipher_suite.signing, cdd.issuer_cipher_suite.hashing
            return self.verifySignature(signing, hashing, cdd.issuer_public_master_key)
        else:
            return False # if we have no signature, we are not valid (or verifiable)
        
    def verify_time(self, time):
        """Whether the container is currently valid. Returns a tuple of (can_mint, can_redeem)."""

        can_mint = time > self.not_before and time < self.key_not_after
        can_redeem = time > self.not_before and time < self.coin_not_after

        return can_mint and can_redeem

    def key_id(self, digestAlgorithm=None):
        if not digestAlgorithm:
            import crypto
            digestAlgorithm = crypto.SHA256HashingAlgorithm
        return digestAlgorithm().update(str(self)).digest()

class CurrencyBase(Container):
    """The base class for the currency types.
    
    Test the adding of currencies
    >>> b = CurrencyBase(standard_version = 'http://opencoin.org/OpenCoinProtocol/1.0',
    ...                 currency_identifier = 'http://opencent.net/OpenCent',
    ...                 denomination = '1',
    ...                 key_identifier = 'keyid',
    ...                 serial = '1')
    >>> b.value
    1
    >>> import copy
    >>> c = copy.copy(b)
    >>> b + c
    2
    >>> sum([b,c])
    2

    Test proper encoding/decoding of key_identifier and serial
    >>> b = CurrencyBase(standard_version = 'http://opencoin.org/OpenCoinProtocol/1.0',
    ...                 currency_identifier = 'http://opencent.net/OpenCent',
    ...                 denomination = '1',
    ...                 key_identifier = 'a',
    ...                 serial = 'b')

    >>> j = b.toJson()
    >>> j
    '[["standard_identifier",null],["currency_identifier","http://opencent.net/OpenCent"],["denomination","1"],["key_identifier","YQ=="],["serial","Yg=="]]'

    >>> b == CurrencyBase().fromJson(j)
    True
    
    """
    
    fields = ['standard_identifier', 
              'currency_identifier', 
              'denomination', 
              'key_identifier', 
              'serial']

    codecs = {'key_identifier':{'encode':base64.b64encode,'decode':base64.b64decode},
              'serial':{'encode':base64.b64encode,'decode':base64.b64decode},}


    def __init__(self, **kwargs):
        Container.__init__(self, **kwargs)
        self.value = 0
        self.setValue()

    def __add__(self,other):
        val = self.value
        if type(other) == type(self) and self.sameCurrency(other):
            return val + other.value
        elif type(other) == int:
            return val + other
            

    __radd__ = __add__ 

    def setValue(self,value=None):
        if value:
            self.value = value
        else:
            try:
                self.value = int(self.denomination)
            except:
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

        if self.standard_identifier != cdd.standard_version:
            return False

        if self.currency_identifier != mint_key.currency_identifier:
            return False

        if self.denomination != mint_key.denomination:
            return False

        if self.key_identifier != mint_key.key_identifier:
            return False

        return True # Everything checks out

    

class CurrencyBlank(CurrencyBase):


    def generateSerial(self):
    
        import crypto
        if self.serial:
            raise MessageError('gah! trying to make another serial.')
        
        self.serial = crypto._r.getRandomString(128)

    def blind_blank(self, cdds, mint_keys_key_id):
        """Returns the blinded value of the hash of the coin for signing."""

        if self.blind_factor:
            raise MessageError('CurrenyBlank already has a blind factor')

        self.blinding = cdds[self.currency_identifier].issuer_cipher_suite.blinding(mint_keys_key_id[self.key_identifier].public_key)
        hashing = cdds[self.currency_identifier].issuer_cipher_suite.hashing()

        hashing.update(self.content_part())
        self.blinding.update(hashing.digest())
        
        self.blind_value, self.blind_factor = self.blinding.blind()
        return self.blind_value

    def unblind_signature(self, signature):
        """Returns the unblinded value of the blinded signature."""

        self.blinding.reset(signature)
        return self.blinding.unblind()

    def newCoin(self, signature, currency_description_document=None, mint_key=None):
        """Returns a coin using the unblinded signature.
        Performs tests if currency_description_document and mint_key are provided.
        """
        coin = CurrencyCoin(self.standard_identifier, 
                            self.currency_identifier, 
                            self.denomination, 
                            self.key_identifier,
                            self.serial, signature)
        
        
        # if only one is provided, we have an error. Purposefully use an 'or' for the test to get an exception later
        if currency_description_document or mint_key:
            if not coin.validate_with_CDD_and_MintKey(currency_description_document, 
                                                         mint_key):
                raise Exception('New coin does not validate!')
        
        return coin
        
class CurrencyCoin(CurrencyBase,ContainerWithSignature):

    content_id = 'Currency'              

    def validate_with_CDD_and_MintKey(self, currency_description_document, mint_key):

        if not CurrencyBase.validate_with_CDD_and_MintKey(self, currency_description_document, mint_key):
            return False

        key = mint_key.public_key
        signer = currency_description_document.issuer_cipher_suite.signing(key)
        hasher = currency_description_document.issuer_cipher_suite.hashing()

        hasher.update(self.content_part())
        signer.update(hasher.digest())
        
        if not signer.verify(self.signature):
            return False

        return True

    

if __name__ == "__main__":
    import doctest
    doctest.testmod()
