import protocols
from messages import Message

class Entity(object):

    def toPython(self):
        return self.__dict__

    def fromPython(self,data):
        self.__dict__ = data     
        
    def toJson(self):
        return json.write(self.toPython())

    def fromJson(self,text):
        return self.fromPython(json.read(text))


    def serialize(self):
        import pickle,base64
        return base64.b64encode(pickle.dumps(self))        

##################### time ################################
def getTime():
    import time
    return time.time()

#################### Wallet ###############################

class Wallet(Entity):
    "A Wallet"

    def __init__(self):
        self.coins = [] # The coins in the wallet
        self.waitingTransfers = {} # The transfers we have done a TRANSFER_TOKEN_REQUEST on
                                   # key is transaction_id, val is the set of blanks
        self.otherCoins = [] # Coins we received from another wallet, waiting to Redeem
        self.getTime = getTime # The getTime function
        self.keyids = {} # MintKeys by key_identifier
        self.cdds = {} # CDDs by [CurrencyIdentifier][version]. version of None gives current version key
        self.issuer_transports = {} # The issuer_transports open by location


    def addCDD(self, CDD):
        """addCDD adds a CDD to the wallet's CDDs. The CDDs are not trusted, just stored."""
        version = dict(CDD.options)['version']
        currencydict = self.cdds.setdefault(CDD.currency_identifier, {})
        if version in currencydict:
            import warnings
            warnings.warn('Tried to add version "%s" which already existed' % version) 
        currencydict[version] = CDD

    def setCurrentCDD(self, CDD):
        """setCurrentCDD sets the default CDD for a currency to CDD. It adds if necessary."""
        version = dict(CDD.options)['version']
        if version not in self.cdds.setdefault(CDD.currency_identifier, {}):
            self.addCDD(CDD)
        self.cdds[CDD.currency_identifier][None] = version

    def getCDD(self, currency_identifier, version=None):
        """Returns a specific version of a CDD.
        
        If version is None, returns the current version.
        """
        if not version:
            version = self.cdds[currency_identifier][None]
        return self.cdds[currency_identifier][version]

    def fetchMintKey(self, transport, denominations=None, keyids=None, time=None):
        protocol = protocols.fetchMintKeyProtocol(denominations=denominations, keyids=keyids, time=time)
        transport.setProtocol(protocol)
        transport.start()
        protocol.newMessage(Message(None))

        # Get the keys direct from the protcool.
        retreivedKeys = protocol.keycerts

        for key in retreivedKeys:
            try:
                cdd = self.getCDD(key.currency_identifier)
            except KeyError:
                continue # try the other currencies

            if key.key_identifier not in self.keyids:
                if key.verify_with_CDD(cdd):
                    self.keyids[key.key_identifier] = key
                else:
                    raise Exception('CDD: %s\n\nMintKey: %s' % (cdd, key))
                    raise Exception('Got a bad key')

    def sendMoney(self,transport):
        """FOR TESTING PURPOSES ONLY. Sends some money to the given transport."""

        protocol = protocols.WalletSenderProtocol(self)
        transport.setProtocol(protocol)
        transport.start()
        #Trigger execution of the protocol
        protocol.newMessage(Message(None))

    def receiveMoney(self,transport):
        """FOR TESTING PURPOSES ONLY. sets up the wallet to receive tokens from another wallet."""
        protocol = protocols.WalletRecipientProtocol(self)
        transport.setProtocol(protocol)
        transport.start()

    def sendCoins(self, transport, target, amount):
        """sendCoins sends coins over a transport to a target of a certain amount.
        
        We need to be careful to try every possible working combination of coins to
        to an amount. To test, we muck in the internals of the coin sending to make
        sure that we get the right coins. (Note: This would be easier if we just
        had a function to get the coins for an amount.)

        To test the functionality we steal the transport, and when a message occurs,
        we steal the tokens directly out of the protocol. This is highly dependant
        on the internal details of TokenSpendSender and the transport/protocol
        relationship.

        >>> class transport:
        ...     def setProtocol(self, protocol): 
        ...         protocol.transport = self
        ...         self.protocol = protocol
        ...     def start(self): pass
        ...     def write(self, info): print sum(self.protocol.coins) # Steal the values 
        
        >>> wallet = Wallet()
        >>> test = lambda x: wallet.sendCoins(transport(), '', x)

        >>> from tests import coins

        Okay. Do some simple checks to make sure things work at all
        
        >>> wallet.coins = [coins[0][0]]
        >>> test(1)
        1

        >>> wallet.coins = [coins[0][0], coins[2][0]]
        >>> test(6)
        6

        >>> wallet.coins = [coins[2][0], coins[0][0]]
        >>> test(6)
        6

        Okay. Now we'll do some more advanced tests of the system. We start off with
        a specifically selected group of coins:
        3 coins of denomination 2
        1 coin of denomination 5
        1 coin of denomination 10
        >>> test_coins = [coins[1][0], coins[1][1], coins[1][2], coins[2][0], coins[3][0]]
        
        >>> test_coins[0].denomination == test_coins[1].denomination == test_coins[2].denomination
        True
        >>> test_coins[0].denomination
        '2'
        >>> test_coins[3].denomination
        '5'
        >>> test_coins[4].denomination
        '10'
        >>> sum(test_coins)
        21

        Now, this group of coins has some specific properties. There are only certain ways to
        get certain values of coins. We'll be testing 6, 11, 15, 16, 19, and 21

        6 = 2 + 2 + 2
        >>> wallet.coins = test_coins
        >>> sum(wallet.coins)
        21
        >>> test(6)
        6

        11 = 5 + 2 + 2 + 2
        >>> wallet.coins = test_coins
        >>> test(11)
        11

        15 = 10 + 5
        >>> wallet.coins = test_coins
        >>> test(15)
        15

        16 = 10 + 2 + 2 + 2
        >>> wallet.coins = test_coins
        >>> test(16)
        16

        19 = 10 + 5 + 2 + 2
        >>> wallet.coins = test_coins
        >>> test(19)
        19

        21 = 10 + 5 + 2 + 2 + 2
        >>> wallet.coins = [coins[1][0], coins[1][1], coins[1][2], coins[2][0], coins[3][0]]
        >>> test(21)
        21

        Okay. Some things we can't do.

        8 = Impossible
        >>> wallet.coins = test_coins
        >>> test(8)
        Traceback (most recent call last):
        UnableToDoError: Not enough tokens

        22 = Impossible
        >>> wallet.coins = test_coins
        >>> test(22)
        Traceback (most recent call last):
        UnableToDoError: Not enough tokens

        Okay. Now we want to make sure we don't lose coins if there is an exception
        that occurs.

        >>> test = lambda x: wallet.sendCoins('foo', '', x)
        >>> wallet.coins = test_coins
        >>> test(21)
        Traceback (most recent call last):
        AttributeError: 'str' object has no attribute ...

        >>> wallet.coins == test_coins
        True

        """
        if sum(self.coins) < amount:
            raise UnableToDoError('Not enough tokens')

        denominations = {} # A dictionary of coins by denomination
        denomination_list = [] # A list of the denomination of every coin
        for coin in self.coins:
            denominations.setdefault(coin.denomination, [])
            denominations[coin.denomination].append(coin)
            denomination_list.append(coin.denomination)
            
        int_denomination_list = [int(d) for d in denomination_list]
        int_denomination_list.sort(reverse=True) # sort from high to low

        def my_split(piece_list, sum):
            # piece_list must be sorted from high to low
            
            # Delete all coins greater than sum
            my_list = [p for p in piece_list if p <= sum]

            while my_list:
                test_piece = my_list[0]
                del my_list[0]

                if test_piece == sum: 
                    return [test_piece]

                test_partition = my_split(my_list, sum - test_piece)

                if test_partition == [] :
                    # Partitioning the rest failed, so remove all pieces of this size
                    my_list = [p for p in my_list if p < test_piece]
                else :
                    test_partition.append(test_piece)
                    return test_partition

            # if we are here, we don't have a set of coins that works
            return []

        if sum(int_denomination_list) != sum(self.coins):
            raise Exception('denomination_list and self.coins differ!')

        denominations_to_use = my_split(int_denomination_list, amount)

        if not denominations_to_use:
            raise UnableToDoError('Not enough tokens')

        denominations_to_use = [str(d) for d in denominations_to_use]

        to_use = []
        for denomination in denominations_to_use:
            to_use.append(denominations[denomination].pop()) # Make sure we remove the coins from denominations!

        for coin in to_use: # Remove the coins to prevent accidental double spending
            self.coins.remove(coin)

        try:
            protocol = protocols.TokenSpendSender(to_use,target)
            transport.setProtocol(protocol)
            transport.start()
            protocol.newMessage(Message(None))
        except: # Catch everything. Losing coins is death. We re-raise anyways.
            # If we had an error at the protocol or transport layer, make sure we don't lose the coins
            self.coins.extend(to_use)
            raise

        # FIXME: protocol.done is not the correct thing to be using here. protocol.done
        # specifies that we are ready to hangup the connection, when instead, we want to
        # know that the specific protocol we are using is complete (protocols.py:58)
        if not protocol.done:
            # If we didn't succeed, re-add the coins to the wallet.
            # Of course, we may need to remint, so FIXME: look at this
            self.coins.extend(to_use)

    def listen(self,transport):
        """listens on a transport, answers a handshake, and performs wallet server type things
        >>> import transports
        >>> w = Wallet()
        >>> stt = transports.SimpleTestTransport()
        >>> w.listen(stt)
        >>> stt.send('HANDSHAKE',[['protocol', 'opencoin 1.0']])
        <Message('HANDSHAKE_ACCEPT',[['protocol', 'opencoin 1.0']])>
        >>> stt.send('sendMoney',[1,2])
        <Message('Receipt',None)>
        """
        protocol = protocols.answerHandshakeProtocol(arguments=self,
                                                     sendMoney=protocols.WalletRecipientProtocol,
                                                     SUM_ANNOUNCE=protocols.TokenSpendRecipient)
        transport.setProtocol(protocol)
        transport.start()


    def confirmReceiveCoins(self,walletid,sum,target):
        """confirmReceiveCoins verifies with the user the transaction can occur.

        confirmReceiveCoins returns 'trust' if they accept the transaction with a certain
        wallet for a sum regarding a target.

        Except that this argument then gets used as the action in 'redeem', 'exhange', 'trust'
        telling us what to do with the tokens after we get them.
        """
        return 'redeem'


    def transferTokens(self, transport, target, blanks, coins, type):
        """transferTokens performs a TOKEN_TRANSFER with a issuer.

        if blanks are provided, transferTokens performs all checks to convert
        the tokens to blinds and unblind the signatures when complete.
        """
        import base64
        blinds = []
        keydict = {}

        if blanks:
            cdd = self.getCDD(blanks[0].currency_identifier)

        for blank in blanks:
            li = keydict.setdefault(blank.encodeField('key_identifier'), [])
            li.append(base64.b64encode(blank.blind_blank(cdd, self.keyids[blank.key_identifier])))

        for key_id in keydict:
            blinds.append([key_id, keydict[key_id]])

        protocol = protocols.TransferTokenSender(target, blinds, coins, type=type)
        transport.setProtocol(protocol)
        transport.start()
        protocol.newMessage(Message(None))

        if type == 'mint':
            if protocol.result == 1: # If set, we got a TRANSFER_TOKEN_ACCEPT
                self.addTransferBlanks(protocol.transaction_id, blanks)
                self.finishTransfer(protocol.transaction_id, protocol.blinds)
            elif protocol.result == 2: #If set, we got a TRANSFER_TOKEN_DELAY
                self.addTransferBlanks(protocol.transaction_id, blanks)
        
        elif type == 'exchange':
            if protocol.result == 1: # If set, we got a TRANSFER_TOKEN_ACCEPT
                self.addTransferBlanks(protocol.transaction_id, blanks)
                self.finishTransfer(protocol.transaction_id, protocol.blinds)
            elif protocol.result == 2: # If set, we got a TRANSFER_TOKEN_DELAY
                self.addTransferBlanks(protocol.transaction_id, blanks)
                self.removeCoins(coins)

        elif type == 'redeem':
            if protocol.result == 1: # If set, we got a TRANSFER_TOKEN_ACCEPT
                self.removeCoins(coins)
                
        else:
            raise NotImplementedError()
                
    def handleIncomingCoins(self,coins,action,reason):
        """handleIncomingCoins is a bridge between receiving coins from a wallet and redeeming.

        it seems to be anther part of receiveCoins. Basically, given some coins, it attempts to
        redeem them with the IS.

        returns True if successful. Nothing if not
        FIXME: It doesn't seem to know if the transfer works?
        """
        # Q: What is reason for reason?
        # A: reason is describing what the tokens are going to be for, e.g 'a book'

        cdd = self.getCDD(coins[0].currency_identifier) # The default CDD for the currency

        # Get the IS location
        issuer_service_location = cdd.issuer_service_location

        if action == 'redeem':
            transport = self.getIssuerTransport(issuer_service_location)
            self.otherCoins.extend(coins) # Deposit them in otherCoins
            if transport:
                self.transferTokens(transport,'my account',[],coins,'redeem')

        elif action == 'exchange':
            transport = self.getIssuerTransport(issuer_service_location)
            # FIXME: should make some amount of blanks and sends the blinds in a TTR
            raise NotImplementedError
        
        elif action == 'trust':
            self.coins.append(coins) # Move the coins into our wallet, trusting that they are good
            
        else:
            raise Exception('Unknown action')

        return True


    def getIssuerTransport(self, location):
        if location in self.issuer_transports:
            return self.issuer_transports[location]
        else:
            return self.makeIssuerTransport(location)

    def makeIssuerTransport(self, location):
        """creates a transport to the issuer at a location."""
        # NOTE: if using in testing and want an issuerTransport that you can not connect to,
        # overwrite with lambda location: return None if you want things to silently fail,
        # and lambda location: raise FIXME exception to signify the connection failed
        if not location.startswith('opencoin://'):
            raise Exception('Improperly formatted transport')

        # strip off opencoin://
        fullstring = location[len('opencoin://'):]

        try:
            address, port = fullstring.split(':')
        except ValueError:
            raise Exception('Improperly formatted transport')

        import transports

        sct = transports.SocketClientTransport(address, int(port))

        self.addIssuerTransport(location, sct)

        return sct
        
    def addIssuerTransport(self, location, transport):
        self.issuer_transports[location] = transport

    def delIssuerTransport(self, location):
        del self.issuer_transports[location]

    def removeCoins(self, coins):
        """removeCoins removes a set of coins from self.coins or self.otherCoins

        This is used so we can cleanly remove coins after a redemption. Coins being
        used for a redemption may come from the wallet itself or from another wallet.
        """
        # NOTE: This assumes that self.coins and self.otherCoins do not contain
        # copies of the same coin
        for c in coins:
            try:
                self.coins.remove(c)
            except ValueError:
                self.otherCoins.remove(c)

    def addTransferBlanks(self, transaction_id, blanks):
        self.waitingTransfers[transaction_id] = blanks

    def finishTransfer(self, transaction_id, blinds):
        """Finishes a transfer where we minted. Takes blinds and makes coins."""
        raise NotImplementedError("We never go here!") #FIXME: Completely untested! Use it!
        from containers import BlankError

        #FIXME: What do we do if a coin is bad?
        coins = []
        blanks = self.waitingTransfers[transaction_id]

        # We have no way of being sure we have the same amount of blanks and blinds afaict.
        # We'll try to make as many coins as we can, then error
        shortest = min(len(blanks), len(blinds))

        cdd = self.getCDD(blanks[0].currency_identifier) # all blanks have the same CDD in a transaction

        #FIXME: We need to make sure we atleast have the same number of blanks and blinds at the protocol level!
        # Well, maybe not the protocol level. We know we received the full message because we can decode the json.
        # At this point, either our memory is screwed, or the IS screwed up. No real way to fix it either.
        for i in range(shortest):
            blank = blanks[i]
            blind = blinds[i]
            try:
                signature = blank.unblind_signature(blind)
            except CryptoError:
                # Skip this one, go to the next
                continue
                
            mintKey = self.keyids[blank.key_identifier]

            try:
                coins.append(blank.newCoin(signature, cdd, mintKey))
            except BlankError:
                # Skip this one, go to the next
                continue

        for coin in coins:
            if coin not in self.coins:
                self.coins.append(coin)

        del self.waitingTransfers[transaction_id]

