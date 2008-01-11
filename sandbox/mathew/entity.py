import containers
import message

class Entity:
    pass

class IssuerDSDBEntity(Entity):
    def __init__(self, cdd, dsdb_key, mk=None, dsdb_database=None, minted=None, dsdb_cert_length=None,
                 mk_before_length=None, mk_coin_not_after_length=None, mk_mint_not_after_length=None, mint_waiting=None,
                 mint_failures=None):
        self.cdd = cdd # the cdd
        #self.mk = mk # a list of all active minting keys
        self.dsdb_key = dsdb_key # the dsdb_certificate
        self.dsdb_database = dsdb_database # the doublespending database, a dictionary by mint_key of
                                           #            (dictionaries by serial of (tuple of ('Spent',),  ('Locked', time_expire, _id))))
        self.minted = minted # dictionary the coins we have minted which haven't been sent by id
        self.mint_waiting = mint_waiting # a dictionary of a reason why it isn't fetchable and either the minted or unminted blanks
        self.mint_failures = mint_failures # a dictionary of a reason why the request failed
        self.dsdb_cert_length = dsdb_cert_length #XXX The time the dsdb cert is good for
        self.mk_before_length = mk_before_length #XXX the time to do the not_before for
        self.mk_coin_not_after_length = mk_coin_not_after_length # XXX the time to do the coin_not_after for
        self.mk_mint_not_after_length = mk_mint_not_after_length # XXX the time to do the mint_not_after for
        self.minting_keys_key_id = {} # dictionary of minting keys by key_identifier
        self.minting_keys_denomination = {} # dictionary by by denomination of (list of valid minting keys)

        self.addMintingKeys(mk)

        if not dsdb_database: # setup a empty database
            self.dsdb_database = {}

    def addMintingKeys(self, keys):
        """Adds minting keys from the list of keys to minting_key_key_id and minting_keys_denomination."""
        import time; now=time.time() #hack for now
        # minting keys is a list of all keys which we sort into minting_keys_key_id and minting_keys_denomination if valid
        for key in keys:
            if now <= key.coin_not_after and self.cdd.currency_identifier == key.currency_identifier: 
                # we don't need keys which have expired or we don't have cdd
                self.minting_keys_key_id[key.key_identifier] = key
                if not self.minting_keys_denomination.has_key(key.denomination):
                    self.minting_keys_denomination[key.denomination] = []
                self.minting_keys_denomination[key.denomination].append(key)
            else:
                print('Invalid minting key: %s', key)
    
    def newDSDBMessageType(self):
        import dsdb
        
        server = message.MessageStatuses.getBaseServer()
        messageType = message.MessageType(server)
        me = dsdb.HandlerManager(messageType, self)

        return messageType

    def newISMessageType(self):
        import issuer

        server = message.MessageStatuses.getBaseServer()
        messageType = message.MessageType(server)
        me = issuer.HandlerManager(messageType, self)

        return messageType


class WalletEntity(Entity):
    def __init__(self, cdds=None, minting_keys=None, coins=None, requests=None, universe=None):
        self.cdds = cdds # dictionary of cdds by currency identifier
        
        self.minting_keys_key_id = {} # dictionary of minting keys by key_identifier
        self.minting_keys_denomination = {} # dictionary by currency identifier of (dictionary by denomination of (list of valid minting keys))
        self.addMintingKeys(minting_keys)


        self.coins = [] # list of coins
        for coin in coins: # only add keys we have the (cdd and) minting key for
            if self.minting_keys_key_id.has_key(coin.key_identifier):
                self.coins.append(coin)
            else:
                print('Invalid coin: %s', coin)

        self.requests = requests # dictionary of requests by request id with the blinding factor and blanks
        
        self.universe = universe # holder of all the entities to allow connections to work
        
    def addMintingKeys(self, minting_keys):
        """Adds minting keys to self.minting_keys_key_id and self.minging_keys_denomination."""
        # minting keys is a list of all keys which we sort into minting_keys_key_id and minting_keys_denomination if valid
        import time; now = time.time() #FIXME hack for time
        
        for key in minting_keys:
            if now <= key.coin_not_after and self.cdds.has_key(key.currency_identifier): 
                # we don't need keys which have expired or we don't have cdd
                self.minting_keys_key_id[key.key_identifier] = key
                if not self.minting_keys_denomination.has_key(key.key_identifier):
                    self.minting_keys_denomination[key.key_identifier] = {}
                table = self.minting_keys_denomination[key.key_identifier]
                if not table.has_key(key.denomination):
                    table[key.denomination] = []
                table[key.denomination].append(key)
            else:
                print('Invalid minting key: %s', key)

    def newMerchantWalletMessageType(self):
        import merchantwallet
        
        server = message.MessageStatuses.getBaseServer()
        messageType = message.MessageType(server)
        me = merchantwallet.MerchantWalletManager(messageType, self)

        return messageType

    def connectToDSDB(self, messageType, dsdb_certificate):
        """connects the messageType to a dsdb_certificate."""
        #FIXME: the dsdb_certificate does not have an address to contact it at. Using the key_id for now
        address = dsdb_certificate.key_identifier

        connection = self._connectToDSDB(address)

        # this makes the input/output functions work
        linkMessageTypes(connection, messageType)
        
    def connectToIS(self, messageType, currency_description_document):
        """connects the messageType to a IS."""
        address = currency_description_document.issuer_service_location

        connection = self._connectToIS(address)

        # this makes the iput/output functions work
        linkMessageTypes(connection, messageType)

    def connectToMerchantWallet(self, messageType, address):
        """connects the messageType to a merchant wallet."""
        connection = self._connectToMerchantWallet(address)

        # this makes the input/output functins work
        linkMessageTypes(connection, messageType)

    def _connectToIS(self, address):
        """use universe to get a new messageType for an IS."""
        return self.universe.getNewISMessageType(address)

    def _connectToDSDB(self, address):
        """use universe to get a new messageType for a DSDB."""
        return self.universe.getNewDSDBMessageType(address)

    def _connectToMerchantWallet(self, address):
        """use universe to get a new messageType for a merchantwallet."""
        return self.universe.getNewMerchantWalletMessageType(address)

    def newConsumerWalletMessageType(self, coins):
        import consumerwallet

        client = message.MessageStatuses.getBaseClient()
        messageType = message.MessageType(client)
        me = consumerwallet.ConsumerWalletManager(messageType, self, coins)

        return me

    def spendCoins(self, address, currency_identifier, denominations):
        """Performs a transaction of coins with wallet at address of coins of type
        currency_identifier for all denominations in denominations.
        """

        # find the coins we are going to spend
        coins = []
        lookingFor = denominations[:]
        for coin in self.coins:
            if not lookingFor:
                break
            if coin.currency_identifier == currency_identifier and coin.denomination in lookingFor: # we are a match
                coins.append(coin)
                lookingFor.remove(coin.denomination)

        if lookingFor:
            raise MessageError('do not have all the coins I am looking for')

        myWallet = self.newConsumerWalletMessageType(coins)
        otherWallet = self._connectToMerchantWallet(address)

        # link the two wallets together
        linkMessageTypes(myWallet.walletMessageType, otherWallet)

        # start the whole shebang!
        myWallet.startConversation()


