from message import DSDBKeyRequest
from message import DSDBKeyPass
from message import BlankPresent
from message import BlankReject
from message import BlankFailure
from message import BlankAccept
from message import CoinsRedeem
from message import CoinsReject
from message import CoinsAccept

from message import MessageType
from message import MessageStatuses
#from message import MessageHandler
#from message import statusHandleServer
from message import MessageError
from message import Hello as MessageHello

#import crypto stuff

class ConsumerWalletManager(object):
    def __init__(self, walletMessageType, entity, coins):
        self.walletMessageType = walletMessageType
        self.entity = entity

        #self.isMessageType = isMessageType
        if not self.walletMessageType.globals.status.can(MessageStatuses.PrivilegeClient):
            raise MessageError('given messageType does not have PrivilegeClient')
        #if not self.isMessageType.globals.status.can(MessageStatuses.PrivilegeClient):
        #    raise MessageError('given messageType does not have PrivilegeClient')
        

        class messages: pass
        self.walletMessages = messages()
        self.isMessages = messages()
        del messages

        # All the responses we can get from the IS
        self.isMessages.DKP = DSDBKeyPass(self.resumeConversation)

        # All the responses we can get from the other wallet
        self.walletMessages.BR = BlankReject(self.resumeConversation)
        self.walletMessages.BF = BlankFailure(self.resumeConversation)
        self.walletMessages.BA = BlankAccept(self.resumeConversation)
        self.walletMessages.CR = CoinsReject(self.resumeConversation)
        self.walletMessages.CA = CoinsAccept(self.resumeConversation)

        ## Add handlers for all the messages, using isMessages if continues conversation
        #self.isMessageType.addMessageHandler(DSDBKeyRequest())
        #self.isMessageType.addMessageHandler(self.isMessages.DKP)

        # Add handlers for all the messages using walletMessages if continues conversation
        self.walletMessageType.addMessageHandler(BlankPresent())
        self.walletMessageType.addMessageHandler(self.walletMessages.BR)
        self.walletMessageType.addMessageHandler(self.walletMessages.BF)
        self.walletMessageType.addMessageHandler(self.walletMessages.BA)
        self.walletMessageType.addMessageHandler(CoinsRedeem())
        self.walletMessageType.addMessageHandler(self.walletMessages.CR)
        self.walletMessageType.addMessageHandler(self.walletMessages.CA)

        self.coins = coins

        class state: pass
        self.persistant = state()
        del state

        self.lastMessageIdentifier = None

    def resumeConversation(self, message, result):
        if isinstance(message, DSDBKeyPass):
            self.setHandler(DSDBKey(self, message))
        elif isinstance(message, BlankReject) or isinstance(message, BlankFailure) or isinstance(message, BlankAccept):
            self.setHandler(Blank(self, message))
        elif isinstance(message, CoinsReject) or isinstance(message, CoinsAccept):
            self.setHandler(Coins(self, message))

        else:
            raise MessageError('Message %s does not continue a conversation' % message.identifier)

    def setHandler(self, handler):
        self.handler = handler

    def startConversation(self):
        #this is kind of a hack. Okay. A lot of a hack
        self.connectToIS(self.entity.cdds[self.coins[0].currency_identifier])

        dkr = DSDBKeyRequest()
        self.isMessageType.addOutput(dkr) # and so it starts. Flow follows to DSDBKey

    def success(self, message, handler):
        print 'Received a success! Message class: %s. Handler class: %s' % (message.__class__, handler.__class__)

    def failure(self, message, handler):
        print 'Received a failure. Message %s Sentence: %s' % (message.identifier, message.sentence)
        print 'We should do something like un-hook ourselves or something.'

    def connectToIS(self, currency_description_document):
        """sets up the isMessageType and links the callbacks."""
        client = MessageStatuses.getBaseClient()
        self.isMessageType = MessageType(client)
        
        # Add handlers for all the messages, using isMessages if continues conversation
        self.isMessageType.addMessageHandler(DSDBKeyRequest())
        self.isMessageType.addMessageHandler(self.isMessages.DKP)

        self.entity.connectToIS(self.isMessageType, currency_description_document)

        #FIXME: This is one of many places we enforce the one currency at a time
        self.cdd = currency_description_document

class Handler(object):
    def _createAndOutput(self, message, messageType):
        m = message()
        messageType.addOutput(m)

    def _createAndOutputIS(self, message):
        self._createAndOutput(message, self.manager.isMessageType)
    
    def _createAndOutputWallet(self, message):
        self._createAndOutput(message, self.manager.walletMessageType)
        
    def _setLastState(self, state):
        print 'setting last state: %s' % state
        self.manager.lastMessageIdentifier = state

    def _verifyLastState(self, state):
        """_verifyLastState is used to make sure that we are progressing properly through messages which can start at Hello.
        For any message which can start at Hello, perform a check to make sure that we have the required lastState in the manager.
        A lastState of None is the beginning.
        """
        if not self.manager.lastMessageIdentifier in state:
            raise MessageError('Did not find expected last state. Found: %s, Wanted: %s' % (self.manager.lastMessageIdentifier, state))

