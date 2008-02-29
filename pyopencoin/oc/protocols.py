"""
Protocol have states, which are basically methods that consume messages, do
something and return messages. The states are just methods, and one state
might change the state of its protocol to another state. 

A protocol writes to a transport, using Transport.write. It receives messages
from the transport with Protocol.newMessage.

A state (a protocol method) returns messages, it does not write directly back
to a transport (XXX not sure about this, what if a state needs to communicate
with another enity). Instead newMessage by default writes back to the transport.
(XXX maybe the transport could take the returned message, and write it up its own,
ah write method?)

Before returning the message, the state should set the protocols state to the next
state (sounds a bit ackward, its easy, check the states code)
"""

from messages import Message
import containers    
import types

class Protocol:
    """A protocol ties messages and actions togehter, it is basically one side
       of an interaction. E.g. when A exchanges a coin with B, A would use the
       walletSenderProtocol, and B the walletRecipientProtocol."""

    def __init__(self):
        'Set the initial state'
        
        self.state = self.start
        self.result = None

    def setTransport(self,transport):
        'get the transport we are working with'
        
        self.transport = transport
        
    def start(self,message):
        'this should be the initial state of the protocol'
       
        pass

    def goodbye(self,message):
        self.state = self.finish
        return Message('GOODBYE')

    def finish(self,message):
        'always the last state. There can be other final states'        
        return Message('finished')
                    
    def newMessage(self,message):
        'this is used by a transport to pass on new messages to the protocol'

        out = self.state(message)
        self.transport.write(out)
        return out

    def newState(self,method):
        self.state = method

    def initiateHandshake(self,message):    
        self.newState(self.firstStep)
        return Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})


class answerHandshakeProtocol(Protocol):


    def __init__(self,**mapping):
        Protocol.__init__(self)
        self.mapping = mapping

    def start(self,message):

        if message.type == 'HANDSHAKE':
            if message.data['protocol'] == 'opencoin 1.0':
                self.newState(self.dispatch)
                return Message('HANDSHAKE_ACCEPT')
            else:
                self.newState(self.goodbye)
                return Message('HANDSHAKE_REJECT','did not like the protocol version')
        else:
            return Message('PROTOCOL_ERROR','please do a handshake')


    def dispatch(self,message):        
        self.result = message
        nextprotocol = self.mapping[message.type]
        self.transport.setProtocol(nextprotocol)
        m = nextprotocol.newMessage(message)
        #print 'here ', m
        #return m




############################### Spending coins (w2w) ##########################
# Spoken bewteen two wallets to transfer coins / tokens                       #
###############################################################################

class CoinSpendSender(Protocol):
    """
    >>> from tests import coins
    >>> coin1 = coins[0][0]
    >>> coin2 = coins[1][0]
    >>> css = CoinSpendSender([coin1,coin2],'foobar')
    >>> css.state(Message(None))
    <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
    >>> css.state(Message('HANDSHAKE_ACCEPT'))
    <Message('SUM_ANNOUNCE',['...', 3, 'foobar'])>
    >>> css.state(Message('SUM_ACCEPT'))
    <Message('COIN_SPEND',['...', [[(...)], [(...)]], 'foobar'])>
    >>> css.state(Message('COIN_ACCEPT'))
    <Message('GOODBYE',None)>
    >>> css.state(Message('Really?'))
    <Message('finished',None)>
    """
    def __init__(self,coins,target):

        self.coins = coins
        self.amount = sum(coins)
        self.target = target
        
        import crypto,base64
        id = crypto._r.getRandomString(128) #_r is an instance of Random() (FIXME: should it be namd something else?)
        self.transaction_id = base64.b64encode(id)

        Protocol.__init__(self)
        self.state = self.initiateHandshake

    def firstStep(self,message):       
        self.state = self.spendCoin
        return Message('SUM_ANNOUNCE',[self.transaction_id,
                                       self.amount,
                                       self.target])


    def spendCoin(self,message):
        if message.type == 'SUM_ACCEPT':
            self.state = self.goodbye            
            jsonCoins = [c.toPython() for c in self.coins]
            return Message('COIN_SPEND',[self.transaction_id,
                                         jsonCoins,
                                         self.target])

    def goodbye(self,message):
        if message.type == 'COIN_ACCEPT':
            self.state = self.finish
            return Message('GOODBYE')