class UnableToDoError(Exception):
    pass


#################### Issuer ###############################

class IssuerEntity(Entity):
    """The issuer.
    IssuerEntity contains all the subparts of the issuer,
    an IS, a DSDB, and a mint
    
    >>> i = IssuerEntity()
    >>> i.createMasterKey(keylength=256)
    """
    
    def __init__(self):
        self.dsdb = DSDB()
        self.mint = Mint()
        self.issuer = Issuer(dsdb=self.dsdb, mint=self.mint)

        self.masterKey = None

        self.getTime = getTime
    
    def createMasterKey(self,keylength=1024):
        import crypto

        self.key_alg = crypto.createRSAKeyPair

        masterKey = self.key_alg(keylength, public=False)
        self.masterKey = masterKey

    def makeCDD(self, currency_identifier, short_currency_identifier, denominations, 
                issuer_service_location, options):
        from containers import CDD, Signature
        import crypto
        
        ics = crypto.CryptoContainer(signing=crypto.RSASigningAlgorithm,
                                     blinding=crypto.RSABlindingAlgorithm,
                                     hashing=crypto.SHA256HashingAlgorithm)

        public_key = self.masterKey.newPublicKeyPair()
        
        cdd = CDD(standard_identifier='http://opencoin.org/OpenCoinProtocol/1.0',
                  currency_identifier=currency_identifier,
                  short_currency_identifier=short_currency_identifier,
                  denominations=denominations,
                  options=options,
                  issuer_cipher_suite=ics,
                  issuer_service_location=issuer_service_location,
                  issuer_public_master_key = public_key)


        signature = Signature(keyprint=ics.hashing(str(public_key)).digest(),
                              signature=ics.signing(self.masterKey).sign(ics.hashing(cdd.content_part()).digest()))

        cdd.signature = signature

        if not cdd.verify_self():
            raise Exception('Just created an invalid CDD')
     
        self.issuer.addCDD(cdd)

    def createSignedMintKey(self, denomination, not_before, key_not_after, token_not_after,
                            signing_key=None, bypass_cdd_checks=False, size=1024):
        """Have the Mint create a new key and sign the public key."""
        import containers

        cdd = self.issuer.getCDD()

        if denomination not in cdd.denominations and not bypass_cdd_checks:
            raise Exception('Trying to create a bad denomination')
       
        if not signing_key:
            signing_key = self.masterKey

        hash_alg = cdd.issuer_cipher_suite.hashing
        sign_alg = cdd.issuer_cipher_suite.signing
        key_alg = self.key_alg

        public = self.mint.createNewKey(hash_alg, key_alg, size)

        keyid = public.key_id(hash_alg)
        
        mintKey = containers.MintKey(key_identifier=keyid,
                                     currency_identifier=cdd.currency_identifier,
                                     denomination=denomination,
                                     not_before=not_before,
                                     key_not_after=key_not_after,
                                     token_not_after=token_not_after,
                                     public_key=public)

        signer = sign_alg(signing_key)
        hashed_content = hash_alg(mintKey.content_part()).digest()
        sig = containers.Signature(keyprint = signing_key.key_id(hash_alg),
                                   signature = signer.sign(hashed_content))

        mintKey.signature = sig

        if not bypass_cdd_checks:
            if not mintKey.verify_with_CDD(cdd):
                raise Exception('Created a bad mintKey')
        
        self.issuer.addMintKey(mintKey)

        return mintKey