class UniverseContainer:
    def __init__(self):
        self.issuers = {}
        self.dsdbs = {}
        self.merchantwallets = {}

    def addIS(self, isEntity, address):
        self.issuers[address] = isEntity

    def addDSDB(self, dsdbEntity, address):
        self.dsdbs[address] = dsdbEntity

    def addMerchantWallet(self, walletEntity, address):
        self.merchantwallets[address] = walletEntity

    def getNewDSDBMessageType(self, address):
        entity = self.dsdbs[address]
        return entity.newDSDBMessageType()

    def getNewISMessageType(self, address):
        entity = self.issuers[address]
        return entity.newISMessageType()

    def getNewMerchantWalletMessageType(self, address):
        entity = self.merchantwallets[address]
        return entity.newMerchantWalletMessageType()
    
def createCDD():
    import crypto

    key = crypto.createRSAKeyPair(1024)

    denominations = ['1', '5', '25', '100', '500', '2500', '10000']

    hashing = crypto.SHA256HashingAlgorithm()
    signing = crypto.RSASigningAlgorithm(key)
    blinding = crypto.RSABlindingAlgorithm(key)

    cipher_suite = crypto.CryptoContainer(signing=signing, blinding=blinding, hashing=hashing)

    cdd = containers.CurrencyDescriptionDocument(
            'OpenCoin standard', 'OpenCent', 'OC', 'IssuerLocation', denominations, cipher_suite, key)

    cdd.sign_self(signing, hashing)

    return cdd

def createMK(denomination, cdd, not_before, mint_not_after, coin_not_after):
    import crypto

    key = crypto.createRSAKeyPair(1024)

    if denomination not in cdd.denominations:
        raise MessageError('denomination not in denominations')

    if mint_not_after <= not_before or mint_not_after > coin_not_after:
        raise MessageError('those variables do not make sense')

    hashing = cdd.issuer_cipher_suite.hashing.__class__()
    hashing.reset()
    hashing.update(key.__str__())

    minting_key = containers.MintKey(hashing.digest(), cdd.currency_identifier, denomination, not_before,
                                        mint_not_after, coin_not_after, key)

    signing = cdd.issuer_cipher_suite.signing

    minting_key.setSignature(cdd.issuer_public_master_key, signing, hashing)
    
    if not minting_key.verify_with_CDD(cdd):
        raise MessageError('Just made a bad minting key')

    return minting_key

def createDSDBCertificate(cdd, not_before, not_after):
    import crypto

    key = crypto.createRSAKeyPair(1024)

    if not_before > not_after:
        raise MessageError('that does not make sense')

    hashing = cdd.issuer_cipher_suite.hashing.__class__(str(key))
    signing = cdd.issuer_cipher_suite.signing

    encrypting = crypto.RSAEncryptionAlgorithm(key)

    cert = containers.DSDBKey(hashing.digest(), not_before, not_after, encrypting, key)

    cert.addAdSignature(cdd.issuer_public_master_key, signing, hashing)
    
    if not cert.verify_with_CDD(cdd):
        raise MessageErrror('Just made a bad DSDB cert')

    return cert

def linkMessageTypes(messagetype1, messagetype2):
    """links the output functions of two MessageTypes to the input of the other."""
    messagetype1._outputFunction = messagetype2.addInput
    messagetype2._outputFunction = messagetype1.addInput


def makeCoin(cdd, mintingKey):
    blank = containers.CurrencyBlank(cdd.standard_version, cdd.currency_identifier, mintingKey.denomination, mintingKey.key_identifier)
    blank.generateSerial()

    hashing = cdd.issuer_cipher_suite.hashing.__class__()
    signing = cdd.issuer_cipher_suite.signing.__class__(mintingKey.public_key)

    hashing.update(blank.content_part())
    signature = signing.sign(hashing.digest())

    coin = blank.newCoin(signature, cdd, mintingKey)

    return coin
    