class CoinSpendRecipient(Protocol):
    """
    >>> import entities
    >>> from tests import coins
    >>> coin1 = coins[0][0].toPython() # Denomination of 1
    >>> coin2 = coins[1][0].toPython() # Denomination of 2
    >>> w = entities.Wallet()
    >>> csr = CoinSpendRecipient(w)
    >>> csr.state(Message('SUM_ANNOUNCE',['123',3,'a book']))
    <Message('SUM_ACCEPT',None)>
    >>> csr.state(Message('COIN_SPEND',['123', [coin1, coin2], 'a book']))
    <Message('COIN_ACCEPT',None)>
    >>> csr.state(Message('Goodbye',None))
    <Message('GOODBYE',None)>
    >>> csr.state(Message('foobar'))
    <Message('finished',None)>

    TODO: Add PROTOCOL_ERROR checking
    """
    
    def __init__(self,wallet,issuer_transport = None):
        self.wallet = wallet
        self.issuer_transport = issuer_transport
        Protocol.__init__(self)

    def start(self,message):
        if message.type == 'SUM_ANNOUNCE':
            self.transaction_id = message.data[0]
            self.sum = message.data[1]
            self.target = message.data[2]
            #get some feedback from interface somehow
            action = self.wallet.confirmReceiveCoins('the other wallet id',self.sum,self.target)
            if action == 'reject':
                self.state = self.goodby                
                return Message('SUM_REJECT')
            else:
                self.action = action
                self.state = self.handleCoins
                return Message('SUM_ACCEPT')
        else:
            self.state = self.goodbye
            return Message('Expected something else')

    def handleCoins(self,message):
        if message.type == 'COIN_SPEND':
            
            #be conservative
            result = Message('COIN_REJECT','default')
            
            transaction_id,coins,target  = message.data
            try:
                coins = [containers.CurrencyCoin().fromPython(c) for c in coins]
            except:
                return Message('PROTOCOL_ERROR', 'send again')
            
            if transaction_id != self.transaction_id:
                result = Message('COIN_REJECT','transaction_id')
            
            elif sum(coins) != self.sum:
                result = Message('COIN_REJECT','wrong sum')
            
            elif target != self.target:
                result = Message('COIN_REJECT','wrong target')
            
            elif self.action in ['redeem','exchange','trust']:
                out = self.wallet.handleIncomingCoins(coins,self.action,target)
                if out:
                    result = Message('COIN_ACCEPT')
        self.state = self.goodbye
        return result




############################### Transfer tokens  ##############################
# This is spoken between a wallet (sender) and the issuer, for minting,       #
# exchange and redemption                                                     #
###############################################################################

class TransferTokenSender(Protocol):
    """
    >>> from tests import coins
    >>> coin1 = coins[0][0] # denomination of 1
    >>> coin2 = coins[1][0] # denomination of 2

    >>> tts = TransferTokenSender('my account',[],[coin1, coin2],type='redeem')
    >>> tts.state(Message(None))
    <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>
    >>> tts.state(Message('HANDSHAKE_ACCEPT'))
    <Message('TRANSFER_TOKEN_REQUEST',['...', 'my account', [], [[(...)], [(...)]], [['type', 'redeem']]])>
    >>> tts.state(Message('TRANSFER_TOKEN_ACCEPT',3))
    <Message('GOODBYE',None)>

    """

    
    def __init__(self,target,blanks,coins,**kwargs):
        import base64
        from crypto import _r as Random
        id = Random.getRandomString(128) #XXX is that a good enough id?
        self.transaction_id = base64.b64encode(id)

        self.target = target
        self.blanks = blanks
        self.coins = [c.toPython() for c in coins]
        self.kwargs = kwargs

        Protocol.__init__(self)
        self.state = self.initiateHandshake
   
    def firstStep(self,message):
        data = [self.transaction_id,
                self.target,
                self.blanks,
                self.coins]
        if self.kwargs:
            data.append([list(i) for i in self.kwargs.items()])                
        self.state = self.goodbye
        return Message('TRANSFER_TOKEN_REQUEST',data)

    def goodbye(self,message):
        if message.type == 'TRANSFER_TOKEN_ACCEPT':
            self.result = 1
        else:
            self.result = 0
        self.state = self.finish
        return Message('GOODBYE')


