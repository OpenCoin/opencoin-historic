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

#################### Wallet ###############################

class Wallet(Entity):
    "Just a testwallet. Does nothing, really"

    def __init__(self):
        self.coins = []


    def fetchMintingKey(self,transport,denomination):
        protocol = protocols.fetchMintingKeyProtocol(denomination)
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

    def sendCoins(self,transport,amount,target,coins=None):
        #FIXME: Doing a broken thing and using something from tests!
        if not coins:
            from tests import coins as testcoins
            coin1 = testcoins[0][0] # denomination of 1
            coin2 = testcoins[1][0] # denomination of 2
            coins = [coin1,coin2]
        protocol = protocols.CoinSpendSender(coins,target)
        transport.setProtocol(protocol)
        transport.start()
        protocol.newMessage(Message(None))

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


    def handleIncomingCoins(self,coins,action,reason):
        transport = self.getIssuerTransport()
        if 1: #redeem
            if transport:
                self.transferTokens(transport,'my account',[],coins,'redeem')
        return 1

    def getIssuerTransport(self):
        return getattr(self,'issuer_transport',0)

#################### Issuer ###############################

class Issuer(Entity):
    """An isser

    >>> i = Issuer()
    >>> i.createKeys(256)
    >>> #i.keys.public()
    >>> #i.keys
    >>> #str(i.keys)
    >>> #i.keys.stringPrivate()
    """
    def __init__(self):
        self.dsdb = DSDB()
        self.mint = Mint()
        self.keys = None
        self.cdd  = None

        #Signed minting keys
        self.signedKeys = {} # dict(denomination=[key,key,...])
        self.keyids = {}     #


    def getKeyByDenomination(self,denomination):
        try:
            return self.signedKeys.get(denomination,[])[-1]
        except (KeyError, IndexError):            
            raise 'KeyFetchError'
    
    def getKeyById(self,keyid):
        try:
            return self.keyids[keyid]
        except KeyError:            
            raise 'KeyFetchError'

    def createKeys(self,keylength=1024):
        import crypto
        keys = crypto.createRSAKeyPair(keylength, public=False)
        self.keys = keys

        
     
    def createSignedMintKey(self,denomination, not_before, key_not_after, coin_not_after, signing_key=None, size=1024):
        """Have the Mint create a new key and sign the public key."""

        #Note: I'm assuming RSA/SHA256. It should really use the CDD defined ones
        #      hmm. And it needs the CDD for the currency_identifier
        
       
        if not signing_key:
            signing_key = self.keys

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

    def lock(self, id, tokens, lock_time):
        """Lock the tokens.
        Tokens are taken as a group. It tries to lock each token one at a time. If it fails,
        it unwinds the locked tokens are reports a failure. If it succeeds, it adds the lock
        to the locks.
        Note: This function performs no checks on the validity of the coins, just blindly allows
        them to be locked
        """
        
        if self.locks.has_key(id):
            raise LockingError('id already locked')

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
                    # FIXME: This implements lazy unlocking. Possible DoS attack vector
                    # Active unlocking would remove the if statement
                    import time
                    if lock[1] >= 0: # FIXME: Use actual time
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
        """Unlocks an id from the dsdb."""
        
        if not self.locks.has_key(id):
            raise LockingError('Unknown transaction_id')

        for token in self.locks[id][1]:
            del self.database[token.key_identifier][token.serial]
            if len(self.database[token.key_identifier]) == 0:
                del self.database[token.key_identifier]

        del self.locks[id]

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
                #if ret != (True,):
                #    return (False, ret[1]) 
            else:
                raise LockingError('Unknown transaction_id')

        if self.locks[id][0] < 0: #FIXME: use real time
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
    """A Mint is the minting agent for a a currency. It has the 
    >>> m = Mint()

    >>> import tests, crypto, base64
    >>> mintKey = tests.mintKeys[0]
    
    This bit is a touch of a hack. Never run like this normally
    >>> m.privatekeys[mintKey.key_identifier] = tests.keys512[0]

    >>> m.addMintKey(mintKey, crypto.RSASigningAlgorithm)

    >>> base64.b64encode(m.signNow(mintKey.key_identifier, 'abcdefghijklmnop'))
    'Mq4dqFpKZEvbl+4HeXh0rGrqBk6Fm2bnUjNiVgirDvOuQf4Ty6ZkvpqB95jMyiwNlhx8A1qZmQv5biLM40emUg=='
    
    >>> m.signNow('abcd', 'efg')
    False

    """
    def __init__(self):
        self.keyids = {}
        self.privatekeys = {}
        self.sign_algs = {}


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
        except KeyError:
            return False
        
        if mintKey.verify_time(mintKey.key_not_after)[0]: # FIXME: Actually check time
            signature = signer.sign(blind)
            return signature
        else:
            return False

if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
