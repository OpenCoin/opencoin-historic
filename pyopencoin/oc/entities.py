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

##################### time ################################
def getTime():
    import time
    return time.time()

#################### Wallet ###############################

class Wallet(Entity):
    "A Wallet"

    def __init__(self):
        self.coins = []
        self.waitingTransfers = {}
        self.otherCoins = [] # Coins we received from another wallet, waiting to Redeem
        self.getTime = getTime


    def fetchMintingKey(self,transport,denominations):
        protocol = protocols.fetchMintingKeyProtocol(denominations)
        transport.setProtocol(protocol)
        transport.start()
        protocol.newMessage(Message(None))

    def sendMoney(self,transport):
        "Sends some money to the given transport."

        protocol = protocols.WalletSenderProtocol(self)
        transport.setProtocol(protocol)
        transport.start()
        #Trigger execution of the protocol
        protocol.newMessage(Message(None))

    def receiveMoney(self,transport):
        protocol = protocols.WalletRecipientProtocol(self)
        transport.setProtocol(protocol)
        transport.start()

    def sendCoins(self,transport,target,amount=None,coins=None):
        """sendCoins sends coins over a transport to a target of a certain amount or using given coins."""
        # The coins argument for sendCoins is being phased out. Need to make the amount part work first though. 
        if coins: #FIXME: phase this out
            touse = coins
            amount = sum(coins)
        elif amount:
            #FIXME: get coins
            touse = None
        else:
            raise Exception()

        protocol = protocols.CoinSpendSender(touse,target)
        transport.setProtocol(protocol)
        transport.start()
        protocol.newMessage(Message(None))

        if protocol.state == protocol.finish:
            # FIXME: remove coins
            if not protocol.coins:
                raise Exception()
            pass

    def listen(self,transport):
        """
        >>> import transports
        >>> w = Wallet()
        >>> stt = transports.SimpleTestTransport()
        >>> w.listen(stt)
        >>> stt.send('HANDSHAKE',{'protocol': 'opencoin 1.0'})
        <Message('HANDSHAKE_ACCEPT',None)>
        >>> stt.send('sendMoney',[1,2])
        <Message('Receipt',None)>
        """
        protocol = protocols.answerHandshakeProtocol(sendMoney=protocols.WalletRecipientProtocol(self),
                                                     SUM_ANNOUNCE=protocols.CoinSpendRecipient(self))
        transport.setProtocol(protocol)
        transport.start()


    def confirmReceiveCoins(self,walletid,sum,target):
        return 'trust'


    def transferTokens(self,transport,target,blanks,coins,type):
        protocol = protocols.TransferTokenSender(target,blanks,coins,type=type)
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
        transport = self.getIssuerTransport()
        if 1: #redeem
            self.otherCoins.extend(coins) # Deposit them
            if transport:
                self.transferTokens(transport,'my account',[],coins,'redeem')
        return 1

    def getIssuerTransport(self):
        return getattr(self,'issuer_transport',0)

    def removeCoins(self, coins):
        for c in coins:
            try:
                self.coins.remove(c)
            except ValueError:
                self.otherCoins.remove(c)

    def addTransferBlanks(self, transaction_id, blanks):
        self.waitingTransfers[transaction_id] = blanks

    def finishTransfer(self, transaction_id, blinds):
        """Finishes a transfer where we minted. Takes blinds and makes coins."""
        #FIXME: What do we do if a coin is bad?
        coins = []
        blanks = self.waitingTransfers[transaction_id]

        #FIXME: We need to make sure we atleast have the same number of blanks and blinds at the protocol level!
        for i in range(len(blanks)):
            blank = blanks[i]
            blind = blinds[i]
            try:
                signature = blank.unblindSignature(blind)
                coins.append(blank.newCoin(signature)) # FIXME: No error checking here
            except NotImplementedError: #What errors can we get here. CryptoError of some sort...
                pass
                # Don't stop. We need to make as many valid coins as possible

        for coin in coins:
            if coin not in self.coins:
                self.coins.append(coin)

        del self.waitingTransfers[transaction_id]

#################### Issuer ###############################