class TransferTokenRecipient(Protocol):
    """
    >>> import entities, tests,containers, base64, copy
    >>> issuer = tests.makeIssuer()

    >>> ttr = TransferTokenRecipient(issuer)
    >>> coin1 = tests.coins[0][0].toPython() # denomination of 1
    >>> coin2 = tests.coins[1][0].toPython() # denomination of 2

    This should not be accepted
    >>> ttr.state(Message('TRANSFER_TOKEN_REQUEST',['123', 'my account', [], ['foobar'], [['type', 'redeem']]]))    
    <Message('PROTOCOL_ERROR','send again')>

    The malformed coin should be rejected
    >>> malformed = copy.deepcopy(tests.coins[0][0])
    >>> malformed.signature = 'Not a valid signature'
    >>> ttr.state(Message('TRANSFER_TOKEN_REQUEST',['123', 'my account', [], [malformed.toPython()], [['type', 'redeem']]]))
    <Message('TRANSFER_TOKEN_REJECT',['123', [], [['sj17RxE1hfO06+oTgBs9Z7xLut/3NN+nHJbXSJYTks0=', 'Error']]])>

    The unknown key_identifier should be rejected
    >>> malformed = copy.deepcopy(tests.coins[0][0])
    >>> malformed.key_identifier = 'Not a valid key identifier'
    >>> ttr.state(Message('TRANSFER_TOKEN_REQUEST',['123', 'my account', [], [malformed.toPython()], [['type', 'redeem']]]))
    <Message('TRANSFER_TOKEN_REJECT',['123', [], [['Tm90IGEgdmFsaWQga2V5IGlkZW50aWZpZXI=', 'Error']]])>

    >>> ttr.state(Message('TRANSFER_TOKEN_REQUEST',['123', 'my account', [], [coin1, coin2], [['type', 'redeem']]]))
    <Message('TRANSFER_TOKEN_ACCEPT',3)>

    Try to double spend. Should not work.
    >>> ttr.state = ttr.start 
    >>> ttr.state(Message('TRANSFER_TOKEN_REQUEST',['123', 'my account', [], [coin1, coin2], [['type', 'redeem']]]))
    <Message('TRANSFER_TOKEN_REJECT',['123', [], [['What do we put here?', 'Error']]])>

    >>> blank1 = containers.CurrencyBlank().fromPython(tests.coinA.toPython(nosig=1))
    >>> blank2 = containers.CurrencyBlank().fromPython(tests.coinB.toPython(nosig=1))
    >>> blind1 = blank1.blind_blank(tests.CDD,tests.mint_key1, blind_factor='a'*26)
    >>> blind2 = blank2.blind_blank(tests.CDD,tests.mint_key2, blind_factor='a'*26)
    >>> blindslist = [[tests.mint_key1.encodeField('key_identifier'),[blind1]],
    ...               [tests.mint_key2.encodeField('key_identifier'),[blind2]]]

    >>> import calendar
    >>> issuer.getTime = lambda: calendar.timegm((2008,01,31,0,0,0)) 
    >>> ttr.state = ttr.start
    >>> ttr.state(Message('TRANSFER_TOKEN_REQUEST',['123', 'my account', blindslist, [], [['type', 'mint']]]))
    <Message('TRANSFER_TOKEN_ACCEPT',['123', 'A message', [['sj17RxE1hfO06+oTgBs9Z7xLut/3NN+nHJbXSJYTks0=', ['jWUOkVfIulEvPjR4HfdxOtEF2vk3ss8vkKSL6aSd2w4Sj0vChSjtmiabkWdbxLTLth13dmigB0vBXDggjBzM7w==']], ['WbXTWO4M60oZ/LGY+sccKf5Oq6HxrjrY4qAxrBDXuek=', ['xBzoYV7W/2NuWdQQrwal7xFbky5D/m3D5Y9aTtuwZPirvK4gx7Po5+VrfGm04BuHo7kwnZ3ZGfUDIXIoILm2ng==']]]])>

    """

    def __init__(self,issuer):
        self.issuer = issuer
        Protocol.__init__(self)

    def start(self,message):
        from entities import LockingError
        #raise `message.data[:4]`
        
        options = {'type':'unknown'}
        if message.data:
            transaction_id,target,blindslist,coins = message.data[:4]
            options.update(len(message.data)==5 and message.data[4] or [])
        if options['type'] == 'redeem':

            failures = []

            #check if coins are 'well-formed'
            try:
                coins = [containers.CurrencyCoin().fromPython(c) for c in coins]
            except:
                return Message('PROTOCOL_ERROR', 'send again')

            #check if they are valid
            for coin in coins:
                mintKey = self.issuer.keyids.get(coin.key_identifier, None)
                if not mintKey or not coin.validate_with_CDD_and_MintKey(self.issuer.cdd, mintKey):
                    failures.append(coin)
            if failures:
                return Message('TRANSFER_TOKEN_REJECT', [transaction_id, [], 
                               [[coin.encodeField('key_identifier'), 'Error'] for coin in failures]])

            #and not double spent
            try:
                self.issuer.dsdb.lock(transaction_id,coins,10) #FIXME: questionable time
            except LockingError, e:
                return Message('TRANSFER_TOKEN_REJECT', [transaction_id, [], [['What do we put here?', 'Error']]])
            
            # XXX transmit funds
            
            if not self.issuer.transferToTarget(target,coins):
                return Message('PROTOCOL_ERROR', 'send again')

            #register them as spent
            try:
                self.issuer.dsdb.spend(transaction_id,coins,10) #FIXME: questionable time
            except:                
                #Note: if we fail here, that means we have large problems, since the coins are locked
                return Message('PROTOCOL_ERROR', 'send again')

            self.state = self.goodbye
            return Message('TRANSFER_TOKEN_ACCEPT',sum(coins))
        elif options['type'] == 'mint':

            #check that we have the keys
            import base64
            blinds = [[self.issuer.keyids[base64.b64decode(keyid)], blinds] for keyid, blinds in blindslist]

            #check target
            if not self.issuer.debitTarget(target,blindslist):
                return Message('PROTOCOL_ERROR', 'send again')

            #check the MintKeys for validity
            timeNow = self.issuer.getTime()
            failures = []
            for mintKey, blindlist in blinds:
                can_mint, can_redeem = mintKey.verify_time(timeNow)
                if not can_mint:
                    # TODO: We need more logic here. can_mint only specifies if we are
                    # between not_before and key_not_after. We may also need to do the
                    # checking of the period of time the mint can mint but the IS cannot
                    # send the key to the mint.
                    failures.append(mintKey.encodeField('key_identifier'))

            if failures:
                return Message('TRANSFER_TOKEN_REJECT', [transaction_id, 'Invalid key identifier', failures, []])

            #mint them immediately (the only thing we can do right now with the mint)
            minted = []
            for key, blindlist in blinds:
                this_set = []
                for blind in blindlist:
                    signature = self.issuer.mint.signNow(key.key_identifier, blind)
                    this_set.append(base64.b64encode(signature))

                minted.append([key.encodeField('key_identifier'), this_set])

            return Message('TRANSFER_TOKEN_ACCEPT', [transaction_id, 'A message', minted])
            
            #respond
            pass 
        else:
            return Message('NOT IMPLEMENTED YET')




