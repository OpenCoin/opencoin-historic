from message import LockCoinsRequest
from message import LockCoinsAccept
from message import LockCoinsFailure
from message import UnlockCoinsRequest
from message import UnlockCoinsPass
from message import UnlockCoinsFailure

from message import MessageType
from message import MessageStatuses
#from message import MessageHandler
from message import statusHandleServer
from message import MessageError
from message import Hello as MessageHello

#import crypto stuff

class Handler(object):
    pass

class LockCoins(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.messageType.addCallback(self.handle)

    def handle(self, message):
        if not isinstance(message, LockCoinsRequest) and not isinstance(message, LockCoinsAccept) and not isinstance(message, LockCoinsFailure):
            if self.manager.messageType.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('Mint should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                        self.manager.messageType.globals.lastState))
            else:
                print 'message class: %s' % message.__class__
                raise MessageError('We somehow called Mint.handle() but cannot be there. Message: %s' % message.identifier)

        if isinstance(message, LockCoinsRequest):
                self.key_id = self.manager.messageType.persistant.key_id
                self.transaction_id = self.manager.messageType.persistant.transaction_id
                self.blanks = self.manager.messageType.persistant.blanks

                self.type, self.result = self.lock(self.key_id, self.transaction_id, self.blanks)
                
                if self.type == 'ACCEPT':
                    transaction_id, self.dsdb_lock = self.result
                    if self.transaction_id != transaction_id:
                        raise MessageError('transaction_id changed. Was: %s, Received: %s' % (self.transaction_id, transaction_id))
                    self.manager.messageType.persistant.dsdb_lock = self.dsdb_lock
                    self.__createAndOutput(LockCoinsAccept)
                    
                elif self.type == 'REJECT':
                    transaction_id, self.reason = self.result
                    if self.transaction_id != transaction_id:
                        raise MessageError('transaction_id changed. Was: %s, Received: %s' % (self.transaction_id, transaction_id))
                    self.manager.messageType.persistant.reason = self.reason
                    self.__createAndOutput(LockCoinsFailure)

                else:
                    raise MessageError('Received an impossible type: %s' % self.type)

        elif isinstance(message, LockCoinsAccept) or isinstance(message, LockCoinsFailure):
            # we output this. Next step can only be Goodbye
            self.manager.messageType.removeCallback(self.handle)

    def lock(self, dsdb_key_id, transaction_id, blanks):
        failure = False
        failures = []

        if len(blanks) == 0:
            raise MessageError('request %s has no blinds' % request_id)

        if not self.validDSDBKeyID(dsdb_key_id):
            return 'REJECT', 'Key ID of DSDB is unknown or expired'
        
        for b in blanks:
            result = self.testBlank(b, dsdb_key_id)
            if result == 'ACCEPT':
                pass
            else:
                failure = True
                failures.append( (b, result) )

        if failure:
            return 'REJECT', failures

        self.lockBlanks(dsdb_key_id, request_id, blanks)

        return 'ACCEPT', request_id

    def testBlank(self, blank, dsdb_key_id):
        key_id, blind = blind
        raise NotImpolementedError
        #for testing, require key_id to be between 10 and 999999 and blind to be less than a million
        if key_id < 10 or key_id > 999999:
            return 'Unknown key_id'

        if blank < 10000000:
            return 'Unable to blind'

        return 'ACCEPT'

    def validDSDBKeyID(self, dsdb_key_id):
        if dsdb_key_id < 10000:
            return False
        return True

    def __createAndOutput(self, message):
        m = message()
        self.manager.messageType.addOutput(m)


class UnlockCoins(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.messageType.addCallback(self.handle)

    def handle(self, message):
        if not isinstance(message, UnlockCoinsRequest) and not isinstance(message, UnlockCoinsPass) and not isinstance(message, UnlockCoinsFailure):
            if self.manager.messageType.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('UnlockCoins should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                        self.manager.messageType.globals.lastState))
            else:
                print 'message class: %s' % message.__class__
                raise MessageError('We somehow called UnlockCoins.handle() but cannot be there. Message: %s' % message.identifier)

        if isinstance(message, UnlockCoinsRequest):
                self.transaction_id = self.manager.messageType.persistant.transaction_id

                self.type, self.result = self.unlock(self.transaction_id)
                
                if self.type == 'ACCEPT':
                    self.__createAndOutput(UnlockCoinsPass)
                    
                elif self.type == 'REJECT':
                    transaction_id, self.reason = self.result
                    if self.transaction_id != transaction_id:
                        raise MessageError('transaction_id changed. Was: %s, Now: %s' % (self.transation_id, transaction_id))
                    self.manager.messageType.persistant.reason = self.reason
                    self.__createAndOutput(UnlockCoinsFailure)

                else:
                    raise MessageError('Received an impossible type: %s' % self.type)

        elif isinstance(message, UnlockCoinsPass) or isinstance(message, UnlockCoinsFailure):
            # we output this. Next step can only be Goodbye
            self.manager.messageType.removeCallback(self.handle)

    def unlock(self, transaction_id):
        if transaction_id < 100:
            return 'REJECT', 'Unknown transaction_id'
        if transaction_id < 10000:
            return 'REJECT', 'Transaction already completed'
        if transaction_id < 1000000:
            return 'REJECT', 'Lock expired'

        return 'ACCEPT', None

    def __createAndOutput(self, message):
        m = message()
        self.manager.messageType.addOutput(m)



class HandlerManager(object):
    def __init__(self, messageType, entity):
        self.messageType = messageType
        self.entity = entity # the entity that spawned us
        
        if not self.messageType.globals.status.can(MessageStatuses.PrivilegeServer):
            raise MessageError('given messageType does not have PrivilegeServer')
        
        class messages: pass
        self.messages = messages
        del messages

        #create conversation starting messages to trigger self.startConversation
        self.messages.LCR = LockCoinsRequest(self.startConversation)
        self.messages.UCR = UnlockCoinsRequest(self.startConversation)

        #add all of our special mesasges as MessageHandlers
        self.messageType.addMessageHandler(self.messages.LCR)
        self.messageType.addMessageHandler(self.messages.UCR)
        
        #everything that can't start a conversation
        self.messageType.addMessageHandler(LockCoinsAccept())
        self.messageType.addMessageHandler(LockCoinsFailure())
        self.messageType.addMessageHandler(UnlockCoinsPass())
        self.messageType.addMessageHandler(UnlockCoinsFailure())

        self.manager = None
        
    def startConversation(self, message, result):
        if isinstance(message, self.messages.LCR.__class__):
            self.setHandler(LockCoins(self, message))
        elif isinstance(message, self.messages.UCR.__class__):
            self.setHandler(UnlockCoins(self, message))
        else:
            raise MessageError("Message %s does not start a conversation" % message.identifier)

    def setHandler(self, handler):
        """Sets the current handler for the manager. Is this used for anything?"""
        self.handler = handler
        