class DSDBKey(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.isMessageType.addCallback(self.handle)

    def handle(self, message):
        if not isinstance(message, DSDBKeyRequest) and not isinstance(message, DSDBKeyPass):
            if self.manager.isMessageType.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('RedeemCoins should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                self.manager.isMessageType.globals.lastState))
            else:
                raise MessageError('We somehow called RedeemCoins.handle() but cannot be there. Message: %s' % message.identifier)

        self._verifyLastState([None])

        if isinstance(message, DSDBKeyRequest):
            # we output this. Previous step was Hello. Do nothing.
            print 'Got a DSDBKeyRequest. I did not know we got these.'

        elif isinstance(message, DSDBKeyPass):
            self.dsdb_certificate = self.manager.isMessageType.persistant.dsdb_certificate 
            self.manager.persistant.dsdb_certificate = self.dsdb_certificate # keep a copy for me
            self.manager.walletMessageType.persistant.dsdb_certificate = self.dsdb_certificate # and we need to encode it
            
            if not self.validCertificate(self.dsdb_certificate, self.manager.cdd, self.getTime()):
                raise MessageError('Invalid DSDB Certificate')
            
            self.createBlinds(self.dsdb_certificate, self.manager.coins)
            self.manager.isMessageType.removeCallback(self.handle) # not coming back here again
            self._createAndOutputWallet(BlankPresent)

        self._setLastState(message.identifier)

    def validCertificate(self, dsdb_certificate, currency_description_document, time):
        """returns if the dsdb_certificate is valid right now."""
        valid = dsdb_certificate.verify_with_CDD(currency_description_document)

        if not valid:
            return False

        return dsdb_certificate.verify_time(time)

    def getTime(self):
        import time

        return time.time()

    def createBlinds(self, dsdb_certificate, coins):
        if len(coins) == 0:
            raise MessageError('Can not blind no coins!')

        blinds = []
        for c in coins:
            blinds.append(self.createBlind(dsdb_certificate, c))

        self.manager.walletMessageType.persistant.blanks = blinds

    def createBlind(self, dsdb_certificate, coin):
        return coin.newObfuscatedBlank(dsdb_certificate)


class Blank(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.walletMessageType.addCallback(self.handle)

    def handle(self, message):
        if not isinstance(message, BlankPresent) and not isinstance(message, BlankAccept) and not isinstance(message, BlankReject) and not isinstance(message, BlankFailure):
            if self.manager.walletMessageType.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('Blank should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                self.manager.walletMessageType.globals.lastState))
            else:
                raise MessageError('We somehow called Blank.handle() but cannot be there. Message: %s' % message.identifier)

        if isinstance(message, BlankPresent):
            # we output this. Previous step was Hello. Do nothing.
            self._verifyLastState(['DSDB_KEY_PASS'])
            print 'Got a BlankPresent. I did not know we got these.'

        elif isinstance(message, BlankAccept):
            self.manager.walletMessageType.persistant.coins = self.manager.coins
            self.manager.walletMessageType.removeCallback(self.handle) #remove the callback. Not coming here again
            self._createAndOutputWallet(CoinsRedeem)

        elif isinstance(message, BlankFailure):
            self.reason = self.manager.walletMessageType.persistant.reason
            # undo the damage and tell someone
            self.manager.failure(message, self)

        elif isinstance(message, BlankReject):
            self.reason = self.manager.walletMessageType.persistant.reason
            self.manager.failure(message, self)

        self._setLastState(message.identifier)

class Coins(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.walletMessageType.addCallback(self.handle)

    def handle(self, message):
        if not isinstance(message, CoinsRedeem) and not isinstance(message, CoinsReject) and not isinstance(message, CoinsAccept):
            if self.manager.walletMessageType.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('Coins should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                self.manager.walletMessageType.globals.lastState))
            else:
                raise MessageError('We somehow called Coins.handle() but cannot be there. Message: %s' % message.identifier)

        if isinstance(message, CoinsRedeem):
            # we output this. Previous step was Hello. Do nothing.
            print 'Got a CoinsRedeem. I did not know we got these.'

        elif isinstance(message, CoinsAccept):
            self.removeSpentCoins(self.manager.entity.coins, self.manager.coins)
            
            self.manager.walletMessageType.removeCallback(self.handle)
            self.manager.success(message, self)

        elif isinstance(message, CoinsReject):
            self.reason = self.manager.walletMessageType.persistant.reason
            
            self.manager.walletMessageType.removeCallback(self.handle)
            # undo the damage and tell someone
            self.manager.failure(message, self)

        self._setLastState(message.identifier)


    def removeSpentCoins(self, entity_coins, coins):
        """Removes spent coins from our wallet."""
        for c in coins:
            entity_coins.remove(c)