############################### Mint key exchange #############################
#Between a wallet and the IS, to get the mint key                             #
###############################################################################

class fetchMintingKeyProtocol(Protocol):
    """
    Used by a wallet to fetch the mints keys, needed when 
    creating blanks
       
    Lets fetch by denomination

    >>> fmp = fetchMintingKeyProtocol(denominations=['1'])
    >>> fmp.state(Message(None))
    <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>

    >>> fmp.state(Message('HANDSHAKE_ACCEPT'))
    <Message('MINTING_KEY_FETCH_DENOMINATION',[['1'], '0'])>

    >>> from tests import mintKeys
    >>> mintKey = mintKeys[0]
    >>> fmp.state(Message('MINTING_KEY_PASS',[mintKey.toPython()]))
    <Message('GOODBYE',None)>


    And now by keyid

    >>> fmp = fetchMintingKeyProtocol(keyids=['sj17RxE1hfO06+oTgBs9Z7xLut/3NN+nHJbXSJYTks0='])
    >>> fmp.state(Message(None))
    <Message('HANDSHAKE',{'protocol': 'opencoin 1.0'})>

    >>> fmp.state(Message('HANDSHAKE_ACCEPT'))
    <Message('MINTING_KEY_FETCH_KEYID',['sj17RxE1hfO06+oTgBs9Z7xLut/3NN+nHJbXSJYTks0='])>

    >>> fmp.state(Message('MINTING_KEY_PASS',[mintKey.toPython()]))
    <Message('GOODBYE',None)>


    Lets have some problems a failures (we set the state
    to getKey to reuse the fmp object and save a couple
    of lines)

    >>> fmp.newState(fmp.getKey)
    >>> fmp.state(Message('MINTING_KEY_FAILURE',[['RxE1', 'Unknown key_identifier']]))
    <Message('GOODBYE',None)>
   
    Now lets break something
    
    >>> fmp.newState(fmp.getKey)
    >>> fmp.state(Message('FOOBAR'))
    <Message('PROTOCOL_ERROR','send again')>

    Okay. Now we'll test every possible MINTING_KEY_PASS.
    The correct argument is a list of coins. Try things to
    break it.
    
    >>> fmp.newState(fmp.getKey)
    >>> fmp.state(Message('MINTING_KEY_PASS', [['foo']]))
    <Message('PROTOCOL_ERROR','send again')>

    >>> fmp.newState(fmp.getKey)
    >>> fmp.state(Message('MINTING_KEY_PASS', ['foo']))
    <Message('PROTOCOL_ERROR','send again')>

    >>> fmp.newState(fmp.getKey)
    >>> fmp.state(Message('MINTING_KEY_PASS', 'foo'))
    <Message('PROTOCOL_ERROR','send again')>

    >>> fmp.newState(fmp.getKey)
    >>> fmp.state(Message('MINTING_KEY_PASS', []))
    <Message('PROTOCOL_ERROR','send again')>

    Now try every possible bad MINTING_KEY_FAILURE.
    Note: it may make sense to verify we have tood reasons
    as well.

    We need to make sure we are setup as handling keyids
    >>> fmp.keyids and not fmp.denominations
    True

    Check base64 decoding causes failure
    >>> fmp.newState(fmp.getKey)
    >>> fmp.state(Message('MINTING_KEY_FAILURE', [[1, '']]))
    <Message('PROTOCOL_ERROR','send again')>

    And the normal tests
    >>> fmp.newState(fmp.getKey)
    >>> fmp.state(Message('MINTING_KEY_FAILURE', [[]]))
    <Message('PROTOCOL_ERROR','send again')>
    
    Okay. Check the denomination branch now
    
    >>> fmp.denominations = ['1']
    >>> fmp.keyids = None

    Make sure we are in the denomination branch
    >>> fmp.newState(fmp.getKey)
    >>> fmp.state(Message('MINTING_KEY_FAILURE', [[1, '']]))
    <Message('GOODBYE',None)>
    
    Do a check

    >>> fmp.newState(fmp.getKey)
    >>> fmp.state(Message('MINTING_KEY_FAILURE', [[]]))
    <Message('PROTOCOL_ERROR','send again')>
    
    """

    def __init__(self,denominations=None,keyids=None,time=None):
        
        self.denominations = denominations
        self.keyids = keyids
        self.keycerts = []

        if not time: # The encoded value of time
            self.encoded_time = '0'
        else:
            self.encoded_time = containers.encodeTime(time)

        Protocol.__init__(self)

    def start(self,message):
        self.newState(self.requestKey)
        return Message('HANDSHAKE',{'protocol':'opencoin 1.0'})

    def requestKey(self,message):
        """Completes handshake, asks for the minting keys """

        if message.type == 'HANDSHAKE_ACCEPT':
            
            if self.denominations:
                self.newState(self.getKey)
                return Message('MINTING_KEY_FETCH_DENOMINATION',[self.denominations, self.encoded_time])
            elif self.keyids:
                self.newState(self.getKey)
                return Message('MINTING_KEY_FETCH_KEYID',self.keyids) 

        elif message.type == 'HANDSHAKE_REJECT':
            self.newState(self.finish)
            return Message('GOODBYE')

        else:
            return Message('PROTOCOL ERROR','send again')

    def getKey(self,message):
        """Gets the actual key"""

        if message.type == 'MINTING_KEY_PASS':
            if not isinstance(message.data, types.ListType):
                return Message('PROTOCOL_ERROR', 'send again')
            
            if len(message.data) == 0: # Nothing in the message
                return Message('PROTOCOL_ERROR','send again')

            for key in message.data:
                try:
                    keycert = containers.MintKey().fromPython(key)
                    self.keycerts.append(keycert)
                except Exception, reason:
                    return Message('PROTOCOL_ERROR','send again')
            
            self.newState(self.finish)
            return Message('GOODBYE')
                

        elif message.type == 'MINTING_KEY_FAILURE':
            try:
                self.reasons = []
                if self.denominations: # Was a denomination search
                    for reasonlist in message.data:
                        denomination, reason = reasonlist
                            
                        #FIXME: Should we make sure valid reason?
                        self.reasons.append((denomination, reason))

                else: # Was a key_identifier search
                    import base64
                    for reasonlist in message.data:
                        key, reason = reasonlist
                            
                        #FIXME: Should we make sure valid reason?
                        self.reasons.append((base64.b64decode(key), reason))
            except TypeError:
                return Message('PROTOCOL_ERROR', 'send again')
            except ValueError:
                return Message('PROTOCOL_ERROR', 'send again')

            self.newState(self.finish)
            return Message('GOODBYE')
        
        else:
            return Message('PROTOCOL_ERROR','send again')



