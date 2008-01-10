class Container:
    def __init__(self):
        pass

class Signature:
    def __init__(self, keyprint, signature):
        self.keyprint = keyprint
        self.signature = signature

class ContainerWithBase(Container):
    def __init__(self):
        Container.__init__(self)

    def _verifyASignature(self, signature, key, content_part):
        return do_crypto(content_part, signature, key)
    
class ContainerWithSignature(ContainerWithBase):
    def __init__(self, signature):
        ContainerWithBase.__init__(self)
        self.signature = signature

    def verifySignature(self, signature, key):
        return self._verifyASignature(signature, key, self.content_part())

    def performSigning(self, key):
        contentpart = self.content_part()
        signature = do_crypto(contentpart, key)
        keyprint = fingerprint(key)
        return Signature(keyprint, signature)

    def setSignature(self, key):
        """This sets the signature part of the container."""
        self.signature = self.performSigning(key)
    
class ContainerWithAdSignatures(ContainerWithBase):
    def __init__(self, signatures):
        ContainerWithBase.__init__(self)
        self.signatures = signatures

    def verifyAdSignatures(self, key, keyprint):
        for s in self.signatures:
            if s.keyprint == keyprint:
                return self._verifyASignature(s, key, self.content_part())
        return False # If we didn't match keyprints, we fail verification

class CurrencyDescriptionDocument(ContainerWithSignature):
    def __init__(self, standard_version, currency_identifier, short_currency_identifier, issuer_service_location, 
                 denominations, issuer_cipher_suite, issuer_public_master_key, signature=None, adSignatures=None):
        ContainerWithSignature.__init__(self, signature)
        self.standard_version = standard_version
        self.currency_identifier = currency_identifier
        self.short_currency_identifier = short_currency_identifier
        self.issuer_service_location = issuer_service_location
        self.denominations = denominations
        self.issuer_cipher_suite = issuer_cipher_suite
        self.issuer_public_master_key = issuer_public_master_key
        self.adSignatures = adSignatures

    def content_part(self):
        #return encode(CurrencyDescriptionDocument (all the parts of content_part)
        content = []
        content.append('"%s"="%s"' % ('standard version', self.standard_version))
        content.append('"%s"="%s"' % ('currency identifier', self.currency_identifier))
        content.append('"%s"="%s"' % ('short currency identifier', self.short_currency_identifier))
        content.append('"%s"="%s"' % ('issuer service location', self.issuer_service_location))
        content.append('"%s"="%s"' % ('denominations', self.denominations))
        content.append('"%s"="%s"' % ('issuer cipher suite', self.issuer_cipher_suite))
        content.append('"%s"="%s"' % ('issuer public master key', self.issuer_public_master_key))
        return 'ContentDescriptionDocument={' + ';'.join(content) + '}'

    def verify_self(self):
        """Verifies the self-signed certificate."""
        return self.verifySignature(signature.signature, self.issuer_public_master_key)

    def sign_self(self):
        """Signs the self-signed certificate."""
        return self.setSignature(self.issuer_public_master_key)

class MintKey(ContainerWithSignature):
    def __init__(self, key_identifier, currency_identifier, denomination, not_before, key_not_after, coin_not_after,
                 public_key, signature = None):
        ContainerWithSignature.__init__(self, signature)
        self.key_identifier = key_identifier
        self.currency_identifier = currency_identifier
        self.denomination = denomination
        self.not_before = not_before
        self.key_not_after = key_not_after
        self.coin_not_after = coin_not_after
        self.public_key = public_key
        self.signature = signature

    def content_part(self):
        #return encode(MintKey (all the parts of content_part) )
        content = []
        content.append('"%s"="%s"' % ('key identifier', self.key_identifier))
        content.append('"%s"="%s"' % ('currency identifier', self.currency_identifier))
        content.append('"%s"="%s"' % ('denomination', self.denomination))
        content.append('"%s"="%s"' % ('not_before', self.not_before))
        content.append('"%s"="%s"' % ('key_not_after', self.key_not_after))
        content.append('"%s"="%s"' % ('coin_not_after', self.coin_not_after))
        content.append('"%s"="%s"' % ('public key', self.public_key))
        return 'MintKey={' + ';'.join(content) + '}'

    def verify_with_CDD(self, currency_description_document):
        """verify_with_CDD verifies the mint key against the CDD ensuring valid values matching the CDD and the signature validity."""
        cdd = currency_description_document
        if self.public_key != cdd.signature.keyprint:
            return False # if they aren't the same master key, it isn't valid

        if self.denomination not in cdd.denominations:
            return False # if we are not a denomination, we aren't valid

        if self.currency_identifier != cdd.currency_identifier:
            return False # we have to be using the same currency identifier

        if self.key_identifier != hashFunction(self.public_key):
            return False # the key identifier is not valid

        if self.signature:
            return self.verifySignature(self.signature, cdd.public_master_key)
        else:
            return False # if we have no signature, we are not valid (or verifiable)
        
    def verify_time(self, time):
        """Whether the container is currently valid. Returns a tuple of (can_mint, can_redeem)."""
        can_mint = time > self.not_before and time < self.key_not_after
        can_redeem = time > self.not_before and time < self.coin_not_after

        return can_mint and can_redeem

