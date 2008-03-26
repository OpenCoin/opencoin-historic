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
                                   # FIXME: What is the format? key is transaction_id, probably..
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

    def setDefaultCDD(self, CDD):
        """setDefaultCDD sets the default CDD for a currency to CDD. It adds if necessary."""
        version = dict(CDD.options)['version']
        if version not in self.cdds.setdefault(CDD.currency_identifier, {}):
            self.addCDD(CDD)
        self.cdds[CDD.currency_identifier][None] = version

    def fetchMintKey(self, transport, denominations=None, keyids=None, time=None):
        protocol = protocols.fetchMintKeyProtocol(denominations=denominations, keyids=keyids, time=time)
        transport.setProtocol(protocol)
        transport.start()
        protocol.newMessage(Message(None))

        # Get the keys direct from the protcool.
        retreivedKeys = protocol.keycerts

        for key in retreivedKeys:
            try:
                cdd_curr = self.cdds[key.currency_identifier]
                cdd = cdd_curr[cdd_curr[None]]
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
            

        #FIXME: If we go to string/fraction amount, the sort will have to be changed
        mysort = lambda x, y: int(x).__cmp__(int(y))
        denomination_list.sort(mysort, reverse=True) # sort from high to low

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

        int_denomination_list = [int(d) for d in denomination_list]

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
            cdd_currs = self.cdds[blanks[0].currency_identifier] # all blanks are the same currency
            cdd = cdd_currs[cdd_currs[None]]

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
        FIXME: It doesn't see to know if the transfer works?
        """
        # Q: What is reason for reason?
        # A: reason is describing what the tokens are going to be for, e.g 'a book'

        cdd_curr = self.cdds[coins[0].currency_identifier]
        cdd = cdd_curr[cdd_curr[None]] # The default CDD for the currency

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
            raise Exception #FIXME: Better error should go here, probably

        # strip off opencoin://
        fullstring = location[len('opencoin://'):]

        try:
            address, port = fullstring.split(':')
        except ValueError:
            raise Exception #FIXME: Better error should go here, probably

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
        from containers import BlankError

        #FIXME: What do we do if a coin is bad?
        coins = []
        blanks = self.waitingTransfers[transaction_id]

        # We have no way of being sure we have the same amount of blanks and blinds afaict.
        # We'll try to make as many coins as we can, then error
        shortest = min(len(blanks), len(blinds))

        cdd = self.cdds[blanks[0].currency_identifier] # all blanks have the same CDD in a transaction

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

class Issuer(Entity):
    """An isser

    >>> i = Issuer()
    >>> i.createMasterKey(keylength=256)
    >>> #i.keys.public()
    >>> #i.keys
    >>> #str(i.keys)
    >>> #i.keys.stringPrivate()
    """
    def __init__(self):
        self.dsdb = DSDB()
        self.mint = Mint()
        self.masterKey = None
        self.cdd  = None
        self.getTime = getTime

        #Signed minting keys
        self.signedKeys = {} # dict(denomination=[key,key,...])
        self.keyids = {}     #


    def getKeyByDenomination(self,denomination,time):
        #FIXME: the time argument is supposed to get all the keys at a certain time
        try:
            return self.signedKeys.get(denomination,[])[-1]
        except (KeyError, IndexError):            
            raise 'KeyFetchError'
    
    
    def getKeyById(self,keyid):
        try:
            return self.keyids[keyid]
        except KeyError:            
            raise 'KeyFetchError'

    
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
     
        self.cdd = cdd

    def createSignedMintKey(self, denomination, not_before, key_not_after, token_not_after, size=1024):
        """Have the Mint create a new key and sign the public key."""

        if denomination not in self.cdd.denominations:
            raise Exception('Trying to create a bad denomination')
       
        signing_key = self.masterKey

        hash_alg = self.cdd.issuer_cipher_suite.hashing
        sign_alg = self.cdd.issuer_cipher_suite.signing
        key_alg = self.key_alg

        public = self.mint.createNewKey(hash_alg, key_alg, size)

        keyid = public.key_id(hash_alg)
        
        import containers
        mintKey = containers.MintKey(key_identifier=keyid,
                                     currency_identifier=self.cdd.currency_identifier,
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
        
        
        self.signedKeys.setdefault(denomination, []).append(mintKey)
        self.keyids[keyid] = mintKey

        return mintKey

    def giveMintKey(self,transport):
        protocol = protocols.giveMintKeyProtocol(self)
        transport.setProtocol(protocol)
        transport.start()

    def listen(self,transport):
        """
        >>> import transports, tests,base64
        >>> tid = base64.b64encode('foobar')
        >>> i = tests.makeIssuer()
        >>> stt = transports.SimpleTestTransport()
        >>> i.listen(stt)
        >>> stt.send('HANDSHAKE',[['protocol', 'opencoin 1.0']])
        <Message('HANDSHAKE_ACCEPT',[['protocol', 'opencoin 1.0'], ['cdd_version', '0']])>
        >>> stt.send('TRANSFER_TOKEN_REQUEST',[tid, 'my account', [], [tests.coinA.toPython()], [['type', 'redeem']]])
        <Message('TRANSFER_TOKEN_ACCEPT',['Zm9vYmFy', []])>

        >>> stt.send('MINT_KEY_FETCH_DENOMINATION',[['1'], '0'])
        <Message('MINT_KEY_PASS',[...])>
        
        >>> stt.send('GOODBYE')
        <Message('GOODBYE',None)>
        >>> stt.send('foobar')
        """
        if hasattr(transport, 'protocol') and transport.protocol:
            transport.setProtocol(self.protocol)

        else:
            protocol = protocols.answerHandshakeProtocol(handshake_options=[['cdd_version','0']], #FIXME: use real cdd version
                                                         arguments=self,
                                                         TRANSFER_TOKEN_REQUEST=protocols.TransferTokenRecipient,
                                                         MINT_KEY_FETCH_DENOMINATION=protocols.giveMintKeyProtocol,
                                                         MINT_KEY_FETCH_KEYID=protocols.giveMintKeyProtocol)
            self.protocol = protocol
            transport.autoreset = self.listen
            transport.setProtocol(protocol)
            transport.start()


    def transferToTarget(self,target,coins):
        return True

    def debitTarget(self,target,blinds):
        return True
        
    def redeemTokens(self, transaction_id, tokens, options):
        """verifies the tokens and locks them.
        
        Returns a tuple of (locked, failures).
        Locked is a boolean specifying if the tokens are locked or not
        Failures is a tuple of (type, reason, reason_detail) to return in case of a reject.
        
        failures may be None if there were no failures
        """
        
        # FIXME: This will fail if we try to lock with an already-known request_id. Maybe a different error?
        
        failures = []

        if not tokens:
            return ('TRANSFER_TOKEN_REJECT', ('Token', 'Rejected', []))

        #check if coins are valid
        for token in tokens:
            mintKey = self.keyids.get(token.key_identifier, None)
            if not mintKey or not token.validate_with_CDD_and_MintKey(self.cdd, mintKey):
                failures.append(token)
        
        if failures: # We don't know exactly how, so give coin by coin information
            details = []
            for token in tokens:
                if token not in failures:
                    details.append('None')
                else:
                    details.append('Rejected')
            return (False, ('Token', 'See detail', details))

        #and not double spent
        try:
            #XXX have adjustable time for lock - not really needed. We unlock anyways, or spend
            self.dsdb.lock(transaction_id, tokens, 86400)
        except LockingError, e:
            # FIXME: Add per-token errors depending on values
            return (False, ('Token', 'Invalid token', []))
            
        return (True, None)

    def verifyMintableBlinds(self, blindslist, options):
        """returns a tuple of (success, failures) if the blinds in blindslist are mintable.
        
        success is a boolean set to true if they are mintable, otherwise false
        failures is a tuple of (type, reason, reason-detail) to return in case of a reject
        
        blindslist is a list of [ [MintKey, [blind1, blind2...]], [MintKey....]]
        """
        
        #check the MintKeys for validity
        timeNow = self.getTime()
        failures = []
        for mintKey, blindlist in blindslist:
            can_mint, can_redeem = mintKey.verify_time(timeNow)
            if not can_mint:
                # TODO: We need more logic here. can_mint only specifies if we are
                # between not_before and key_not_after. We may also need to do the
                # checking of the period of time the mint can mint but the IS cannot
                # send the key to the mint.
                failures.append(mintKey.encodeField('key_identifier'))

        if failures:
            return (False, ('Blind', 'Invalid key_identifier', []))

        else:
            return (True, None)
            
    def submitMintableBlinds(self, transaction_id, blindslist, options):
        """returns a tuple of (success, time, failures) after submitting blinds to the mint.
        
        success is a boolean set to true if we successfully submitted. False otherwise.
                Note: it can be false if we have JITM and it has already failed.
        time is an int of time in seconds to pass with a 'DELAY'
        failures is a tuple of (type, reason, reason_detail) to be passed if a 'REJECT'.
        """
        #FIXME: we only do JITM minting right now

        import base64
        
        #mint them immediately (the only thing we can do right now with the mint)
        minted = []
        for key, blindlist in blindslist:
            this_set = []
            for blind in blindlist:
                signature = self.mint.signNow(key.key_identifier, blind)
                this_set.append(base64.b64encode(signature))

            minted.extend(this_set)
            
        # FIXME: HACK! Submitting blinds instead of time.
        return (True, minted, None)
        
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
    
    FIXME: It does not currently use any real times
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
        self.locks = locks or {}       # a dictionary by id of tuple of (time_expire, tuple(tokens))
        self.getTime = getTime

    def lock(self, id, tokens, lock_duration):
        """Lock the tokens.
        Tokens are taken as a group. It tries to lock each token one at a time. If it fails,
        it unwinds the locked tokens are reports a failure. If it succeeds, it adds the lock
        to the locks.
        Note: This function performs no checks on the validity of the coins, just blindly allows
        them to be locked
        """
        
        lock_time = lock_duration + self.getTime()

        my_locks = (lock_time, [])
        locks = self.locks.setdefault(id, my_locks)

        if my_locks is not locks:
            raise LockingError('id already locked')
        
        tokens = list(tokens[:])

        reason = None
        
        while tokens:
            token = tokens.pop()
            key_dict = self.database.setdefault(token.key_identifier, {})
            if token.serial in key_dict:
                lock = key_dict[token.serial]
                if lock[0] == 'Spent':
                    tokens = []
                    reason = 'Token already spent'
                    break
                elif lock[0] == 'Locked':
                    # XXX: This implements lazy unlocking. Possible DoS attack vector
                    # Active unlocking would remove the if statement
                    if lock[1] > self.getTime(): # If the lock hasn't expired 
                        tokens = []
                        reason = 'Token locked'
                        break
                    else:
                        self.unlock(lock[2])
                else:
                    raise NotImplementedError('Impossible string')

            my_lock = ('Locked', lock_time, id)
            lock = key_dict.setdefault(token.serial, my_lock)
            if lock is not my_lock:
                raise LockingError('Possible race condition detected.')

            self.locks[id][1].append(token)

        if reason:
            self.unlock(id)

            raise LockingError(reason)

        return

    def unlock(self, id):
        """Unlocks an id from the dsdb.
        This only unlocks if a transaction is locked. If the transaction is
        completed and the token is spent, it cannot unlock.
        """
        
        if id not in self.locks:
            raise LockingError('Unknown transaction_id')

        lock = self.locks[id]

        lazy_unlocked = False
        if lock[0] < self.getTime(): # unlock and then error
            lazy_unlocked = True

        for token in lock[1]:
            del self.database[token.key_identifier][token.serial]
            if len(self.database[token.key_identifier]) == 0:
                # FIXME: Possible race condition here. We delete the dict of
                # by key_identifier if it is empty, but another thread can
                # be writing to it between the if and the del.
                pass
                # del self.database[token.key_identifier]

        del self.locks[id]

        if lazy_unlocked:
            raise LockingError('Unknown transaction_id')

        return

    def spend(self, id, tokens, automatic_lock=True):
        """Spend verifies the tokens are locked (or locks them) and marks the tokens as spent.
        FIXME: Small tidbit of code in place for lazy unlocking.
        FIXME: automatic_lock doesn't automatically unlock if it locked and the spending fails (how can it though?)
        """
        if id not in self.locks:
            if automatic_lock:
                # we can spend without locking, so lock now.
                self.lock(id, tokens, 86400)
            else:
                raise LockingError('Unknown transaction_id')

        if self.locks[id][0] < self.getTime():
            self.unlock(id)
            raise LockingError('Unknown transaction_id')
        
        # check to ensure locked tokens are the same as current tokens.
        if len(set(tokens)) != len(self.locks[id][1]): # self.locks[id] is guarenteed to have unique values by lock
            raise LockingError('Unknown token')

        for token in self.locks[id][1]:
            if token not in tokens:
                raise LockingError('Unknown token')

        # we know all the tokens are valid. Change them to locked
        for token in self.locks[id][1]:
            self.database[token.key_identifier][token.serial] = ('Spent',)

        del self.locks[id]

        return

class Mint:
    """A Mint is the minting agent for a currency. It has the 
    >>> m = Mint()
    >>> import calendar
    >>> m.getTime = lambda: calendar.timegm((2008,01,31,0,0,0))

    >>> import tests, crypto, base64
    >>> mintKey = tests.mintKeys[0]
    
    This bit is a touch of a hack. Never run like this normally
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


    def getKey(self,denomination,notbefore,notafter):
        pass

    def createNewKey(self, hash_alg, key_generator, size=1024):
        private, public = key_generator(size)
        self.privatekeys[private.key_id(hash_alg)] = private
        return public

    def addMintKey(self, mintKey, sign_alg):
        self.keyids[mintKey.key_identifier] = mintKey
        self.sign_algs[mintKey.key_identifier] = sign_alg
        
    def signNow(self, key_identifier, blind):
        from crypto import CryptoError
        try:
            sign_alg = self.sign_algs[key_identifier]
            signing_key = self.privatekeys[key_identifier]
            mintKey = self.keyids[key_identifier]
            
            signer = sign_alg(self.privatekeys[key_identifier])
        except KeyError, reason:
            raise MintError("KeyError: %s" % reason)
        
        if mintKey.verify_time(self.getTime())[0]: # if can_sign
            try:
                signature = signer.sign(blind)
            except CryptoError, reason:
                raise MintError("CryptoError: %s" % reason)
            return signature
        else:
            raise MintError("MintKey not valid for minting")

class MintError(Exception):
    pass

if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