class giveMintingKeyProtocol(Protocol):
    """An issuer hands out a key. The other side of fetchMintingKeyProtocol.
    >>> from entities import Issuer
    >>> issuer = Issuer()
    >>> issuer.createKey(keylength=512)
    >>> now = 0; later = 1; much_later = 2
    >>> pub1 = issuer.createSignedMintKey('1', now, later, much_later)
    >>> gmp = giveMintingKeyProtocol(issuer)
    
    >>> gmp.state(Message('HANDSHAKE',{'protocol': 'opencoin 1.0'}))
    <Message('HANDSHAKE_ACCEPT',None)>

    >>> m = gmp.state(Message('MINTING_KEY_FETCH_DENOMINATION',[['1'], '0']))
    >>> m == Message('MINTING_KEY_PASS',[pub1.toPython()])
    True

    >>> gmp.newState(gmp.giveKey)
    >>> m = gmp.state(Message('MINTING_KEY_FETCH_KEYID',[pub1.key_identifier]))
    >>> m == Message('MINTING_KEY_PASS',[pub1.toPython()])
    True

    >>> gmp.newState(gmp.giveKey)
    >>> gmp.state(Message('MINTING_KEY_FETCH_DENOMINATION',[['2'], '0']))
    <Message('MINTING_KEY_FAILURE',[['2', 'Unknown denomination']])>
   

    >>> gmp.newState(gmp.giveKey)
    >>> gmp.state(Message('MINTING_KEY_FETCH_KEYID',['non existant id']))
    <Message('MINTING_KEY_FAILURE',[['non existant id', 'Unknown key_identifier']])>

    >>> gmp.newState(gmp.giveKey)
    >>> gmp.state(Message('bla','blub'))
    <Message('PROTOCOL_ERROR','send again')>

    """

    def __init__(self,issuer):
        
        self.issuer = issuer
        Protocol.__init__(self)


    def start(self,message):

        if message.type == 'HANDSHAKE':
            if message.data['protocol'] == 'opencoin 1.0':
                self.newState(self.giveKey)
                return Message('HANDSHAKE_ACCEPT')
            else:
                self.newState(self.goodbye)
                return Message('HANDSHAKE_REJECT','did not like the protocol version')
        else:
            return Message('PROTOCOL_ERROR','please do a handshake')


    def giveKey(self,message):
    
        self.newState(self.goodbye)

        errors = []
        keys = []
        if message.type == 'MINTING_KEY_FETCH_DENOMINATION':
            try:
                denominations, time = message.data
            except ValueError: # catch tuple unpack errors
                return Message('PROTOCOL_ERROR', 'send again')

            if time == '0':
                time = self.issuer.getTime()
            else:
                time = containers.decodeTime(time)
                
            for denomination in denominations:
                try:
                    key = self.issuer.getKeyByDenomination(denomination, time)            
                    keys.append(key)
                except 'KeyFetchError': 
                    errors.append([denomination, 'Unknown denomination'])
        
        elif message.type == 'MINTING_KEY_FETCH_KEYID':                
            for keyid in message.data:
                try:
                    key = self.issuer.getKeyById(keyid)
                    keys.append(key)
                except 'KeyFetchError':                
                    errors.append([keyid, 'Unknown key_identifier'])
        
        else:
            return Message('PROTOCOL_ERROR', 'send again')

        if not errors:            
            return Message('MINTING_KEY_PASS',[key.toPython() for key in keys])
        else:
            return Message('MINTING_KEY_FAILURE',errors)

