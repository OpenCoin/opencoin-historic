import base64,json

class Container(object):
    """A generic container, handles serializing
    
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
    '[["foo","foo"],["bar","YmFy\\\\n"]]'
    
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


class Signature(Container):
    '''
    >>> s = Signature(keyprint='foo',signature='bar')
    >>> s
    <Signature(keyprint='foo',signature='bar')>
    >>> s.toPython()
    [('keyprint', 'foo'), ('signature', 'bar')]
    >>> s.toJson()
    '[["keyprint","foo"],["signature","bar"]]'
    '''
    fields = ['keyprint',
              'signature']
    

class ContainerWithSignature(Container):
    

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
        return signer.verify(hasher.digest(), self.signature.signature)

class CurrencyDescriptionDocument(ContainerWithSignature):
    """
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

    >>> data = cdd.toPython()
    >>> cdd2 = CDD().fromPython(data)
    >>> cdd2 == cdd
    True

    >>> cdd2.toJson() == cdd.toJson()
    True

    >>> j = cdd.toJson()
    >>> j
    '[["standard_version","http://opencoin.org/OpenCoinProtocol/1.0"],["currency_identifier","http://opencent.net/OpenCent"],["short_currency_identifier","OC"],["issuer_service_location","opencoin://issuer.opencent.net:8002"],["denominations",[1,2,5,10,20,50,100,200,500,1000]],["issuer_cipher_suite",["RSASigningAlgorithm","RSABlindingAlgorithm","SHA256HashingAlgorithm"]],["issuer_public_master_key","DKE=,EQ=="]]'
 
    >>> cdd3 = CDD().fromJson(j)
    >>> cdd3 == cdd
    True

    >>> sig = Signature(keyprint=21, signature=23)
    >>> cdd3.signature = sig

    >>> cdd3.toJson(1) #the format expected is questionable.
    '[["standard_version","http://opencoin.org/OpenCoinProtocol/1.0"],["currency_identifier","http://opencent.net/OpenCent"],["short_currency_identifier","OC"],["issuer_service_location","opencoin://issuer.opencent.net:8002"],["denominations",[1,2,5,10,20,50,100,200,500,1000]],["issuer_cipher_suite",["RSASigningAlgorithm","RSABlindingAlgorithm","SHA256HashingAlgorithm"]],["issuer_public_master_key","DKE=,EQ=="],["signature",[["keyprint",21],["signature",23]]]]'
    
    
    And now, lets play with a really signed CDD
    >>> private_key = crypto.createRSAKeyPair(1024)
    >>> public_key = private_key.newPublicKeyPair()

    >>> public_key.hasPrivate()
    False

    >>> test_cdd = CDD(standard_version = 'http://opencoin.org/OpenCoinProtocol/1.0',
    ...            currency_identifier = 'http://opencent.net/OpenCent',
    ...            short_currency_identifier = 'OC',
    ...            issuer_service_location = 'opencoin://issuer.opencent.net:8002',
    ...            denominations = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000],
    ...            issuer_cipher_suite = ics,
    ...            issuer_public_master_key = public_key)
    
    >>> hasher = crypto.SHA256HashingAlgorithm()
    >>> signer = crypto.RSASigningAlgorithm(private_key)

    >>> keyprint = hasher.update(str(test_cdd.issuer_public_master_key)).digest()
    >>> signature = signer.sign(hasher.reset(test_cdd.content_part()).digest())

    >>> test_cdd.signature =  Signature(keyprint=keyprint, signature=signature)

    >>> test_j = test_cdd.toJson(1)
    
    >>> test_cdd2 = CDD().fromJson(test_j)
    >>> test_cdd2 == test_cdd
    True


    # would this ever fail and test_cdd2 == test_cdd?
    >>> test_cdd2.signature == test_cdd.signature
    True


    We always use the original jsontext to represent ourself!
    >>> test_cdd2.short_currency_identifier = 'Foobar'
    >>> test_cdd2.toJson(1) == test_j
    True

    >>> test_cdd.verify_self()
    True

    """

    from crypto import encodeCryptoContainer, decodeCryptoContainer, decodeRSAKeyPair
    
    fields = ['standard_version', 
              'currency_identifier', 
              'short_currency_identifier', 
              'issuer_service_location', 
              'denominations', 
              'issuer_cipher_suite', 
              'issuer_public_master_key']

    codecs = { \
              'issuer_cipher_suite':{'encode':encodeCryptoContainer,'decode':decodeCryptoContainer}, \
              'issuer_public_master_key':{'encode':str, \
                                          'decode':decodeRSAKeyPair}, \
              # 'signature':{'encode':Signature.,'decode':Signature.decode} \
              }


    def __init__(self,**kwargs):
        ContainerWithSignature.__init__(self, **kwargs)
        self.signature = kwargs.get('signature',None)
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

    fields = ['key_identifier', 
              'currency_identifier', 
              'denomination', 
              'not_before', 
              'key_not_after', 
              'coin_not_after',
              'public_key']

    from crypto import decodeRSAKeyPair

    codecs = {'key_identifier':{'encode':base64.b64encode,'decode':base64.b64decode},
              'public_key':{'encode':str,'decode':decodeRSAKeyPair}}

    def __init__(self, **kwargs):
        ContainerWithSignature.__init__(self, **kwargs)
        self.signature = kwargs.get('signature', None)
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

class CurrencyBase:

    fields = ['standard_identifier', 
              'currency_identifier', 
              'denomination', 
              'key_identifier', 
              'serial']

    codecs = {'key_identifier':{'encode':base64.encode,'decode':base64.decode},
              'serial':{'encode':base64.encode,'decode':base64.decode},}

    def validate_with_CDD_and_MintingKey(self, currency_description_document, minting_key):
        """Validates the currency with the cdd and minting key. Also verifies minting_key (for my safety)."""

        cdd = currency_description_document

        if not minting_key.verify_with_CDD(cdd):
            return False

        if self.standard_identifier != cdd.standard_version:
            return False

        if self.currency_identifier != minting_key.currency_identifier:
            return False

        if self.denomination != minting_key.denomination:
            return False

        if self.key_identifier != minting_key.key_identifier:
            return False

        return True # Everything checks out

    

class CurrencyBlank(CurrencyBase):

    fields = ['standard_identifier', 
              'currency_identifier', 
              'denomination', 
              'key_identifier', 
              'serial', 
              #'blind_factor'
              ]
    
    def generateSerial(self):
    
        import crypto
        if self.serial:
            raise MessageError('gah! trying to make another serial.')
        
        self.serial = crypto._r.getRandomString(128)

    def blind_blank(self, cdds, minting_keys_key_id):
        """Returns the blinded value of the hash of the coin for signing."""

        if self.blind_factor:
            raise MessageError('CurrenyBlank already has a blind factor')

        self.blinding = cdds[self.currency_identifier].issuer_cipher_suite.blinding(minting_keys_key_id[self.key_identifier].public_key)
        hashing = cdds[self.currency_identifier].issuer_cipher_suite.hashing()

        hashing.update(self.content_part())
        self.blinding.update(hashing.digest())
        
        self.blind_value, self.blind_factor = self.blinding.blind()
        return self.blind_value

    def unblind_signature(self, signature):
        """Returns the unblinded value of the blinded signature."""

        self.blinding.reset(signature)
        return self.blinding.unblind()

    def newCoin(self, signature, currency_description_document=None, minting_key=None):
        """Returns a coin using the unblinded signature.
        Performs tests if currency_description_document and minting_key are provided.
        """
        coin = CurrencyCoin(self.standard_identifier, 
                            self.currency_identifier, 
                            self.denomination, 
                            self.key_identifier,
                            self.serial, signature)
        
        
        # if only one is provided, we have an error. Purposefully use an 'or' for the test to get an exception later
        if currency_description_document or minting_key:
            if not coin.validate_with_CDD_and_MintingKey(currency_description_document, 
                                                         minting_key):
                raise Exception('New coin does not validate!')
        
        return coin
        
class CurrencyCoin(CurrencyBase):

    fields = ['standard_identifier', 
              'currency_identifier', 
              'denomination', 
              'key_identifier', 
              'serial']

    content_id = 'Currency'              
       
    def validate_with_CDD_and_MintingKey(self, currency_description_document, minting_key):

        if not CurrencyBase.validate_with_CDD_and_MintingKey(self, currency_description_document, minting_key):
            return False

        key = minting_key.public_key
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
