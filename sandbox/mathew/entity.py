import containers
import message

class Entity:
    pass

class IssuerDSDBEntity(Entity):
    def __init__(self, cdd, mk, dsdb_cert, dsdb_database, minted, dsdb_cert_length,
                 mk_before_length, mk_coin_not_after_length, mk_mint_not_after_length, mint_waiting):
        self.cdd = cdd # the cdd
        self.mk = mk # a list of all active minting keys
        self.dsdb_cert = dsdb_cert # the dsdb_certificate
        self.dsdb_database = dsdb_database # the doublespending database
        self.minted = minted # dictionary the coins we have minted which haven't been sent by id
        self.mint_waiting = mint_waiting # a dictionary of a reason why it isn't fetchable and either the minted or unminted blanks
        self.mint_failures = mint_failures # a dictionary of a reason why the request failed
        self.dsdb_cert_length #XXX The time the dsdb cert is good for
        self.mk_before_length #XXX the time to do the not_before for
        self.mk_coin_not_after_length # XXX the time to do the coin_not_after for
        self.mk_mint_not_after_length # XXX the time to do the mint_not_after for


    
    def newDSDBMessageType(self):
        import dsdb
        
        server = message.MessageStatuses.getBaseServer()
        messageType = message.MessageType(server)
        me = dsdb.HandlerManager(messageType, self)

        return me

    def newISMessageType(self):
        import issuer

        server = message.MessageStatuses.getBaseServer()
        messageType = message.MessageType(server)
        me = dsdb.HandlerManager(messageType, self)

        return me


class WalletEntity(Entity):
    def __init__(self, cdds=None, minting_keys=None, coins=None, requests=None, universe=None):
        self.cdds = cdds # dictionary of cdds by currency identifier
        
        self.minting_keys_key_id = {} # dictionary of minting keys by key_identifier
        self.minting_keys_denomination = {} # dictionary by currency identifier of (dictionary by denomination of (list of valid minting keys))
        # minting keys is a list of all keys which we sort into minting_keys_key_id and minting_keys_denomination if valid
        for key in minting_keys:
            if now <= key.coin_not_after and cdds.has_key(key.currency_identifier): 
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

        self.coins = [] # list of coins
        for coin in coins: # only add keys we have the (cdd and) minting key for
            if self.minting_keys_key_id.has_key(coin.key_identifier):
                self.coins.append(coin)
            else:
                print('Invalid coin: %s', coin)

        self.requests = requests # dictionary of requests by request id with the blinding factor and blanks
        
        self.universe = universe # holder of all the entities to allow connections to work
        
    def newMerchantWalletMessageType(self):
        import merchantwallet
        
        server = message.MessageStatuses.getBaseServer()
        messageType = message.MessageType(server)
        me = mercantwallet.HandlerManager(messageType, self)

        return me

    def connectToDSDB(messageType, dsdb_certificate):
        """connects the messageType to a dsdb_certificate."""
        #FIXME: the dsdb_certificate does not have an address to contact it at. Using the key_id for now
        address = dsdb_certificate.key_identifier

        connection = self._connectDSDB(address)

        # this makes the input/output functions work
        linkMessageTypes(connection, messageType)
        
    def connectToIS(messageType, currency_description_document):
        """connects the messageType to a IS."""
        address = currency_description_document.issuer_service_location

        connection = self._connectIS(address)

        # this makes the iput/output functions work
        linkMessageTypes(connection, messageType)

    def connectToMerchantWallet(messageType, address):
        """connects the messageType to a merchant wallet."""
        connection = self._connectMerchantWallet(address)

        # this makes the input/output functins work
        linkMessageTypes(connection, messageType)

    def _connectToIS(self, address):
        """use universe to get a new messageType for an IS."""
        return self.universe.getNewIssuerMessageType(address)

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
    def __init__():
        self.issuers = {}
        self.dsdbs = {}
        self.merchantwallets = {}

    def addIS(self, isEntity, address):
        self.issuers[address] = isEntity

    def addDSDB(self, dsdbEntity, address):
        self.issuers[address] = dsdbEntity

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
    signing = crypto.RSASigningAlgorithm()
    blinding = crypto.RSABlindingAlgorithm()

    cipher_suite = crypto.CryptoCollection(signing=signing, blinding=blinding, hashing=hashing)

    cdd = containers.CurrencyDescriptionDocument(
            'OpenCoin standard', 'OpenCent', 'OC', 'location', denominations, cipher_suite, key)

    cdd.sign_self()

    return cdd

def createMK(denomination, cdd, not_before, mint_not_after, coin_not_after):
    import crypto

    key = crypto.createRSAKeyPair(1024)

    if denomination not in cdd.denominations:
        raise MessageError('denomination not in denominations')

    if mint_not_after <= not_before or mint_not_after > coin_not_after:
        raise MessageError('those variables do not make sense')

    hashing = cdd.issuer_cipher_suite.hashing
    hashing.reset()
    hashing.update(key.__str__())

    minting_key = containers.MintingKey(hashing.digest(), cdd.currency_identifier, denomination, not_before,
                                        mint_not_after, coin_not_after, key)

    signing = cdd.issuer_cipher_suite.signing
    hash.reset()
    hash.update(minting_key.content_part())
    signature = signing(hash.digest())

    minting_key.signature = signature
    
    if not minting_key.verify_with_CDD(cdd):
        raise MessageError('Just made a bad minting key')

    return minting_key
    
def linkMessageTypes(messagetype1, messagetype2):
    """links the output functions of two MessageTypes to the input of the other."""
    messagetype1._outputFunction = messagetype2.addInput
    messagetype2._outputFunction = messagetype1.addInput


       
