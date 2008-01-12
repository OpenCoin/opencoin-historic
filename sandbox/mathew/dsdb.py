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

from crypto import CryptoError

class Handler(object):
    pass

class LockCoins(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.messageType.addCallback(self.handle)

    def handle(self, message):
        if not isinstance(message, LockCoinsRequest) and not isinstance(message, LockCoinsAccept) and not isinstance(message, LockCoinsFailure):
            if self.manager.messageType.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('LockCoins should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                        self.manager.messageType.globals.lastState))
            else:
                print 'message class: %s' % message.__class__
                raise MessageError('We somehow called LockCoins.handle() but cannot be there. Message: %s' % message.identifier)

        if isinstance(message, LockCoinsRequest):
                self.key_id = self.manager.messageType.persistant.key_id
                self.transaction_id = self.manager.messageType.persistant.transaction_id
                self.blanks = self.manager.messageType.persistant.blanks # blanks is a tuple of mint_key_id and obfuscated serial

                self.type, self.result = self.lock(self.key_id, self.transaction_id, self.blanks, self.manager.dsdb_key,
                                                   self.manager.entity.dsdb_database, self.manager.entity.minting_keys_key_id, self.timeNow())
               
                if self.type == 'ACCEPT':
                    transaction_id, self.dsdb_lock = self.result
                    if self.transaction_id != transaction_id:
                        raise MessageError('transaction_id changed. Was: %s, Received: %s' % (self.transaction_id, transaction_id))
                    self.manager.messageType.persistant.dsdb_lock = self.dsdb_lock
                    
                    self.manager.messageType.removeCallback(self.handle) # we are done here
                    self.__createAndOutput(LockCoinsAccept)
                    
                elif self.type == 'REJECT':
                    self.manager.messageType.persistant.reason = self.result

                    self.manager.messageType.removeCallback(self.handle) # we are done here
                    self.__createAndOutput(LockCoinsFailure)

                else:
                    raise MessageError('Received an impossible type: %s' % self.type)

        elif isinstance(message, LockCoinsAccept) or isinstance(message, LockCoinsFailure):
            # we output this. Next step can only be Goodbye
            self.manager.messageType.removeCallback(self.handle)

    def lock(self, dsdb_key_id, transaction_id, blanks, dsdb_key, dsdb_database, minting_keys_key_id, now):
        failure = False
        failures = []

        blanksAndSerials = []

        if len(blanks) == 0:
            raise MessageError('request %s has no blinds' % request_id)

        if not self.validDSDBKeyID(dsdb_key_id, dsdb_key, now):
            return 'REJECT', 'Key ID of DSDB is unknown or expired'
        
        for b in blanks:
            type, result = self.testBlank(b, dsdb_key_id, dsdb_key, dsdb_database, minting_keys_key_id, now)
            if type == 'ACCEPT':
                blanksAndSerials.append((b, result)) # Add the tuple of the blank and the serial
            elif type == 'REJECT':
                failure = True
                failures.append( (b, result) )
            else:
                raise MessageError('Received impossible type: %s' % type)

        if failure:
            return 'REJECT', failures

        dsdb_lock_time = self.lockBlanks(transaction_id, blanksAndSerials, dsdb_key, dsdb_database, now)

        return 'ACCEPT', (transaction_id, dsdb_lock_time)

    def testBlank(self, blank, dsdb_key_id, dsdb_key, dsdb_database, minting_keys_key_id, now):
        mint_key_id, obfuscated = blank

        serial = self.unobfuscate(obfuscated, dsdb_key)
        if serial == 'Decryption of serial failed':
            return 'REJECT', 'Decryption of serial failed'

        if not minting_keys_key_id.has_key(mint_key_id) or not minting_keys_key_id[mint_key_id].verify_time(now):
            return 'REJECT', 'Key ID of blank is unknown or expired'
        
        if dsdb_database.has_key(mint_key_id):
            if dsdb_database[mint_key_id].has_key(serial):
                result = dsdb_database[mint_key_id][serial]
                if result[0] == 'Spent':
                    return 'REJECT', 'Serial already redeemed'
                elif result[0] == 'Locked':
                    string, time_lock_expires, transaction_id = result
                    if self.timeNow() <= time_lock_expires:
                        return 'REJECT', 'Serial locked (not spent)'
                    else:
                        # the serial is no longer locked. unlock it
                        del dsdb_database[mint_key_id][serial]
                        return 'ACCEPT', serial
                else:
                    raise MessageError('Got an impossible state: %s' % result[0])
            else: # we have never seen this serial
                return 'ACCEPT', serial
        else: # we have never seen this valid mint_key_id
            return 'ACCEPT', serial

        
    def validDSDBKeyID(self, dsdb_key_id, dsdb_key, now):
        return dsdb_key_id == dsdb_key.key_identifier and dsdb_key.verify_time(now)

    def __createAndOutput(self, message):
        m = message()
        self.manager.messageType.addOutput(m)

    def timeNow(self):
        import time
        return time.time()

    def unobfuscate(self, obfuscated, dsdb_key):
        enc = dsdb_key.cipher(dsdb_key.public_key)
        enc.update(obfuscated)
        
        try:
            serial = enc.decrypt()
        except CryptoError:
            return 'Decryption of serial failed'

        return serial

    def lockBlanks(self, transaction_id, blanksAndSerials, dsdb_key, dsdb_database, now):
        """locks the serials in the dsdb_database and returns the dsdb_lock_time."""
        dsdb_lock_time = now + 5 * 60 # 5 minute lock #FIXME: should be setable somewhere.

        #FIXME this is ugly. It doesn't delete transactions as they expire

        for bas in blanksAndSerials:
            blank, serial = bas
            mint_key, obfuscated_serial = blank
            if not dsdb_database.has_key(mint_key):
                dsdb_database[mint_key] = {} # Make it

            # FIXME: This assumes only one transaction at a time is going on twith the dsdb. If two concurrent transactions happen, this will not catch them
            dsdb_database[mint_key][serial] = ('Locked', dsdb_lock_time, transaction_id)

        return dsdb_lock_time
        

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
                    self.manager.messageType.removeCallback(self.handle)
                    self.__createAndOutput(UnlockCoinsPass)
                    
                elif self.type == 'REJECT':
                    transaction_id, self.reason = self.result
                    if self.transaction_id != transaction_id:
                        raise MessageError('transaction_id changed. Was: %s, Now: %s' % (self.transation_id, transaction_id))
                    self.manager.messageType.persistant.reason = self.reason

                    self.manager.messageType.removeCallback(self.handle)
                    self.__createAndOutput(UnlockCoinsFailure)

                else:
                    raise MessageError('Received an impossible type: %s' % self.type)

        elif isinstance(message, UnlockCoinsPass) or isinstance(message, UnlockCoinsFailure):
            # we output this. Next step can only be Goodbye
            self.manager.messageType.removeCallback(self.handle)

    def unlock(self, transaction_id):
        # raise NotImplementedError
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
        self.dsdb_key = self.entity.dsdb_key
        
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
        