class DSDBKey(ContainerWithAdSignatures):
    def __init__(self, key_identifier, not_before, not_after, public_key, signatures = None):
        ContainerWithAdSignature.__init__(self, signatures)
        self.key_identifier = key_identifier
        self.not_before = not_before
        self.not_after = not_after
        self.public_key = public_key

    def content_part(self):
        #return encode(MintKey (all the parts of content_part) )
        content = []
        content.append('"%s"="%s"' % ('key identifier', self.key_identifier))
        content.append('"%s"="%s"' % ('not_before', self.not_before))
        content.append('"%s"="%s"' % ('not_after', self.not_after))
        content.append('"%s"="%s"' % ('public key', self.public_key))
        return 'DSDBKey={' + ';'.join(content) + '}'

    def verify_with_CDD(self, currency_description_document):
        """verify_with_CDD verifies the signatures of the dsdb key against the CDD."""
        cdd = currency_description_document

        for s in signatures:
            if s.keyprint == cdd.signature.keyprint: # we have the same signer
                return self.verifySignature(s, cdd.master_public_key)
        return False #if we get here, no valid signatures were found
        
    def verify_time(self, time):
        """Whether the time is between self.not_before and self.not_after"""
        return time > self.not_before and time < self.not_after


class CurrencyBase:
    def __init__(self, standard_identifier, currency_identifier, denomination, key_identifier, serial=None):
        self.standard_identifier = standard_identifier
        self.currency_identifier = currency_identifier
        self.denomination = denomination
        self.key_identifier = key_identifier
        self.serial = serial

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
    def __init__(self, standard_identifier, currency_identifier, denomination, key_identifier, serial=None, blind_factor=None):
        CurrencyBase.__init__(self, standard_identifier, currency_identifier, denomination, key_identifier, serial)

        self.blind_factor = blind_factor

    def generateSerial(self):
        if self.serial:
            raise MessageError('gah! trying to make another serial.')
        
        self.serial = crypto._r.getRandomString(128)

    def content_part(self):
        if not self.serial:
            raise SomeError('Serial is not set')
        do_some_encode_thing()

    def blind_blank(self):
        """Returns the blinded value of the hash of the coin for signing."""
        if self.blind_factor:
            raise MessageError('CurrenyBlank already has a blind factor')

        blinding = self.currency_identifier.issuer_cipher_suite.blinding
        hashing = self.currency_identifier.issuer_cipher_suite.hashing
        blinding.reset()
        hashing.reset()

        hashing.update(self.content_part())
        blinding.update(hashing.digest())
        
        self.blind_value, self.blind_factor = blinding.blind()

        return self.blind_value

    def unblind_signature(self, signature):
        """Returns the unblinded value of the blinded signature."""
        blinding = self.currency_identifier.issuer_cipher_suite.blinding

        return blinding.unblind(signature, self.blind_factor)

    def newCoin(self, signature, currency_description_document=None, minting_key=None):
        """Returns a coin using the unblinded signature.
        Performs tests if currency_description_document and minting_key are provided.
        """
        coin = CurrencyCoin(self.standard_identifier, self.currency_identifier, self.denomination, self.key_identifier,
                            self.serial, signature)
        
        
        # if only one is provided, we have an error. Purposefully use an 'or' for the test to get an exception later
        if currency_description_document or minting_key:
            coin.validate_with_CDD_and_MintingKey(currency_description_document, minting_key)
        
        return coin
        
class CurrencyCoin(CurrencyBase):
    def __init__(self, standard_identifier, currency_identifier, denomination, key_identifier, serial, signature):
        CurrencyBase.__init__(self, standard_identifier, currency_identifier, denomination, key_identifier, serial)
        self.signature = signature

    def validate_with_CDD_and_MintingKey(self, currency_description_document, minting_key):
        if not CurrencyBase.validate_with_CDD_and_MintingKey(self, currency_description_document, minting_key):
            return False

        key = minting_key.public_key
        signer = currency_description_document.issuer_cipher_suite.signing.__class__(key)
        hasher = currency_description_document.issuer_cipher_suite.hashing

        hasher.reset()
        hasher.update(self.content_part())
        signer.update(hasher.digest())
        
        if not signer.verify(self.signature):
            return False

        return True

    def content_part(self):
        do_some_encode_thing()

    def check_similar_to_obfuscated_blank(blank):
        """check_similar_to_obfuscated_blank verifies that the coin and the blank both refer to a specific minting of a coin without verifying the serials."""
        if self.standard_identifier != blank.standard_identifier:
            return False

        if self.currency_identifier != blank.currency_identifier:
            return False

        if self.denomination != blank.denomination:
            return False

        if self.key_identifier != blank.key_identifier:
            return False

        return True # We have performed allt he cbecks we can

    def check_obfuscated_blank_serial(blank, dsdb_certificate):
        """Attempts to ensure the the blank and the dsdb_key have the same serial. This may require additional information if we use something like ElGamal."""
        obfuscated_serial = obfuscated_crypto(self.serial, dsdb_certificate.public_key)
        return obfuscated_serial == blank.serial

    def newObfuscatedBlank(self, dsdb_certificate):
        """Returns an CurrencyObfuscatedBlank for a certian DSDB."""
        obfuscatedserial = obfuscated_crypto(self.serial, dsdb_certificate.public_key)
        return CurrencyObfuscatedBlank(self.standard_identifier, self.currency_identifier, self.denomination,
                                       self.key_identifier, obfuscatedserial)

class CurrencyObfuscatedBlank(CurrencyBase):
    def __init__(self, standard_identifier, currency_identifier, denomination, key_identifier, serial):
        CurrencyBase.__init__(self, standard_identifier, currency_identifier, denomination, key_identifier, serial)

    def content_part(self):
        do_some_encode_thing()