class Issuer(Entity):
    """An isser

    >>> i = Issuer()
    >>> i.createKey(keylength=256)
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

    def createKey(self,keylength=1024):
        import crypto
        masterKey = crypto.createRSAKeyPair(keylength, public=False)
        self.masterKey = masterKey

        
     
    def createSignedMintKey(self,denomination, not_before, key_not_after, coin_not_after, signing_key=None, size=1024):
        """Have the Mint create a new key and sign the public key."""

        #Note: I'm assuming RSA/SHA256. It should really use the CDD defined ones
        #      hmm. And it needs the CDD for the currency_identifier
        
       
        if not signing_key:
            signing_key = self.masterKey

        import crypto
        hash_alg = crypto.SHA256HashingAlgorithm
        key_alg = crypto.createRSAKeyPair

        public = self.mint.createNewKey(hash_alg, key_alg, size)

        keyid = public.key_id(hash_alg)
        
        import containers
        mintKey = containers.MintKey(key_identifier=keyid,
                                     currency_identifier='http://...Cent/',
                                     denomination=denomination,
                                     not_before=not_before,
                                     key_not_after=key_not_after,
                                     coin_not_after=coin_not_after,
                                     public_key=public)

        sign_alg = crypto.RSASigningAlgorithm
        signer = sign_alg(signing_key)
        hashed_content = hash_alg(mintKey.content_part()).digest()
        sig = containers.Signature(keyprint = signing_key.key_id(hash_alg),
                                   signature = signer.sign(hashed_content))

        mintKey.signature = sig
        
        
        self.signedKeys.setdefault(denomination, []).append(mintKey)
        #self.signedKeys[mintKey.denomination].append(mintKey)
        self.keyids[keyid] = mintKey
        return mintKey

    def giveMintingKey(self,transport):
        protocol = protocols.giveMintingKeyProtocol(self)
        transport.setProtocol(protocol)
        transport.start()

    def listen(self,transport):
        """
        >>> import transports
        >>> w = Wallet()
        >>> stt = transports.SimpleTestTransport()
        >>> w.listen(stt)
        >>> stt.send('HANDSHAKE',{'protocol': 'opencoin 1.0'})
        <Message('HANDSHAKE_ACCEPT',None)>
        >>> stt.send('sendMoney',[1,2])
        <Message('Receipt',None)>
        """
        protocol = protocols.answerHandshakeProtocol(TRANSFER_TOKEN_REQUEST=protocols.TransferTokenRecipient(self),)
        transport.setProtocol(protocol)
        transport.start()


    def transferToTarget(self,target,coins):
        return True

    def debitTarget(self,target,blinds):
        return True

    def getNow(self):
        import time
        return time.time()

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
        
        if self.locks.has_key(id):
            raise LockingError('id already locked')

        lock_time = lock_duration + self.getTime()

        self.locks[id] = (lock_time, [])
        
        tokens = list(tokens[:])

        reason = None
        
        while tokens:
            token = tokens.pop()
            self.database.setdefault(token.key_identifier, {})
            if self.database[token.key_identifier].has_key(token.serial):
                lock = self.database[token.key_identifier][token.serial]
                if lock[0] == 'Spent':
                    tokens = []
                    reason = 'Token already spent'
                    break
                elif lock[0] == 'Locked':
                    # XXX: This implements lazy unlocking. Possible DoS attack vector
                    # Active unlocking would remove the if statement
                    if lock[1] >= self.getTime(): # FIXME: This statement passes tests but is wrong. 
                        tokens = []
                        reason = 'Token locked'
                        break
                    else:
                        self.unlock(lock[2])
                else:
                    raise NotImplementedError('Impossible string')

            lock = self.database[token.key_identifier].setdefault(
                                        token.serial, ('Locked', lock_time, id))
            if lock != ('Locked', lock_time, id):
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
        
        if not self.locks.has_key(id):
            raise LockingError('Unknown transaction_id')

        lazy_unlocked = False
        if self.locks[id][0] < self.getTime(): # unlock and then error
            lazy_unlocked = True

        for token in self.locks[id][1]:
            del self.database[token.key_identifier][token.serial]
            if len(self.database[token.key_identifier]) == 0:
                del self.database[token.key_identifier]

        del self.locks[id]

        if lazy_unlocked:
            raise LockingError('Unknown transaction_id')

        return

    def spend(self, id, tokens, automatic_lock=True):
        """Spend verifies the tokens are locked (or locks them) and marks the tokens as spent.
        FIXME: Small tidbit of code in place for lazy unlocking.
        FIXME: automatic_lock doesn't automatically unlock if it locked and the spending fails (how can it though?)
        """
        if not self.locks.has_key(id):
            if automatic_lock:
                # we can spend without locking, so lock now.
                self.lock(id, tokens, 1)
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
        try:
            sign_alg = self.sign_algs[key_identifier]
            signing_key = self.privatekeys[key_identifier]
            mintKey = self.keyids[key_identifier]
            
            signer = sign_alg(self.privatekeys[key_identifier])
        except KeyError, reason:
            raise MintError("KeyError: %s" % reason)
        
        if mintKey.verify_time(self.getTime())[0]:
            signature = signer.sign(blind)
            return signature
        else:
            raise MintError("MintKey not valid for minting")

class MintError(Exception):
    pass

if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