class Issuer(Entity):
    """An IS

    >>> ie = IssuerEntity()
    >>> issuer = ie.issuer
    """
    def __init__(self, dsdb, mint):
        self.dsdb = dsdb 
        self.mint = mint

        self.cdds = {} # CDDs by version
        self.current_cdd_version = None
        self.transactions = {} # transactions by transaction_id
        
        self.getTime = getTime

        # Signed minting keys
        self.mintKeysByDenomination = {} # List of mint keys for a denomination
        self.mintKeysByKeyID = {}

        self.keyids = self.mintKeysByKeyID

    def getKeyByDenomination(self, denomination, time):
        #FIXME: Is this supposed to return the mint keys valid for minting at a certain time?
        try:
            keys = self.mintKeysByDenomination[denomination]
        except KeyError:
            raise KeyFetchError

        not_before = [k for k in keys if time >= k.not_before]
        key_not_after = [k for k in keys if time <= k.key_not_after]

        # If we were python2.4+, we could use sets and take the intersection
        response = []
        for k in not_before:
            if k in key_not_after:
                response.append(k)

        if not response: # No denominations found valid at that time
            raise KeyFetchError

        return response
    
    def getKeyById(self,keyid):
        try:
            return self.mintKeysByKeyID[keyid]
        except KeyError:            
            raise KeyFetchError

    def addMintKey(self, mintKey):
        denomination = mintKey.denomination
        self.mintKeysByDenomination.setdefault(denomination, []).append(mintKey)
        self.mintKeysByKeyID[mintKey.key_identifier] = mintKey

    def addCDD(self, cdd):
        """Adds a CDD to the issuer

        >>> import tests
        >>> issuer = Issuer(mint=None, dsdb=None)
        """
        version = dict(cdd.options)['version']

        if version in self.cdds:
            import warnings
            warnings.warn('Trying to add the same version of CDD')

        if not cdd.verify_self():
            raise Exception('Tried to add an invalid CDD')

        self.cdds[version] = cdd

    def setCurrentCDDVersion(self, version):
        if self.current_cdd_version == version:
            import warnings
            warnings.warn('Setting CDD version to the same version')

        self.current_cdd_version = version

    def getCDD(self, version=None):
        """Returns a specific CDD. If version=None, returns the current CDD."""
        if version == None:
            version = self.current_cdd_version

        return self.cdds[version]

    def getCurrentCDDVersion(self):
        """Returns the current CDD version."""
        if not self.current_cdd_version:
            raise Exception('No current CDD version.')

        return self.current_cdd_version

    #### Entity protocols ####
    
    def giveMintKey(self,transport):
        protocol = protocols.giveMintKeyProtocol(self)
        transport.setProtocol(protocol)
        transport.start()

    def listen(self,transport):
        """Listen is the main operator between an issuer and a wallet.
        >>> import transports, tests, base64
        >>> tid = base64.b64encode('foobar')
        >>> ie = tests.makeIssuerEntity()
        >>> import calendar
        >>> ie.getTime = lambda: calendar.timegm((2008,01,31,0,0,0)) 
        >>> ie.issuer.getTime = ie.mint.getTime = ie.dsdb.getTime = ie.getTime
        >>> stt = transports.SimpleTestTransport()
        >>> ie.issuer.listen(stt)
        >>> stt.send('HANDSHAKE',[['protocol', 'opencoin 1.0']])
        <Message('HANDSHAKE_ACCEPT',[['protocol', 'opencoin 1.0'], ['cdd_version', '0']])>

        >>> stt.send('TRANSFER_TOKEN_REQUEST',[tid, 'my account', [], [tests.coinA.toPython()], [['type', 'redeem']]])
        <Message('TRANSFER_TOKEN_ACCEPT',['Zm9vYmFy', []])>

        >>> stt.send('MINT_KEY_FETCH_DENOMINATION',[['1'], '0'])
        <Message('MINT_KEY_PASS',[...]])>

        >>> stt.send('MINT_KEY_FETCH_KEYID', [tests.mint_key1.encodeField('key_identifier')])
        <Message('MINT_KEY_PASS',[...]])>

        >>> stt.send('FETCH_CDD_REQUEST', '0')
        <Message('FETCH_CDD_PASS',[...])>

        >>> stt.send('foo')
        <Message('PROTOCOL_ERROR','send again...')>

        >>> stt.send('FETCH_CDD_REQUEST', '0')
        <Message('FETCH_CDD_PASS',[...])>

        >>> stt.send('GOODBYE')
        <Message('GOODBYE',None)>
        >>> stt.send('foobar')
        """
        if hasattr(transport, 'protocol') and transport.protocol:
            # transport will only have protocol if we are looping on ourselves. Don't
            # setup protocol again. Just reset the transport to use the protocol and
            # reset the protocol itself
            transport.setProtocol(self.protocol)
            self.protocol.newState(self.protocol.start) 

        else:
            protocol = protocols.answerHandshakeProtocol(handshake_options=[['cdd_version',self.getCurrentCDDVersion()]],
                                                         arguments=self,
                                                         TRANSFER_TOKEN_REQUEST=protocols.TransferTokenRecipient,
                                                         MINT_KEY_FETCH_DENOMINATION=protocols.giveMintKeyProtocol,
                                                         MINT_KEY_FETCH_KEYID=protocols.giveMintKeyProtocol,
                                                         FETCH_CDD_REQUEST=protocols.giveCDDProtocol)
            self.protocol = protocol
            transport.autoreset = self.listen
            transport.setProtocol(protocol)
            transport.start()


    #### Helper functions ####

    def transferToTarget(self,target,coins):
        """Transfers coins to a target.
        
        Returns True if success, False if error.
        """
        return True

    def debitTarget(self,target,blinds):
        """Debits a target by an amount of what blinds is worth
        
        Returns True if success, False if error.
        """
        return True
        
    def transferTokenRequestHelper(self, transaction_id, target, blindslist, tokens, options):
        if 'type' not in options:
            return 'REJECT', ['Options', 'Reject', []]

        # Start doing things
        if options['type'] == 'redeem':

            success, obsolete, failures = self.redeemTokens(transaction_id, tokens, options)

            if not success:
                # tokens are not locked if not successful
                self.addTransaction(transaction_id, type='Redeem', status='Reject', added=self.getTime(),
                                    obsolete=obsolete, response=failures)
                return 'REJECT', failures

            # transmit funds
            if not self.transferToTarget(target, tokens):
                self.dsdb.unlock(transaction_id)
                failures = ['Target', 'Rejected', []]
                self.addTransaction(transaction_id, type='Redeem', status='Reject', added=self.getTime(),
                                    obsolete=obsolete, response=failures)
                return 'REJECT', failures

            # register the tokens as spent
            self.dsdb.spend(transaction_id, tokens)

            self.addTransaction(transaction_id, type='Redeem', status='Accept', added=self.getTime(),
                                obsolete=obsolete, response=failures, signed_blinds=[])
            return 'ACCEPT', []

        elif options['type'] == 'mint':

            # check that we have the keys
            try:
                blinds = [[self.keyids[keyid], blinds] for keyid, blinds in blindslist]
            except KeyError:
                obsolete = self.getTime() + 86400 # FIXME: Hardcoded min obsolete
                details = []
                for keyid, blinds in blindslist:
                    try:
                        mintKey = self.keyids[keyid]
                        details.append('None')
                        obsolete = max(obsolete, mintKey.token_not_after)
                    except KeyError:
                        details.append('None')
                self.addTransaction(transaction_id, type='Mint', status='Failure', added=self.getTime(),
                                    obsolete=obsolete, response=['Blind', 'See detail', details], numblinds=0)
                return 'REJECT', ['Blind', 'See detail', details]

            numblinds = 0
            for key, blindslist in blinds:
                numblinds = numblinds + len(blindslist)

            # check that the keys are usable
            success, obsolete, failures = self.verifyMintableBlinds(blinds, options)
            if not success:
                self.addTransaction(transaction_id, type='Mint', status='Failure', added=self.getTime(),
                                    obsolete=obsolete, numblinds=numblinds, response=failures)
                return 'REJECT', failures

            #check target
            if not self.debitTarget(target,blindslist):
                self.addTransaction(transaction_id, type='Mint', status='Failure', added=self.getTime(),
                                    obsolete=obsolete, numblinds=numblinds, response=['Target', 'Rejected', []])
                return 'REJECT', ['Target', 'Rejected', []]

            success, additional = self.submitMintableBlinds(transaction_id, blinds, options)
            if not success:
                failures = additional
                self.addTransaction(transaction_id, type='Mint', status='Failure', added=self.getTime(),
                                    obsolete=obsolete, numblinds=numblinds, response=failures)
                return 'REJECT', failures

            delay = additional
            self.addTransaction(transaction_id, type='Mint', status='Delayed', added=self.getTime(),
                                obsolete=obsolete, numblinds=numblinds, expected=self.getTime() + int(delay))
            # FIXME: If we can only send a delay, the only useful logic is in the if
            if delay != '0':
                return 'DELAY', str(delay)

            else:
                response, additional = self.resumeTransaction(transaction_id)
                if response == 'PASS':
                    signed_blinds = additional
                    return 'ACCEPT', signed_blinds
                elif response == 'REJECT':
                    failures = additional
                    return 'REJECT', failures
                elif response == 'DELAY':
                    time = additional
                    return 'DELAY', time
                else:
                    raise NotImplementedError('Got an impossible response')

        elif options['type'] == 'exchange':

            # check tokens
            success, obsolete, failures = self.redeemTokens(transaction_id, tokens, options)
            if not success:
                self.addTransaction(transaction_id, type='Exchange', status='Reject', added=self.getTime(),
                                    obsolete=obsolete, target=target, options=options, amount=0,
                                    response=failures)
                return 'REJECT', failures

            # And onto the blinds

            # check that we have the keys
            try:
                blinds = [[self.keyids[keyid], blinds] for keyid, blinds in blindslist]
            except KeyError:
                details = []
                for keyid, blinds in blindslist:
                    try:
                        mintKey = self.keyids[keyid]
                        details.append('None')
                        obsolete = max(obsolete, mintKey.token_not_after)
                    except KeyError:
                        details.append('None')
                self.addTransaction(transaction_id, type='Exchange', status='Failure', added=self.getTime(),
                                    obsolete=obsolete, response=['Blind', 'See detail', details], numblinds=0,
                                    target=target, options=options, amount=0)
                return 'REJECT', ['Blind', 'See detail', details]

            #check target
            if not self.debitTarget(target,blindslist):
                self.dsdb.unlock(transaction_id)
                self.addTransaction(transaction_id, type='Exchange', status='Failure', added=self.getTime(),
                                    obsolete=obsolete, response=['Target', 'Rejected', []], numblinds=0,
                                    target=target, options=options, amount=0)
                return 'REJECT', ['Target', 'Rejected', []]

            # check mintifyable blinds
            success, an_obsolete, failures = self.verifyMintableBlinds(blinds, options)
            obsolete = max(obsolete, an_obsolete)

            if not success:
                self.addTransaction(transaction_id, type='Exchange', status='Failure', added=self.getTime(),
                                    obsolete=obsolete, response=failures, numblinds=0,
                                    target=target, options=options, amount=0)
                return 'REJECT', failures

            # Make sure that we have the same amount of tokens as mintings
            total = 0
            for b in blinds:
                total += int(b[0].denomination) * len(b[1])

            if total != sum(tokens):
                self.dsdb.unlock(transaction_id)
                self.addTransaction(transaction_id, type='Exchange', status='Failure', added=self.getTime(),
                                    obsolete=obsolete, response=['Generic', 'Rejected', []], numblinds=0,
                                    target=target, options=options, amount=0)
                return 'REJECT', ['Generic', 'Rejected', []]

            # FIXME: This code implements the 'mark as spent if we send a delay'
            #        method of handling delayed minting and any problems. However
            # FIXME  we have not implemented the solution, allowing reminting with
            #        the value of the money stored.

            success, additional = self.submitMintableBlinds(transaction_id, blinds, options)
            if not success:
                self.dsdb.unlock(transaction_id)
                failures = additional
                self.addTransaction(transaction_id, type='Exchange', status='Failure', added=self.getTime(),
                                    obsolete=obsolete, response=failures, numblinds=0,
                                    target=target, options=options, amount=0)
                return 'REJECT', failures

            delay = additional

            # calculate numblinds and amount
            numblinds = 0
            for key, blindslist in blinds:
                numblinds = numblinds + len(blindslist)

            self.addTransaction(transaction_id, type='Exchange', status='Delayed', added=self.getTime(),
                                obsolete=obsolete, response=failures, expected=self.getTime() + int(delay),
                                numblinds=numblinds, target=target, options=options, amount=0)
            # FIXME: If we can only send a delay, the only useful logic is in the if
            if delay != '0':
                self.updateTransaction(transaction_id, amount=total)
                self.spend(transaction_id, tokens)
                return 'DELAY', str(delay)

            else:
                response, additional = self.resumeTransaction(transaction_id)
                if response == 'PASS':
                    signed_blinds = additional
                    self.updateTransaction(transaction_id, amount=total)
                    self.dsdb.spend(transaction_id, tokens)
                    return 'ACCEPT', signed_blinds
                elif response == 'REJECT':
                    self.dsdb.unlock(transaction_id)
                    failures = additional
                    return 'REJECT', failures
                elif response == 'DELAY':
                    time = additional
                    self.updateTransaction(transaction_id, amount=total)
                    self.dsdb.spend(transaction_id, tokens)
                    return 'DELAY', str(time)
                else:
                    raise NotImplementedError('Got an impossible response')

        else:
            # FIXME: the transaction added pretends to be a Redeem since that carries little state
            # FIXME: hardcoded obsolete
            self.addTransaction(transaction_id, type='Redeem', status='Reject', added=self.getTime(),
                                obsolete=self.getTime() + 86400, response=['Options', 'Rejected', []])
            return 'REJECT', ['Option', 'Rejected', []]


    def redeemTokens(self, transaction_id, tokens, options):
        """verifies the tokens and locks them.
        
        Returns a tuple of (locked, obsolete, [failures|None]).
        Locked is a boolean specifying if the tokens are locked or not
        Obsolete is the time for obsolete
        Failures is a tuple of (type, reason, reason_detail) to return in case locked is false
        
        failures may be None if there were no failures

        """
        
        # This will fail if we try to lock with an already-known request_id.
        
        failures = []
        obsolete = self.getTime() + 86400 # FIXME: hardcoded min obsolete

        if not tokens:
            return ('TRANSFER_TOKEN_REJECT', obsolete, ('Token', 'Rejected', []))

        #check if tokens are valid
        for token in tokens:
            mintKey = self.mintKeysByKeyID.get(token.key_identifier, None)
            if mintKey:
                obsolete = max(obsolete, mintKey.token_not_after)
                if not token.validate_with_CDD_and_MintKey(self.getCDD(), mintKey):
                    failures.append(token)
            else:
                failures.append(token)
        
        if failures:
            details = []
            for token in tokens:
                mintKey = self.mintKeysByKeyID.get(token.key_identifier, None)
                if not mintKey:
                    details.append('Invalid key_identifier')
                    continue
                if token not in failures:
                    details.append('None')
                else:
                    details.append('Invalid token')

            return (False, obsolete, ('Token', 'See detail', details))

        #and not double spent
        try:
            #XXX have adjustable time for lock - not really needed. We unlock anyways, or spend
            self.dsdb.lock(transaction_id, tokens, 86400)
        except LockingError, e:
            reasons = []
            locking_error = False
            for token in tokens:
                status = self.dsdb.check(token)
                if status == 'Locked':
                    reasons.append('Token already spent')
                    locking_error = True
                elif status == 'Spent':
                    reasons.append('Token already spent')
                    locking_error = True
                elif status == 'Unlocked':
                    reasons.append('None')
                else:
                    raise NotImplementedError('Impossible string')
            if locking_error:
                return (False, obsolete, ('Token', 'See detail', reasons))
            else: # The problem is that the transaction_id is locked
                return (False, obsolete, ('Token', 'Rejected')) #FIXME: Should this be a different error?

        return (True, obsolete, None)

    def verifyMintableBlinds(self, blindslist, options):
        """returns a tuple of (success, obsolete, [failures|None]).
        
        success is a boolean set to true if they are mintable, otherwise false
        obsolete is the time till obsolescence
        failures is a tuple of (type, reason, reason-detail) to return in case of a reject
        
        blindslist is a list of [ [MintKey, [blind1, blind2...]], [MintKey....]]
        """
        
        #check the MintKeys for validity
        timeNow = self.getTime()
        obsolete = timeNow + 86400 # FIXME: Hardcoded min obsolete
        failures = []
        for mintKey, blindlist in blindslist:
            can_mint, can_redeem = mintKey.verify_time(timeNow)
            if not can_mint:
                # TODO: We need more logic here. can_mint only specifies if we are
                # between not_before and key_not_after. We may also need to do the
                # checking of the period of time the mint can mint but the IS cannot
                # send the key to the mint.
                failures.append(mintKey.key_identifier)
            obsolete = max(obsolete, mintKey.token_not_after)

        if failures:
            reasons = []
            for mintKey, blindlist in blindslist:
                if mintKey.key_identifier not in failures:
                    reasons.append('None')
                else:
                    if timeNow < mintKey.not_before:
                        reasons.append('Key too soon')
                    elif timeNow > mintKey.key_not_after: # TODO: Another place to put fudge time
                        reasons.append('Key expired')
                    else:
                        raise NotImplementedError('We failed for no reason')
            return (False, obsolete, ('Blind', 'See detail', reasons))

        else:
            return (True, obsolete, None)
            
    def submitMintableBlinds(self, transaction_id, blindslist, options):
        """returns a tuple of (success, [time|failures]) after submitting blinds to the mint.
        
        success is a boolean set to true if we successfully submitted. False otherwise.
                Note: it can be false if we have JITM and it has already failed.
        time is a stringint time in seconds to pass with a 'DELAY'
        failures is a tuple of (type, reason, reason_detail) to be passed if a 'REJECT'.
        """
        #FIXME: Do something with options
        time = self.mint.submit(transaction_id, blindslist)

        if not time: # we had an error
            response = self.resumeTransaction(transaction_id)
            failure, reasons = response
            if failure != 'REJECT':
                raise Exception('Got no time but failure was not reject')
            return (False, reasons)

        remaining = self.getTime() - time
        if remaining < 0:
            remaining = 0

        return (True, str(int(remaining)))

    def resumeTransaction(self, transaction_id):
        """Attempts to resume a transaction."""
        #FIXME: Only resumes minting/exchanges right now
        self.resumeTransactionHelper()
        return self.getTransaction(transaction_id)

    def resumeTransactionHelper(self):
        """Moves completed transactions from the mint to the IS."""
        try:
            transaction = self.mint.completedTransactions.pop(0) # FIFO
        except IndexError:
            return

        while True:
            transaction_id = transaction['transaction_id']
            del transaction['transaction_id']
            
            self.updateTransaction(transaction_id, **transaction)

            try:
                transaction = self.mint.completedTransactions.pop(0) # FIFO
            except IndexError:
                return
        
    # The transaction_id storage
    def addTransaction(self, transaction_id, type, status, added=None, obsolete=None, **kwargs):
        """adds a TRANSFER_TOKEN_REQUEST transaction

        transactions are held in self.transactions. Each transaction is a dict
        with certain fields depending on its value

        Each transaction has certain fields.
        All transactions have 'type', 'status', 'added', 'obsolete' fields.
        
        'added' is the time when the transaction was added
        'obsolete' is the time when the transaction will be obsolete
        If the 'type' is 'Mint':
            A field 'numblinds' of the number of blinds
            If 'status' is 'Delayed':
                A field 'expected' with the time expected to be complete
            If 'status' is 'Minted':
                A 'completed' field of when the minting was completed
                A 'signed_blinds' field of all the signed blinds
            If 'status' is 'Failure':
                A 'completed' field of when the minting was completed
                A 'response' field of the complete response for a _REJECT.
                        The response has all the information and should be
                        scrubbed of too much information somewhere else

        If the 'type' is 'Redeem':
            If 'status' is 'Accept':
                A 'signed_blinds' field of the signed blinds (empty)
            If 'status' is 'Reject':
                A 'response' field like the one for a 'type' of 'Mint'

        If the 'type' is 'Exchange':
            A field 'target' of the target for the exchange
            A 'options' field with the options for the exchange
            A 'amount' field with the amount of tokens in the exchange
            If 'status' is 'Reject':
                A 'response' field like the one for a 'type' of 'Mint'
            If 'status' is Failure':
                All the fields of a 'Failure' of type mint
            If 'status' is 'Delayed':
                All the fields of a 'Delayed' of type mint
            If 'status' is 'Minted':
                All the fields of a 'Minted' of type mint

        If the 'type' is 'Deleted':
            No other fields

        Now, it should be easy to see than an exchange just stores some extra
        information but otherwise works exactly like minting or redeeming.

        """
        transaction = kwargs
        transaction['type'] = type
        transaction['status'] = status
        transaction['added'] = added
        transaction['obsolete'] = obsolete

        transaction['lock'] = 'addTransaction'

        the_transaction = self.transactions.setdefault(transaction_id, transaction)
        if the_transaction is not transaction:
            raise Exception('Trying to add a transaction that already exists')

        del transaction['lock']
        return

    def getTransaction(self, transaction_id, lockobj=None):
        """Looks up the transaction and returns information for the protocol.

        Returns (type, value) where type is the string 'DELAY', 'REJECT', or
        'ACCEPT', and the value is the rest of the arguments needed (delay time,
        tuple of reject, or the signed blinds
        """
        try:
            transaction = self.transactions[transaction_id]
        except KeyError:
            return ('REJECT', ('Generic', 'Unknown transaction_id', ()))

        if not lockobj:
            lockobj = 'getTransaction'
        lock = transaction.setdefault('lock', lockobj)
        while lock is not lockobj:
            lock = transaction.setdefault('lock', lockobj)

        if transaction['type'] == 'Deleted':
            # The transaction has been deleted while we were locking, so
            # we need to get the transaction again and lock that one.
            # Ensure that everyone else can find out that the transaction
            # has been deleted, and call ourselves
            del transaction['lock']
            return self.getTransaction(transaction_id)

        if transaction['status'] == 'Delayed': # Mint or Exchange
            time = max(0, int(self.getTime() - transaction['expected']))
            del transaction['lock']
            return ('DELAY', str(time))

        elif transaction['status'] == 'Failure': # Mint or Exchange
            response = transaction['response']
            del transaction['lock']
            return ('REJECT', response)

        elif transaction['status'] == 'Reject': # Redeem or Exchange
            response = transaction['response']
            del transaction['lock']
            return ('REJECT', response)

        elif transaction['status'] == 'Minted': # Mint or Exchange
            signed_blinds = transaction['signed_blinds']
            del transaction['lock']
            return ('PASS', signed_blinds)

        elif transaction['status'] == 'Accept': # Redeem
            del transaction['lock']
            return ('PASS', [])

        else:
            raise NotImplementedError('Impossible status string: %s' % transaction['status'])

    def updateTransaction(self, transaction_id, lockobj=None, **kwargs):
        transaction = self.transactions[transaction_id]

        if not lockobj:
            lockobj = 'updateTransaction'
        lock = transaction.setdefault('lock', lockobj)
        while lock is not lockobj:
            lock = transaction.setdefault('lock', lockobj)

        if transaction['type'] == 'Deleted':
            del transaction['lock']
            return self.updateTransaction(transaction_id, kwargs)

        if transaction['type'] != 'Mint' and transaction['type'] != 'Exchange':
            del transaction['lock']
            raise Exception('Unable to update. Wrong type: %s' % transaction['type'])

        try:
            transaction.update(kwargs)
        except:
            del transaction['lock']
            raise

        if transaction['status'] != 'Delayed' and 'expected' in transaction:
            del transaction['expected']

        del transaction['lock']


    def delTransaction(self, transaction_id, lockobj=None):
        """deletes a transaction."""
        try:
            transaction = self.transactions(transaction_id)
        except KeyError:
            # FIXME: what should we do here?
            pass

        if not lockobj:
            lockobj = 'delTransaction'
        lock = transaction.setdefault('lock', lockobj)
        if lock is not lockobj:
            #FIXME: what should we do here. I'm just going to fail
            raise Exception('Trying to delete something in use')

        del self.transactions[transaction_id]
        transaction['status'] = 'Deleted'
        del transaction['lock']

        return
        

