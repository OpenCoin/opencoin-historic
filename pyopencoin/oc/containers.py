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

    Serialize human readable    
    >>> c.content_part()
    'Container={"foo"="foo";"bar"="bar"}'

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

        content = ';'.join(['"%s"="%s"' % t for t in self.toPython()])
        return "%s={%s}" % (self.content_id,content)

    def toJson(self):
        return json.write(self.toPython())

    def fromJson(self,text):
        return self.fromPython(json.read(text))

    def __eq__(self,other):
        return self.__dict__==other.__dict__


class Signature:
    def __init__(self, keyprint, signature):
        self.keyprint = keyprint
        self.signature = signature


class ContainerWithBase(Container):

    def _verifyASignature(self, signature_algorithm, hashing_algorithm, signature, key, content_part):

        hasher = hashing_algorithm(content_part)
        signer = signature_algorithm(key, hasher.digest())
        return signer.verify(signature.signature)
    

class ContainerWithSignature(ContainerWithBase):

    def __init__(self, **kwargs):
        ContainerWithBase.__init__(self,**kwargs)
        self.signature = kwargs.get('signature')

    def verifySignature(self, signature_algorithm, hashing_algorithm, key):

        return self._verifyASignature(signature_algorithm, 
                                      hashing_algorithm, 
                                      self.signature, 
                                      key, 
                                      self.content_part())


class ContainerWithAdSignatures(ContainerWithBase):
    "has multiple additional signatures, not necessarily signed by a specific party."

    def __init__(self, **kwargs):
        ContainerWithBase.__init__(self,**kwargs)
        self.signatures = kwargs.get('signatures')
        if not signatures:
            self.signatures = []

    def verifyAdSignatures(self, signature_algorithm, hashing_algorithm, key, keyprint):
        for s in self.signatures:
            if s == keyprint:
                return self._verifyASignature(signature_algorithm, 
                                              hashing_algorithm, 
                                              s, 
                                              key, 
                                              self.content_part())
        return False # If we didn't match keyprints, we fail verification

    



class CurrencyDescriptionDocument(ContainerWithSignature):
    """
    Lets test a bit
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
    '[["standard_version","http://opencoin.org/OpenCoinProtocol/1.0"],["currency_identifier","http://opencent.net/OpenCent"],["short_currency_identifier","OC"],["issuer_service_location","opencoin://issuer.opencent.net:8002"],["denominations",[1,2,5,10,20,50,100,200,500,1000]],["issuer_cipher_suite",["sha-256","rsa","rsa"]],["issuer_public_master_key","foobar"]]'
 
    >>> cdd3 = CDD().fromJson(j)
    >>> cdd3 == cdd
    True

    And now, lets play with a signed CDD
    >>> import crypto
    >>> private_key = crypto.createRSAKeyPair(1024)
    >>> public_key = private_key.newPublicKeyPair()

    >>> public_key.hasPrivate()
    False

    >>> cdd4 = CDD(standard_version = 'http://opencoin.org/OpenCoinProtocol/1.0',
    ...            currency_identifier = 'http://opencent.net/OpenCent',
    ...            short_currency_identifier = 'OC',
    ...            issuer_service_location = 'opencoin://issuer.opencent.net:8002',
    ...            denominations = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000],
    ...            issuer_cipher_suite = ['SHA256HashingAlgorithm', 'RSASigningAlgorithm', 'RSABlindingAlgorithm'],
    ...            issuer_public_master_key = public_key.toJson())
    
    >>> hasher = crypto.SHA256HashingAlgorithm()
    >>> signer = crypto.RSASigningAlgorithm(private_key)

    >>> keyprint = hasher.update(cdd4.issuer_public_master_key).digest()
    >>> signature = signer.sign(hasher.reset(cdd4.content_part()).digest())

    >>> cdd4.adSignatures.append(Signature(keyprint, signature))

    #>>> cdd4.verify_self()
    #True

    """

    
    fields = ['standard_version', 
              'currency_identifier', 
              'short_currency_identifier', 
              'issuer_service_location', 
              'denominations', 
              'issuer_cipher_suite', 
              'issuer_public_master_key']


    def __init__(self,**kwargs):
        ContainerWithSignature.__init__(self, **kwargs)
        self.adSignatures = kwargs.get('adSignatures',[])

    def verify_self(self):
        """Verifies the self-signed certificate."""
        return self.verifySignature(self.issuer_cipher_suite.signing, 
                                    self.issuer_cipher_suite.hashing, 
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

    codecs = {'key_identifier':{'encode':base64.encode,'decode':base64.decode},}


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



class DSDBKey(ContainerWithAdSignatures):
    
    fields=['key_identifier', 
            'not_before', 
            'not_after', 
            'cipher', 
            'public_key']

    codecs = {'key_identifier':{'encode':base64.encode,'decode':base64.decode},}

    def verify_with_CDD(self, currency_description_document):
        """verify_with_CDD verifies the signatures of the dsdb key against the CDD."""

        cdd = currency_description_document

        for s in self.signatures:
            if s.keyprint == cdd.signature.keyprint: # we have the same signer
                return self.verifyAdSignatures(cdd.issuer_cipher_suite.signing, 
                                               cdd.issuer_cipher_suite.hashing, 
                                               cdd.issuer_public_master_key, 
                                               s)
        return False #if we get here, no valid signatures were found
        
    def verify_time(self, time):
        """Whether the time is between self.not_before and self.not_after"""

        return time > self.not_before and time < self.not_after


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


    def check_similar_to_obfuscated_blank(self, blank):
        """check_similar_to_obfuscated_blank verifies that the coin and the blank both 
           refer to a specific minting of a coin without verifying the serials."""

        if self.standard_identifier != blank.standard_identifier:
            return False

        if self.currency_identifier != blank.currency_identifier:
            return False

        if self.denomination != blank.denomination:
            return False

        if self.key_identifier != blank.key_identifier:
            return False

        return True # We have performed allt he cbecks we can

    def check_obfuscated_blank_serial(self, blank, dsdb_certificate):
        """Attempts to ensure the the blank and the dsdb_key have the same serial. 
           This may require additional information if we use something like ElGamal."""

        enc = dsdb_certificate.cipher(dsdb_certificate.public_key, self.serial)
        obfuscated_serial = enc.encrypt()
        return obfuscated_serial == blank.serial

    def newObfuscatedBlank(self, dsdb_certificate):
        """Returns an CurrencyObfuscatedBlank for a certian DSDB."""
        enc = dsdb_certificate.cipher(dsdb_certificate.public_key)
        enc.update(self.serial)
        obfuscatedserial = enc.encrypt()
        return CurrencyObfuscatedBlank(self.standard_identifier, 
                                       self.currency_identifier, 
                                       self.denomination,
                                       self.key_identifier, 
                                       obfuscatedserial)


class CurrencyObfuscatedBlank(CurrencyBase):

    fields = ['standard_identifier', 
              'currency_identifier', 
              'denomination', 
              'key_identifier', 
              'serial']

    content_id = 'Currency'   

if __name__ == "__main__":
    import doctest
    doctest.testmod()
