from message import MintingKeyFetchDenomination
from message import MintingKeyFetchKeyID
from message import MintingKeyPass
from message import MintingKeyFailure
from message import MintRequest
from message import MintReject
from message import MintAccept
from message import FetchMintedRequest
from message import FetchMintedFailure
from message import FetchMintedWait
from message import FetchMintedAccept
from message import DSDBKeyRequest
from message import DSDBKeyPass
from message import RedeemCoinsRequest
from message import RedeemCoinsReject
from message import RedeemCoinsAccept

from message import MessageType
from message import MessageStatuses
#from message import MessageHandler
from message import statusHandleServer
from message import MessageError
from message import Hello as MessageHello

#import crypto stuff

class Handler(object):
    pass

class FetchMinted(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.messageType.addCallback(self.handle)

        #FIXME: This is a hack. It should be setup somewhere else
        self.isRequiresMRbeforeRCR = True

    def handle(self, message):
        if not isinstance(message, FetchMintedRequest) and not isinstance(message, FetchMintedFailure) and not \
                            isinstance(message, FetchMintedWait) and not isinstance(message, FetchMintedAccept):
            if self.manager.messageType.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('FetchMinted should have already been removed. It was not. Very odd. Message: %s' % message.identifier)
                self.manager.messageType.removeCallback(self.handle)
            else:
                print 'message class: %s' % message.__class__
                raise MessageError('We somehow called FetchMinted.handle() but cannot be there. Message: %s' % message.identifier)

        if isinstance(message, FetchMintedRequest):
            self.request_id = self.manager.messageType.persistant.request_id

            # FIXME: Hack to ensure we try to mint things. Run the minting right now, if we have it
            self.manager.entity.attemptToMint() # this tries to mint everything waiting
            
            type, result = self.findRequest(self.request_id)

            if type == 'ACCEPT':
                self.signatures = result
                self.manager.messageType.persistant.signatures = result
                self.__createAndOutput(FetchMintedAccept)

            elif type == 'WAIT':
                self.reason = result
                self.manager.messageType.persistant.reason = result
                self.__createAndOutput(FetchMintedWait)

            elif type == 'FAILURE':
                self.reason = result
                self.manager.messageType.persistant.reason = result
                self.__createAndOutput(FetchMintedFailure)

            else:
                raise MessageError('Received unknown type: %s' % type)

        elif isinstance(message, FetchMintedAccept):
            # we output this. Next step can only be Goodbye
            self.manager.messageType.removeCallback(self.handle)

        elif isinstance(message, FetchMintedFailure):
            #we output this. Next step can only be Goodbye
            self.manager.messageType.removeCallback(self.handle)

        elif isinstance(message, FetchMintedWait):
            # we output this. Next step can only be Goodbye
            self.manager.messageType.removeCallback(self.handle)

    def findRequest(self, request_id):
        if self.manager.entity.minted.has_key(request_id):
            result = 'ACCEPT', self.manager.entity.minted[request_id]
            del self.manager.entity.minted[request_id]
            return result

        if self.manager.entity.mint_waiting.has_key(request_id):
            reason, currency = self.manager.entity.mint_waiting[request_id]
            if not self.isRequiresMRbeforeRCR:
                if reason != 'Request not credited':
                    return 'WAIT', reason
                else:
                    #FIXME: This mode should be impossible. It wouldn't be stored becuase we would have rejected it.
                    return 'FAILURE', reason
            else:
                return 'WAIT', reason

        if self.manager.entity.mint_failures.has_key(request_id):
            return 'FAILURE', self.manager.entity.mint_failures[request_id]


    def __createAndOutput(self, message):
        m = message()
        self.manager.messageType.addOutput(m)




class MintingKey(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.messageType.addCallback(self.handle)

    def handle(self, message):
        if not isinstance(message, MintingKeyFetchDenomination) and not isinstance(message, MintingKeyFetchKeyID) and not \
                            isinstance(message, MintingKeyFailure) and not isinstance(message, MintingKeyPass):
            if self.manager.messageType.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('MintingKey should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                        self.manager.messageType.globals.lastState))
            else:
                print 'message class: %s' % message.__class__
                raise MessageError('We somehow called MintingKey.handle() but cannot be there. Message: %s' % message.identifier)

        if isinstance(message, MintingKeyFetchKeyID) or isinstance(message, MintingKeyFetchDenomination):
            if isinstance(message, MintingKeyFetchKeyID):
                self.key_id = self.manager.messageType.persistant.key_id
                self.denomination = None
            else:
                self.denomination = self.manager.messageType.persistant.denomination
                self.key_id = None

            type, result = self.findKey(self.key_id, self.denomination)

            if type == 'PASS':
                self.minting_certificate = result
                self.manager.messageType.persistant.minting_certificate = self.minting_certificate

                self.manager.messageType.removeCallback(self.handle)
                self.__createAndOutput(MintingKeyPass)
            elif type == 'FAILURE':
                self.manager.messageType.persistant.reason = result
                if result == 'Unknown key_id':
                    self.reason = 'Unknown key_id'

                    self.manager.messageType.persistant.reason = self.reason

                    self.manager.messageType.removeCallback(self.handle)
                    self.__createAndOutput(MintingKeyFailure)
                elif result == 'Unknown denomination':
                    self.reason = 'Unknown denomination'
                        
                    self.manager.messageType.persistant.reason = self.reason

                    self.manager.messageType.removeCallback(self.handle)
                    self.__createAndOutput(MintingKeyFailure)
                else:
                    raise MessageError('Received impossible result: %s' % result)
            else:
                raise MessageError('Received impossible type: %s' % type)

        elif isinstance(message, MintingKeyPass) or isinstance(message, MintingKeyFailure):
            # we output this. Next step can only be Goodbye
            print 'we should never get here. Message: %s' % message.identifier
            self.manager.messageType.removeCallback(self.handle)

    def findKey(self, key_id, denomination):
        if key_id:
            if self.manager.entity.minting_keys_key_id.has_key(key_id):
                return 'PASS', self.manager.entity.minting_keys_key_id[key_id]
            else:
                return 'FAILURE', 'Unknown key_id'
        else:
            if self.manager.entity.minting_keys_denomination.has_key(denomination):
                return 'PASS', self.mostCurrentValid(self.manager.entity.minting_keys_denomination[denomination], self.timeNow())
            else:
                return 'FAILURE', 'Unknown denomination'

    def __createAndOutput(self, message):
        m = message()
        self.manager.messageType.addOutput(m)

    def timeNow(self):
        import time
        return time.time()

    def mostCurrentValid(self, keys, now):
        if len(keys) > 1:
            raise NotImplementedError

        return keys[0]

class DSDBKey(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.messageType.addCallback(self.handle)

    def handle(self, message):
        if not isinstance(message, DSDBKeyRequest) and not isinstance(message, DSDBKeyPass):
            if self.manager.messageType.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('DSDBKey should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                        self.manager.messageType.globals.lastState))
            else:
                print 'message class: %s' % message.__class__
                raise MessageError('We somehow called DSDBKey.handle() but cannot be there. Message: %s' % message.identifier)

        if isinstance(message, DSDBKeyRequest):
                self.dsdb_certificate = self.dsdbKey()

                self.manager.messageType.persistant.dsdb_certificate = self.dsdb_certificate
                self.__createAndOutput(DSDBKeyPass)

        elif isinstance(message, DSDBKeyPass):
            # we output this. Next step can only be Goodbye
            self.manager.messageType.removeCallback(self.handle)

    def dsdbKey(self):
        return self.manager.entity.dsdb_key

    def __createAndOutput(self, message):
        m = message()
        self.manager.messageType.addOutput(m)



class Mint(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.messageType.addCallback(self.handle)

    def handle(self, message):
        if not isinstance(message, MintRequest) and not isinstance(message, MintAccept) and not isinstance(message, MintReject):
            if self.manager.messageType.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('Mint should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                        self.manager.messageType.globals.lastState))
            else:
                print 'message class: %s' % message.__class__
                raise MessageError('We somehow called Mint.handle() but cannot be there. Message: %s' % message.identifier)

        if isinstance(message, MintRequest):
                self.request_id = self.manager.messageType.persistant.request_id
                self.blinds = self.manager.messageType.persistant.blinds

                type, result = self.request(self.request_id, self.blinds, self.manager.entity.minting_keys_key_id, self.timeNow())
                
                if type == 'ACCEPT':
                    if self.request_id != result:
                        raise MessageError('request_id changed. Was: %s, Received: %s' % (self.request_id, result))

                    self.manager.messageType.removeCallback(self.handle)
                    self.__createAndOutput(MintAccept)
                    
                elif type == 'REJECT':
                    self.manager.messageType.persistant.reason = result

                    self.manager.messageType.removeCallback(self.handle)
                    self.__createAndOutput(MintReject)

                else:
                    raise MessageError('Received an impossible type: %s' % self.type)

        elif isinstance(message, MintAccept) or isinstance(message, MintReject):
            # we output this. Next step can only be Goodbye
            self.manager.messageType.removeCallback(self.handle)

    def request(self, request_id, blinds, minting_keys_key_id, now):
        failure = False
        failures = []

        if len(blinds) == 0:
            raise MessageError('request %s has no blinds' % request_id)

        for b in blinds:
            type, result = self.testBlind(b, minting_keys_key_id, now)
            if type == 'ACCEPT':
                pass
            elif type == 'REJECT':
                failure = True
                key_id, blind = b
                failures.append( (blind, result) )

        if failure:
            return 'REJECT', failures

        self.acceptBlinds(request_id, blinds)

        return 'ACCEPT', request_id

    def testBlind(self, blind, minting_keys_key_id, now):
        key_id, blind = blind

        if not minting_keys_key_id.has_key(key_id) or not minting_keys_key_id[key_id].verify_time(now):
            return 'REJECT', 'Unknown key_id'

        if len(blind) > minting_keys_key_id[key_id].public_key.key.size(): # FIXME: this will probably break if we change from RSA
            return 'REJECT', 'Unable to blind'

        return 'ACCEPT', None


    def acceptBlinds(self, request_id, blinds):
        self.manager.entity.mint_waiting[request_id] = ('No attempt to mint', blinds)

    def timeNow(self):
        import time
        return time.time()

    def __createAndOutput(self, message):
        m = message()
        self.manager.messageType.addOutput(m)

       
class RedeemCoins(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.messageType.addCallback(self.handle)

    def handle(self, message):
        if not isinstance(message, RedeemCoinsRequest) and not isinstance(message, RedeemCoinsAccept) and not isinstance(message, RedeemCoinsReject):
            if self.manager.messageType.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('RedeemCoins should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                        self.manager.messageType.globals.lastState))
            else:
                print 'message class: %s' % message.__class__
                raise MessageError('We somehow called RedeemCoins.handle() but cannot be there. Message: %s' % message.identifier)

        if isinstance(message, RedeemCoinsRequest):
                self.transaction_id = self.manager.messageType.persistant.transaction_id
                self.target = self.manager.messageType.persistant.target
                self.coins = self.manager.messageType.persistant.coins

                type, result = self.redeem(self.transaction_id, self.target, self.coins, self.manager.entity.cdd,
                                           self.manager.entity.minting_keys_key_id, self.manager.entity.dsdb_database,
                                           self.manager.entity.dsdb_requests)

                if type == 'ACCEPT':
                    self.manager.messageType.removeCallback(self.handle)
                    self.__createAndOutput(RedeemCoinsAccept)

                elif type == 'REJECT':
                    self.manager.messageType.persistant.reason = result
                    self.manager.messageType.removeCallback(self.handle)
                    self.__createAndOutput(RedeemCoinsReject)

                else:
                    raise MessageError('Received an impossible type: %s' % self.type)

        elif isinstance(message, RedeemCoinsAccept) or isinstance(message, RedeemCoinReject):
            # we output this. Next step can only be Goodbye
            self.manager.messageType.removeCallback(self.handle)

        else:
            raise MessageError('Trying to handle a message we are not designed for: %s' % message.identifier)

    def redeem(self, transaction_id, target, coins, currency_description_document, minting_keys_key_id, dsdb_database, dsdb_requests):
        """redeem checks the validity of the coins.
        redeem first checks the validity of the coins. It then verifies the target.
        Finally, it tries to redeem all the coins at once. This action first verifies then updates the DSDB.
        """
        failure = False
        failures = []

        if len(coins) == 0:
            raise MessageError('transaction %s has no coins' % transaction_id)

        for c in coins:
            type, result = self.testCoin(c, transaction_id, currency_description_document, minting_keys_key_id)
            if type == 'ACCEPT':
                pass
            elif type == 'REJECT':
                failure = True
                failures.append( (coin, result) )
            else:
                raise MessageError('Received impossible type: %s' % type)

        if failure:
            return 'REJECT', failures

        if not self.checkValidTarget(target):
            return 'REJECT', 'Unknown target'
        
        type, result = self.redeemCoins(transaction_id, target, coins, dsdb_database, dsdb_requests)
        if type == 'ACCEPT':
            return 'ACCEPT', None
        elif type == 'REJECT':
            return 'REJECT', result
        else:
            raise MessageError('Received impossible type: %s' % type)

    def testCoin(self, coin, transaction_id, currency_description_document, minting_keys_key_id):
        if not self.validKeyID(coin, minting_keys_key_id):
            return 'REJECT', 'Unknown key_id'

        minting_key = minting_keys_key_id[coin.key_identifier]
        if not self.validCoin(coin, currency_description_document, minting_key):
            return 'REJECT', 'Invalid coin'
        
        else:
            return 'ACCEPT', None

    def validKeyID(self, coin, minting_keys_key_id):
        """Returns whether the coin has a valid key_identifier."""
        # FIXME: does this mean that the key_identifier still has to be valid?
        return minting_keys_key_id.has_key(coin.key_identifier)

    def validCoin(self, coin, currency_description_document, minting_key):
        """Returns whether the coin is a valid coin with signature."""
        return coin.validate_with_CDD_and_MintingKey(currency_description_document, minting_key)

    def checkValidTarget(self, target):
        #FIXME This needs to be really implemented.
        return True

    def redeemCoins(self, transaction_id, target, coins, dsdb_database, dsdb_requests):
        """Redeem coins updates the DSDB locking out the coins and credits the target."""
        if not dsdb_requests.has_key(transaction_id):
            return 'REJECT', 'Unknown transaction_id' #FIXME: This error isn't in the standard

        dsdb_lock_time, keysAndSerials = dsdb_requests[transaction_id]

        #FIXME: There is probably a timing attack against the dsdb here where one redeems the locked coins twice
        
        coinKeysAndSerials = []
        for c in coins:
            coinKeysAndSerials.append( (c.key_identifier, c.serial) )

        if len(coinKeysAndSerials) != len(coinKeysAndSerials):
            return 'REJECT', 'Unknown transaction_id' #FIXME: This error isn't in the standard

        # Check the coin keys and serials against the dsdb locked ones
        for kAndS in keysAndSerials:
            if kAndS not in coinKeysAndSerials:
                return 'REJECT', 'Unknown transaction_id' # FIXME: This error isn't in the standard
            coinKeysAndSerials.remove(kAndS) # Remove the serial from the list. This prevents trying to use the same coin twice in one redeem

        # change the status of all the serials to locked
        for key, serial in keysAndSerials:
            dsdb_database[key][serial] = ('Spent',)

        # Remove the transaction_id from the dsdb_requests
        del dsdb_requests[transaction_id]

        worth = self.figureWorth(coins)

        self.creditTarget(target, worth)

        return 'ACCEPT', None

    def figureWorth(self, coins):
        #FIXME: implement me!
        return None

    def creditTarget(self, target, worth):
        #FIXME: Implement me!
        pass

    def __createAndOutput(self, message):
        m = message()
        self.manager.messageType.addOutput(m)


class HandlerManager(object):
    def __init__(self, messageType, entity):
        self.messageType = messageType
        self.entity = entity

        if not self.messageType.globals.status.can(MessageStatuses.PrivilegeServer):
            raise MessageError('given messageType does not have PrivilegeServer')
        
        class messages: pass
        self.messages = messages
        del messages

        #create conversation starting messages to trigger self.startConversation
        self.messages.DKR = DSDBKeyRequest(self.startConversation)
        self.messages.FMR = FetchMintedRequest(self.startConversation)
        self.messages.MR = MintRequest(self.startConversation)
        self.messages.MKFD = MintingKeyFetchDenomination(self.startConversation)
        self.messages.MKFK = MintingKeyFetchKeyID(self.startConversation)
        self.messages.RCR = RedeemCoinsRequest(self.startConversation)

        #add all of our special mesasges as MessageHandlers
        self.messageType.addMessageHandler(self.messages.DKR)
        self.messageType.addMessageHandler(self.messages.FMR)
        self.messageType.addMessageHandler(self.messages.MR)
        self.messageType.addMessageHandler(self.messages.MKFD)
        self.messageType.addMessageHandler(self.messages.MKFK)
        self.messageType.addMessageHandler(self.messages.RCR)
        
        #everything that can't start a conversation
        self.messageType.addMessageHandler(MintingKeyPass())
        self.messageType.addMessageHandler(MintingKeyFailure())
        self.messageType.addMessageHandler(MintReject())
        self.messageType.addMessageHandler(MintAccept())
        self.messageType.addMessageHandler(FetchMintedFailure())
        self.messageType.addMessageHandler(FetchMintedWait())
        self.messageType.addMessageHandler(FetchMintedAccept())
        self.messageType.addMessageHandler(DSDBKeyPass())
        self.messageType.addMessageHandler(RedeemCoinsReject())
        self.messageType.addMessageHandler(RedeemCoinsAccept())

        self.manager = None
        
    def startConversation(self, message, result):
        if isinstance(message, DSDBKeyRequest):
            self.setHandler(DSDBKey(self, message))
        elif isinstance(message, FetchMintedRequest):
            self.setHandler(FetchMinted(self, message))
        elif isinstance(message, MintRequest):
            self.setHandler(Mint(self, message))
        elif isinstance(message, MintingKeyFetchDenomination) or isinstance(message, MintingKeyFetchKeyID):
            self.setHandler(MintingKey(self, message))
        elif isinstance(message, RedeemCoinsRequest):
            self.setHandler(RedeemCoins(self, message))
        else:
            raise MessageError("Message %s does not start a conversation" % message.identifier)

    def setHandler(self, handler):
        """Sets the current handler for the manager. Is this used for anything?"""
        self.handler = handler
        