class KeyFetchError(Exception):
    pass


#################### dsdb ###############################

class LockingError(Exception):
    pass


class DSDB:
    """A double spending database.

    This DSDB is a simple DSDB. It only allows locking, unlocking, and
    spending a list of tokens. It is designed in a way to make it easier
    to make it race-safe (although that is not done yet).
    
    FIXME: It does extremely lazy evaluation of expiration of locks.
           When it tries to lock a token, it may find that there is already
           a lock on the token. It checks the times, and if the time has
           passed on the lock, it removes lock on all tokens in the transaction.

           This allows a possible DoS where they flood they DSDB with locks for
           fake keys, hoping to exhaust resources.

    NOTE: The functions of the DSDB have very simple logic. They only care about
          the values of key_identifier and serial for each token passed in. Any
          checking of the base types should be vetted prior to actually
          interfacing with the DSDB

          TODO: Maybe make an extractor for the token so we only see the parts
                we need. This would allow locking with one type and spending
                with another type. (e.g.: lock with Blanks, spend with Coins)

    >>> dsdb = DSDB()

    >>> class test:
    ...     def __init__(self, key_identifier, serial):
    ...         self.key_identifier = key_identifier
    ...         self.serial = serial

    >>> tokens = []
    >>> for i in range(10):
    ...     tokens.append(test('2', i))

    >>> token = tokens[-1]
    
    >>> dsdb.lock(3, (token,), 1)
    >>> dsdb.unlock(3)
    >>> dsdb.lock(3, (token,), 1)
    >>> dsdb.spend(3, (token,))
    >>> dsdb.unlock(3)
    Traceback (most recent call last):
       ...
    LockingError: Unknown transaction_id

    >>> dsdb.lock(4, (token,), 1)
    Traceback (most recent call last):
       ...
    LockingError: Token already spent
 
    Ensure trying to lock the same token twice doesn't work
    >>> dsdb.lock(4, (tokens[0], tokens[0]), 1)
    Traceback (most recent call last):
       ...
    LockingError: Token locked
    
    >>> dsdb.spend(4, (tokens[0], tokens[0]))
    Traceback (most recent call last):
       ...
    LockingError: Token locked

    Try to sneak in double token when already locked
    >>> dsdb.lock(4, tokens[:2], 1)
    >>> dsdb.spend(4, (tokens[0], tokens[0]))
    Traceback (most recent call last):
       ...
    LockingError: Unknown token

    Try to feed different tokens between the lock and spend
    >>> dsdb.spend(4, (tokens[0], tokens[2]))
    Traceback (most recent call last):
       ...
    LockingError: Unknown token

    Actually show we can handle multiple tokens for spending
    >>> dsdb.spend(4, (tokens[0], tokens[1]))

    And that the tokens can be in different orders between lock and spend
    >>> dsdb.lock(5, (tokens[2], tokens[3]), 1)
    >>> dsdb.spend(5, (tokens[3], tokens[2]))

    Respending a single token causes the entire transaction to fail
    >>> dsdb.spend(6, (tokens[4], tokens[3]))
    Traceback (most recent call last):
       ...
    LockingError: Token already spent

    But doesn't cause other tokens to be affected
    >>> dsdb.spend(6, (tokens[4],))

    We have to have locked tokens to spend if not automatic
    >>> dsdb.spend(7, (tokens[5],), automatic_lock=False)
    Traceback (most recent call last):
       ...
    LockingError: Unknown transaction_id

    And we can't relock (FIXME: I just made up this requirement.)
    >>> dsdb.lock(8, (tokens[6],), 1)
    
    >>> dsdb.lock(8, (tokens[6],), 1)
    Traceback (most recent call last):
       ...
    LockingError: id already locked

    Check to make sure that we can lock different key_id's and same serial
    >>> tokens[7].key_identifier = '2'
    >>> tokens[7].key_identifier
    '2'
    >>> dsdb.spend(9, (tokens[7], tokens[8]))
    """

    def __init__(self, database=None, locks=None):
        self.database = database or {} # a dictionary by MintKey of (dictionaries by
                                       #   serial of tuple of ('Spent',), ('Locked', time_expire, id))
        self.locks = locks or {} # a dictionary by id of tuple of (time_expire, list(tokens), {'lock':[...]})
                                 # the dict is to ensure only one thread plays with a transaction at a time
        self.getTime = getTime

    def lock(self, id, tokens, lock_duration, lockobj=None):
        """Lock the tokens.
        Tokens are taken as a group. It tries to lock each token one at a time. If it fails,
        it unwinds the locked tokens are reports a failure. If it succeeds, it adds the lock
        to the locks.
        Note: This function performs no checks on the validity of the coins, just blindly allows
        them to be locked
        """
        
        lock_time = lock_duration + self.getTime()

        unlock = not lockobj # if passed in a lock obj, do not automatically unlock

        if not lockobj:
            lockobj = ['lock']
        my_locks = (lock_time, [], {'Lock':lockobj})
        locks = self.locks.setdefault(id, my_locks)

        if my_locks is not locks:
            raise LockingError('id already locked')
        
        tokens = list(tokens[:])

        reason = None
        
        for token in tokens:
            key_dict = self.database.setdefault(token.key_identifier, {})
            
            my_lock = ('Locked', lock_time, id)
            lock = key_dict.setdefault(token.serial, my_lock)

            exit = False

            while lock is not my_lock:
                if lock[0] == 'Spent':
                    reason = 'Token already spent'
                    exit = True # break out of the for loop
                    break
                elif lock[0] == 'Locked':
                    # XXX: This implements lazy unlocking. Possible DoS attack vector
                    # Active unlocking would just break
                    if lock[1] > self.getTime(): # If the lock hasn't expired 
                        reason = 'Token locked'
                        exit = True
                        break
                    else:
                        try:
                            self.unlock(lock[2])
                        except LockingError:
                            pass # Only locking error is if it is already unlocked

                        # It should be unlocked. Now try to lock it again
                        lock = key_dict.setdefault(token.serial, my_lock)
                        
                else:
                    raise NotImplementedError('Impossible string')

            if exit: # break out of for loop
                break

            self.locks[id][1].append(token)

        if reason:
            self.unlock(id, lockobj)
            raise LockingError(reason)

        # clear the lock
        if unlock:
            del locks[2]['Lock']

        return

    def unlock(self, id, lockobj=None):
        """Unlocks an id from the dsdb.
        This only unlocks if a transaction is locked. If the transaction is
        completed and the token is spent, it cannot unlock.
        """
        
        lock = self.locks.get(id, None)
        if not lock:
            raise LockingError('Unknown transaction_id')

        if not lockobj:
            lockobj = ['unlock']

        lockcheck = lock[2].setdefault('Lock', lockobj)
        if lockcheck is not lockobj:
            raise LockingError('Unknown trasaction_id')

        # check to make sure we have the real and current lock
        if lock is not self.locks.get(id, None):
            raise LockingError('Unknown transaction_id')

        lazy_unlocked = False
        if lock[0] < self.getTime(): # unlock and then error
            lazy_unlocked = True

        for token in lock[1]:
            del self.database[token.key_identifier][token.serial]
            # Can not delete self.database[token.key_identifier] if it
            # is empty since it introduces a race condition

        del self.locks[id]

        if lazy_unlocked:
            raise LockingError('Unknown transaction_id')

        return

    def spend(self, id, tokens, automatic_lock=True, lockobj=None):
        """Spend verifies the tokens are locked (or locks them) and marks the tokens as spent.
        FIXME: Small tidbit of code in place for lazy unlocking.
        FIXME: automatic_lock doesn't automatically unlock if it locked and the spending fails (how can it though?)
        """
        if not lockobj:
            lockobj = ['spend']

        lock = self.locks.get(id, None)
        if not lock:
            if automatic_lock:
                # we can spend without locking, so lock now.
                self.lock(id, tokens, 86400, lockobj)
                lock = self.locks[id] # We have it locked
            else:
                raise LockingError('Unknown transaction_id')

        selflock = lock[2].setdefault('Lock', lockobj)
        if selflock is not lockobj:
            raise LockingError('Unknown transaction_id')

        if self.locks[id][0] < self.getTime():
            self.unlock(id, lockobj)
            raise LockingError('Unknown transaction_id')
        
        # check to ensure locked tokens are the same as current tokens.
        if len(set(tokens)) != len(self.locks[id][1]): # self.locks[id] is guarenteed to have unique values by lock
            del lock[2]['Lock']
            raise LockingError('Unknown token')

        for token in self.locks[id][1]:
            if token not in tokens:
                del lock[2]['Lock']
                raise LockingError('Unknown token')

        # we know all the tokens are valid. Change them to locked
        for token in self.locks[id][1]:
            self.database[token.key_identifier][token.serial] = ('Spent',)

        del self.locks[id]

        return

    def check(self, token):
        """Checks to see if a token is locked
        It checks a single token to see if it is locked or not.
        """
        
        key_dict = self.database.setdefault(token.key_identifier, {})
            
        # XXX: Implements lazy unlocking. Only unlock once.
        try:
            lock = self.database[token.key_identifier][token.serial]
        except KeyError:
            return 'Unlocked'

        if lock[0] == 'Spent':
            return 'Spent'
        elif lock[0] == 'Locked':
            # XXX: This implements lazy unlocking. Possible DoS attack vector
            # Active unlocking would just return 'Locked'
            if lock[1] > self.getTime(): # If the lock hasn't expired 
                return 'Locked'
            else:
                try:
                    self.unlock(lock[2])
                except LockingError:
                    pass # Only locking error is if it is already unlocked

                try:
                    lock = self.databasee[token.key_identifier][token.serial]
                except KeyError:
                    return 'Unlocked'

                if lock[0] == 'Spent':
                    return 'Spent'
                elif lock[0] == 'Locked':
                    return 'Locked'
                        
                else:
                    raise NotImplementedError('Impossible string')
        else:
            raise NotImplementedError('Impossible string')