############################### For testing ########################################

class WalletSenderProtocol(Protocol):
    """
    This is just a fake protocol, just showing how it works

    >>> sp = WalletSenderProtocol(None)
   
    It starts with sending some money
    >>> sp.state(Message(None))
    <Message('sendMoney',[1, 2])>
    
    >>> sp.state(Message('Foo'))
    <Message('Please send a receipt',None)>

    Lets give it a receipt
    >>> sp.state(Message('Receipt'))
    <Message('Goodbye',None)>

    >>> sp.state(Message('Bla'))
    <Message('finished',None)>

    >>> sp.state(Message('Bla'))
    <Message('finished',None)>

    """

    def __init__(self,wallet):
        'we would need a wallet for this to work'

        self.wallet = wallet
        Protocol.__init__(self)

    def start(self,message):
        'always set the new state before returning'
        
        self.state = self.waitForReceipt
        return Message('sendMoney',[1,2])

    def waitForReceipt(self,message):
        'after sending we need a receipt'

        if message.type == 'Receipt':
            self.state=self.finish
            return Message('Goodbye')
        else:
            return Message('Please send a receipt')

class WalletRecipientProtocol(Protocol):

    def __init__(self,wallet=None):
        self.wallet = wallet
        Protocol.__init__(self)

    def start(self,message):
        if message.type == 'sendMoney':
            if self.wallet:
                self.wallet.coins.extend(message.data)
            self.state=self.Goodbye
            return Message('Receipt')
        else:
            return Message('Please send me money, mama')

    def Goodbye(self,message):
        self.state = self.finish
        return Message('Goodbye')

if __name__ == "__main__":
    import doctest,sys
    if len(sys.argv) > 1 and sys.argv[-1] != '-v':
        name = sys.argv[-1]
        gb = globals()
        verbose = '-v' in sys.argv 
        doctest.run_docstring_examples(gb[name],gb,verbose,name)
    else:        
        doctest.testmod(optionflags=doctest.ELLIPSIS)