class Mint:
    """A Mint is the minting agent for a currency. It has the 
    >>> m = Mint()
    >>> import calendar
    >>> m.getTime = lambda: calendar.timegm((2008,01,31,0,0,0))

    >>> import tests, crypto, base64
    >>> mintKey = tests.mintKeys[0]
    
    This bit is a touch of a hack. Keys are normally made in the mint
    >>> m.privatekeys[mintKey.key_identifier] = tests.keys512[0]

    >>> m.addMintKey(mintKey, crypto.RSASigningAlgorithm)

    >>> base64.b64encode(m.signNow(mintKey.key_identifier, 'abcdefghijklmnop'))
    'Mq4dqFpKZEvbl+4HeXh0rGrqBk6Fm2bnUjNiVgirDvOuQf4Ty6ZkvpqB95jMyiwNlhx8A1qZmQv5biLM40emUg=='
    
    >>> m.signNow('abcd', 'efg')
    Traceback (most recent call last):
    ...
    MintError: KeyError: 'abcd'

    """
    def __init__(self):
        self.keyids = {}
        self.privatekeys = {}
        self.sign_algs = {}
        self.getTime = getTime

        self.waitingTransactions = []
        self.completedTransactions = []

    def createNewKey(self, hash_alg, key_generator, size=1024):
        """creates a new keypair of a certain size.
        This is used by the IssuerEntity to create a new MintKey. The private
        key is only stored in the Mint

        Note: A different but seperation of powers would be for the IssuerEntity
        to send the keypair to the Mint. This would prevent contamination of the
        IssuerEntity in case the Mint is compromised

        >>> m = Mint()
        >>> import crypto
        >>> hash_alg = crypto.SHA256HashingAlgorithm
        >>> pub = m.createNewKey(hash_alg, crypto.createRSAKeyPair, 512)
        >>> pub.hasPrivate()
        False
        >>> key_id = pub.key_id(hash_alg)
        >>> pub == m.privatekeys[key_id].newPublicKeyPair()
        True
        """
        private, public = key_generator(size)
        self.privatekeys[private.key_id(hash_alg)] = private
        return public

    def addMintKey(self, mintKey, sign_alg):
        """adds a mintkey and sign_alg for a mint key to the mint.

        Requires the key to be in Mint.privateKeys (but verification
        does not occur to ensure the key is valid)

        >>> import crypto, tests
        >>> m = Mint()
        >>> mintKey = tests.mintKeys[0]
        >>> sign_alg = crypto.RSASigningAlgorithm

        First, make sure it fails when it doesn't know the key
        >>> m.addMintKey(mintKey, sign_alg)
        Traceback (most recent call last):
        MintError: Key not in Mint
        >>> mintKey.key_identifier not in m.keyids
        True
        >>> mintKey.key_identifier not in m.sign_algs
        True

        >>> m.privatekeys[mintKey.key_identifier] = None
        >>> m.addMintKey(mintKey, sign_alg)
        >>> m.keyids[mintKey.key_identifier] == mintKey
        True
        >>> m.sign_algs[mintKey.key_identifier] == sign_alg
        True
        """
        if mintKey.key_identifier not in self.privatekeys:
            raise MintError('Key not in Mint')
        self.keyids[mintKey.key_identifier] = mintKey
        self.sign_algs[mintKey.key_identifier] = sign_alg
        
    def signNow(self, key_identifier, blind):
        """Performs JITM of a blind.
        
        >>> m = Mint()
        >>> import crypto, tests, base64, calendar
        >>> hash_alg = crypto.SHA256HashingAlgorithm
        >>> sign_alg = crypto.RSASigningAlgorithm
        >>> mintKey = tests.mint_key1
        >>> m.privatekeys = {mintKey.key_identifier:tests.mint_private_key1}
        >>> m.addMintKey(mintKey, sign_alg)

        >>> blind = base64.b64decode('HIck+fim0TkjVupU1AeKpuSGN1CxLnDmT2jpBHMZSgdp' + 
        ...                          'YhKE90XoAsQVznljEn4NTXvRs5cXslWUNvcUeAuv2A==')

        This one passes
        >>> m.getTime = lambda: calendar.timegm((2008,01,31,0,0,0))
        >>> signedBlind = m.signNow(mintKey.key_identifier, blind)
        >>> base64.b64encode(signedBlind)
        'BJ597EK2lqlC4HN/C35v1MR5qG/476mzjS12qTomv8bjp6u9//W9RwOk6mijywTM6rg9quFuIXlTiVF9U6RJvA=='

        >>> m.getTime = lambda: mintKey.not_before - 1
        >>> m.signNow(mintKey.key_identifier, blind)
        Traceback (most recent call last):
        MintError: MintKey not valid for minting
        
        >>> m.getTime = lambda: mintKey.key_not_after + 1
        >>> m.signNow(mintKey.key_identifier, blind)
        Traceback (most recent call last):
        MintError: MintKey not valid for minting
        
        """
        from crypto import CryptoError
        try:
            sign_alg = self.sign_algs[key_identifier]
            signing_key = self.privatekeys[key_identifier]
            mintKey = self.keyids[key_identifier]
        except KeyError, reason:
            raise MintError("KeyError: %s" % reason)
            
        signer = sign_alg(signing_key)
        
        if mintKey.verify_time(self.getTime())[0]: # if can_sign
            try:
                signature = signer.sign(blind)
            except CryptoError, reason:
                raise MintError("CryptoError: %s" % reason)
            return signature
        else:
            raise MintError("MintKey not valid for minting")

    def submit(self, transaction_id, keys_and_blinds):
        """adds a minting transaction to the mint

        transaction_id is used to allow the transactions to be recalled
        keys_and_blinds is a list of [key_identifier, [blinds]]

        Returns the expected time the minting will be done

        >>> m = Mint()
        >>> m.performMinting = lambda: None # Make into a noop
        >>> m.getTime = lambda: 15180
        >>> m.submit('abcd', [])
        15180
        >>> m.waitingTransactions
        [{'status': 'Minting', 'added': 15180, 'kandb': [], 'transaction_id': 'abcd'}]

        >>> m.getTime = lambda: 15181
        >>> m.submit('efgh', [])
        15181
        >>> m.waitingTransactions
        [{'status': 'Minting', 'added': 15180, 'kandb': [], 'transaction_id': 'abcd'}, {'status': 'Minting', 'added': 15181, 'kandb': [], 'transaction_id': 'efgh'}]
        """
        # cheat for now and mint them before returning a time of now

        transaction = {'status':'Minting', 'kandb':keys_and_blinds,
                       'added':self.getTime(), 'transaction_id':transaction_id}
        self.waitingTransactions.append(transaction)

        # This is where we cheat
        self.performMinting()

        return self.getTime() # expect it to be done right now

    def performMinting(self):
        """Go through self.waitingTransactions and mint them all. Thread safe.
        
        >>> m = Mint()
        >>> import tests
        >>> realPerformMinting = m.performMinting
        >>> m.performMinting = lambda: None # Make into noop for now
        >>> m.getTime = lambda: 15180
        >>> m.submit('abcd', [])
        15180
        >>> m.getTime = lambda: 15181
        >>> m.submit('efgh', [])
        15181
        >>> m.getTime = lambda: 15182
        >>> m.performMinting = realPerformMinting

        We have waiting transactions and no completed transactions
        >>> m.waitingTransactions and True
        True
        >>> m.completedTransactions or False
        False

        And things work
        >>> m.performMinting()
        >>> m.waitingTransactions
        []
        >>> tests.printdictlist(m.completedTransactions)
        [{'added': 15180, 'completed': 15182, 'signed_blinds': [], 'status': 'Minted', 'transaction_id': 'abcd'}, {'added': 15181, 'completed': 15182, 'signed_blinds': [], 'status': 'Minted', 'transaction_id': 'efgh'}]

        It doesn't fail if there are no transactions
        >>> m.waitingTransactions
        []
        >>> m.performMinting()
        >>> tests.printdictlist(m.completedTransactions)
        [{'added': 15180, 'completed': 15182, 'signed_blinds': [], 'status': 'Minted', 'transaction_id': 'abcd'}, {'added': 15181, 'completed': 15182, 'signed_blinds': [], 'status': 'Minted', 'transaction_id': 'efgh'}]

        Okay. Now test failures
        >>> ie = tests.makeIssuerEntity()
        >>> m = ie.mint
        >>> m.getTime = lambda: tests.mint_key1.not_before
        >>> realPerformMinting = m.performMinting
        >>> m.performMinting = lambda: None
        >>> m.submit('abcd', [[tests.mint_key1, ['a' * (520/8)]]])
        1199145600
        >>> m.waitingTransactions and True
        True
        >>> m.completedTransactions
        []
        >>> realPerformMinting()
        >>> tests.printdictlist(m.completedTransactions)
        [{'added': 1199145600, 'completed': 1199145600, 'response': ['Blind', 'See detail', ['Unable to sign']], 'status': 'Failure', 'transaction_id': 'abcd'}]

        Test a more complicated failure. Valid should always pass. Invalid has two failures.
        Partial has a good key and a bad key. key_id has a key that the mint doesn't know about.
        We make sure we only get one failure per mint_key.
        >>> m.completedTransactions = []
        >>> valid = [tests.mint_key1, ['a' * 40, 'b' * 40]]
        >>> invalid = [tests.mint_key2, ['a' * (520/8), 'b' * (520/8)]]
        >>> partial = [tests.mint_key2, ['a' * 40, 'b' * (520/8)]]
        >>> key_id = [tests.mint_key3, ['a' * 40, 'b' * (520/8)]]
        >>> m.submit('abcd', [valid, invalid, key_id])
        1199145600
        >>> realPerformMinting()
        >>> tests.printdictlist(m.completedTransactions)
        [{'added': 1199145600, 'completed': 1199145600, 'response': ['Blind', 'See detail', ['None', 'Unable to sign', 'Invalid key_identifier']], 'status': 'Failure', 'transaction_id': 'abcd'}]

        Now I'm not sure if two sets with the same key_id is invalid or not.
        I'm testing seperately for now with partial since it has the same mintkey
        as invalid.
        >>> m.completedTransactions = []
        >>> m.submit('abcd', [partial, valid])
        1199145600
        >>> realPerformMinting()
        >>> tests.printdictlist(m.completedTransactions)
        [{'added': 1199145600, 'completed': 1199145600, 'response': ['Blind', 'See detail', ['Unable to sign', 'None']], 'status': 'Failure', 'transaction_id': 'abcd'}]

        And Key too soon and Key expired
        >>> m.completedTransactions = []
        >>> m.getTime = lambda: tests.mint_key1.not_before - 1
        >>> m.submit('abcd', [invalid])
        1199145599
        >>> realPerformMinting()
        >>> tests.printdictlist(m.completedTransactions)
        [{'added': 1199145599, 'completed': 1199145599, 'response': ['Blind', 'See detail', ['Key too soon']], 'status': 'Failure', 'transaction_id': 'abcd'}]

        >>> m.completedTransactions = []
        >>> m.getTime = lambda: tests.mint_key1.key_not_after + 1
        >>> m.submit('abcd', [invalid])
        1201824001
        >>> realPerformMinting()
        >>> tests.printdictlist(m.completedTransactions)
        [{'added': 1201824001, 'completed': 1201824001, 'response': ['Blind', 'See detail', ['Key expired']], 'status': 'Failure', 'transaction_id': 'abcd'}]

        """
        import base64
        try:
            transaction = self.waitingTransactions.pop(0) # FIFO
        except IndexError:
            return

        while transaction:
            keys_and_blinds = transaction['kandb']
            minted = []
            for key, blinds in keys_and_blinds:
                this_set = ['Success']
                for blind in blinds:
                    try:
                        signature = self.signNow(key.key_identifier, blind)
                    except MintError, reason:
                        this_set = ['Failure']
                        if reason.args[0].startswith('CryptoError'):
                            this_set.append('Unable to sign')
                        elif reason.args[0].startswith('KeyError'):
                            this_set.append('Invalid key_identifier')
                        elif reason.args[0] == 'MintKey not valid for minting':
                            if key.not_before > self.getTime():
                                this_set.append('Key too soon')
                            elif key.key_not_after < self.getTime():
                                this_set.append('Key expired')
                            else:
                                raise
                                # FIXME: This is where revoked key checks would go
                        else:
                            raise
                        break # Stop this key

                    this_set.append(base64.b64encode(signature))

                minted.append(this_set)

            if 'Failure' not in [k[0] for k in minted]:
                signed = []
                for k in minted:
                    signed.extend(k[1:])
                transaction['status'] = 'Minted'
                transaction['signed_blinds'] = signed
                transaction['completed'] = self.getTime()
                del transaction['kandb']
            else:
                details = []
                for m in minted:
                    if m[0] == 'Success':
                        details.append('None')
                    else:
                        details.append(m[1])
                transaction['status'] = 'Failure'
                transaction['response'] = ['Blind', 'See detail', details]
                transaction['completed'] = self.getTime()
                del transaction['kandb']

            self.completedTransactions.append(transaction)

            try:
                transaction = self.waitingTransactions.pop(0) # FIFO
            except IndexError:
                return
        

class MintError(Exception):
    pass


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
