terrible_hack = 1

class MessageType(object):
    def __init__(self, basestatus, callback=None):
        class globals(object): pass
        self.globals = globals
        del globals

        self.globals.handlers = {}
        self.globals.lastState = None
        self.globals.state = Hello
        self.globals.status = basestatus
        
        self.callback = []
        if callback:
            self.callback.append(callback)

        self.__clearPersistant()

        if not terrible_hack:
            self.input = ''
            self.output = ''
        else:
            self.input = []
            self.output = []

    def addMessageHandler(self, handler):
        self.globals.handlers[handler.identifier] = handler

    def addInput(self, input):
        self.input.append(input)
        while self.input:
            #print 'addInput() looping'
            if not terrible_hack:
                raise NotImplementedError
            else:
                message, self.input = self.input[0], self.input[1:]
                try:
                    #print 'making handler'
                    message = self.getHandler(message.identifier, message)
                    #print 'handling'
                    result = message.handle()
                    if self.callback:
                        for f in self.callback:
                            f(result)
                except MessageError:
                    #Do error handling
                    raise #or rethrow exception for now

    def addOutput(self, message):
        #print 'addOutput()'
        try:
            if not message.messageHandler:
                raise MessageError('messageHandler for message %s is None!' % message.identifier)
        except AttributeError:
            message.setMessageLayer(self)
            print 'setting message handler for message %s to %s' % (message.identifier,self)

        result = message.encode()
        self.output.append(result)
        if self.callback:
            for f in self.callback:
                f(result)

    def getHandler(self, identifier, message):
        """Gets the handler for the identifier.
        This function retreives the handler for the identifier  and verifies
        that the chain of messages is upheld.
        Also, if we detect that we have done a Goodbye, the state is changed
        to Hello and we clear self.persistant.
        """
        #print 'addInput.handle()'
        try:
            handler = self.globals.handlers[identifier]
        except KeyError:
            raise MessageError('Unable to find handler "%s"' % identifier)

        # Set the state to Hello if we have done a Goodbye.
        self.__setIfGoodbye(identifier, handler)

        state_in_chain = ((identifier in self.globals.state.suffixes) and
                           self.globals.state.identifier in handler.prefixes)

        state_from_hello = Hello in self.globals.state.suffixes

        state_to_hello = Hello in handler.prefixes

        state_at_hello = state_from_hello and state_to_hello

        if not state_in_chain and not state_at_hello:  
            raise MessageError('Handler "%s" is not valid suffix. Prefix: %s' % 
                                (identifier, self.globals.state.identifier))

        #print 'addInput.handle() handler.new'
        h = handler.new(message, self)
       
        return h

    def __setIfGoodbye(self, identifier, handler):
        """This helper function resets the state to Hello if we have done a Goodbye.
        This function causes __clearPersistant to be called if we are coming from Hello.
        """

        if Hello == self.globals.state:
            return # we are already at Hello

        state_in_chain = ((identifier in self.globals.state.suffixes) and
                           self.globals.state.identifier in handler.prefixes)

        if state_in_chain:
            return # we have a valid chain so not at Goodbye

        state_from_hello = Hello in self.globals.state.suffixes
        state_to_hello = Hello in handler.prefixes

        if state_from_hello and state_to_hello:
            self.__clearPersistant()
            self.globals.lastState = self.globals.state # keep the old state available
            self.globals.state = Hello

       
    def __clearPersistant(self, keep=[]):
        print 'clearing persistant information'
        if keep:
            raise NotImplementedError
        class persistant: pass
        self.persistant = persistant

    def addCallback(self, callback):
        print 'adding a callback'
        if callback not in self.callback:
            self.callback.append(callback)

    def removeCallback(self, callback):
        print 'removing a callback'
        if callback not in self.callback:
            raise MessageError('Callback function not in list of callbacks.')

        self.callback.remove(callback)








class MessageHandler(object):
    def __init__(self, identifier, prefixes, suffixes, grammer, status, func):
        self.identifier = identifier
        self.prefixes = prefixes
        self.suffixes = suffixes
        self.grammer = grammer
        self.sentence = []
        self.handlestatus, self.encodestatus, self.mustalreadyhave = status
        self.func = func
        self.messageLayer = None

    def new(self, message, messageLayer):
        """Make new message and decode grammer."""
        #print 'MessageHandler.new(%s)' % message.name
        handler = MessageHandler(self.identifier, self.prefixes, self.suffixes,
                                 self.grammer,
                                 (  self.handlestatus, self.encodestatus,
                                    self.mustalreadyhave),
                                 self.func)
        handler.messageLayer = messageLayer

        # This is a hack. Why do I need this?
        handler.__class__ = self.__class__

        if not terrible_hack:
            raise MessageError('Unimplemented.')
        else:
            for i in message.sentence:
                handler.sentence.append(i)
        return handler

    def setMessageLayer(self, messageLayer):
        self.messageLayer = messageLayer

    def _setupNext(self):
        self.messageLayer.globals.lastState = self.messageLayer.globals.state
        self.messageLayer.globals.state = self
        #print 'new self.globals.state %s' % self.identifier

    def _setupStatus(self, status):
        """Resets the message layer status and sets the status required."""
        #FIXME: this should only remove things not needed
        self.messageLayer.globals.status.reset()
        self.messageLayer.globals.status.elevate(status)

    def _finally(self, result):
        if self.func:
            self.func(self, result)

    def setCallback(self, func):
        self.func = func

    def handle(self):
        if self.mustalreadyhave:
            test = self.messageLayer.globals.status.has
        else:
            test = self.messageLayer.globals.status.can

        if not test(self.handlestatus):
            raise MessageError("Unable to handle. Requires %s. Do not have/can't get" %
                                self.handlestatus.status)
        
        result = self._handle()
        if result == None: # we require that the result is a message for some logic
            result = self

        if not self.mustalreadyhave:
            self.messageLayer.globals.status.reset()
            self.messageLayer.globals.status.elevate(self.handlestatus)

        self._setupNext()

        self._finally(result)

        return result

    def encode(self):
        if self.mustalreadyhave:
            test = self.messageLayer.globals.status.has
        else:
            test = self.messageLayer.globals.status.can
            
        if not test(self.encodestatus):
            raise MessageError("Unable to handle. Requires %s. DO not have/can't get" %
                                self.handlestatus.status)
        
        result = self._encode()
        if result == None: # we require that the result to be a message for some logic
            result = self

        if not self.mustalreadyhave:
            self.messageLayer.globals.status.reset()
            self.messageLayer.globals.status.elevate(self.encodestatus)

        self._setupNext()

        self._finally(result)

        return result








class BlankPresent(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='BLANK_PRESENT',
                                prefixes=[Hello],
                                suffixes=['BLANK_FAILURE', 'BLANK_REJECT',
                                'BLANK_ACCEPT'], grammer='',
                                status=statusHandleServerSet, func=func)
        
    def _handle(self):
        self.messageLayer.persistant.dsdb_certificate = self.sentence[0]
        self.messageLayer.persistant.blanks = self.sentence[1]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.dsdb_certificate)
        self.sentence.append(self.messageLayer.persistant.blanks)

class BlankReject(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='BLANK_REJECT', 
                                prefixes=['BLANK_PRESENT'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        self.messageLayer.persistant.reason = self.sentence[0]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.reason)

class BlankFailure(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='BLANK_FAILURE',
                                prefixes=['BLANK_PRESENT', 'BLANK_ACCEPT'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        self.messageLayer.persistant.reason = self.sentence[0]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.reason)

class BlankAccept(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='BLANK_ACCEPT', 
                                prefixes=['BLANK_PRESENT'],
                                suffixes=['COINS_REDEEM', 'BLANK_REJECT'], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        pass

    def _encode(self):
        pass

class CoinsRedeem(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='COINS_REDEEM', prefixes=['BLANK_ACCEPT'],
                                suffixes=['COINS_REJECT', 'COINS_ACCEPT'], grammer='',
                                status=statusHandleServer, func=func)

    def _handle(self):
        self.messageLayer.persistant.coins = self.sentence[0]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.coins)

class CoinsReject(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='COINS_REJECT', prefixes=['COINS_REDEEM'],
                                suffixes=['COINS_REDEEM', Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        self.messageLayer.persistant.reason = self.sentence[0]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.reason)

class CoinsAccept(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='COINS_ACCEPT', prefixes=['COINS_REDEEM'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        pass

    def _encode(self):
        pass

class LockCoinsRequest(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='LOCK_COINS_REQUEST', prefixes=[Hello],
                                suffixes=['LOCK_COINS_ACCEPT', 'LOCK_COINS_FAILURE'], 
                                grammer='',
                                status=statusHandleServerSet, func=func)

    def _handle(self):
        self.messageLayer.persistant.key_id = self.sentence[0]
        self.messageLayer.persistant.transaction_id = self.sentence[1]
        self.messageLayer.persistant.blanks = self.sentence[2]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.key_id)
        self.sentence.append(self.messageLayer.persistant.transaction_id)
        self.sentence.append(self.messageLayer.persistant.blanks)

class LockCoinsAccept(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='LOCK_COINS_ACCEPT', 
                                prefixes=['LOCK_COINS_REQUEST'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        if self.messageLayer.persistant.transaction_id != self.sentence[0]:
            raise MessageError('transaction_id changed. Was: %s, Now: %s' %
                               (self.messageLayer.persistant.transaction_id, self.sentence[0]))
        self.messageLayer.persistant.dsdb_lock = self.sentence[1]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.transaction_id)
        self.sentence.append(self.messageLayer.persistant.dsdb_lock)

class LockCoinsFailure(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='LOCK_COINS_FAILURE', 
                                prefixes=['LOCK_COINS_REQUEST'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        if self.messageLayer.persistant.transaction_id != self.sentence[0]:
            raise MessageError('transaction_id changed. Was %s, Now: %s' %
                               (self.messageLayer.persistant.transaction_id, self.sentence[0]))
        self.messageLayer.persistant.reason = self.sentence[1]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.transaction_id)
        self.sentence.append(self.messageLayer.persistant.reason)

class UnlockCoinsRequest(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='UNLOCK_COINS_REQUEST', prefixes=[Hello],
                                suffixes=['UNLOCK_COINS_PASS', 'UNLOCK_COINS_FAILURE'], 
                                grammer='',
                                status=statusHandleServerSet, func=func)

    def _handle(self):
        self.messageLayer.persistant.transaction_id = self.sentence[0]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.transaction_id)

class UnlockCoinsPass(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='UNLOCK_COINS_PASS', 
                                prefixes=['UNLOCK_COINS_REQUEST'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        pass

    def _encode(self):
        pass

class UnlockCoinsFailure(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='UNLCOK_COINS_FAILURE', 
                                prefixes=['UNLOCK_COINS_REQUEST'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        self.messageLayer.persistant.transaction_id = self.sentence[0]
        self.messageLayer.persistant.reason = self.sentence[1]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.transaction_id)
        self.sentence.append(self.messageLayer.persistant.reason)

class MintingKeyFetchDenomination(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='MINTING_KEY_FETCH_DENOMINATION',
                                prefixes=[Hello],
                                suffixes=['MINTING_KEY_PASS', 'MINTING_KEY_FAILURE'], 
                                grammer='',
                                status=statusHandleServerSet, func=func)

    def _handle(self):
        self.messageLayer.persistant.denomination = self.sentence[0]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.denomination)

class MintingKeyFetchKeyID(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='MINTING_KEY_FETCH_KEYID',
                                prefixes=[Hello],
                                suffixes=['MINTING_KEY_PASS', 'MINTING_KEY_FAILURE'], 
                                grammer='',
                                status=statusHandleServerSet, func=func)

    def _handle(self):
        self.messageLayer.persistant.key_id = self.sentence[0]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.key_id)

class MintingKeyPass(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='MINTING_KEY_PASS',
                                prefixes=['MINTING_KEY_FETCH_DENOMINATION', 
                                            'MINTING_KEY_FETCH_KEYID'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        self.messageLayer.persistant.minting_certificate = self.sentence[0]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.minting_certificate)

class MintingKeyFailure(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='MINTING_KEY_FAILURE',
                                prefixes=['MINTING_KEY_FETCH_DENOMINATION', 
                                            'MINTING_KEY_FETCH_KEYID'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        self.messageLayer.persistant.reason = self.sentence[0]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.reason)

class MintRequest(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='MINT_REQUEST', prefixes=[Hello],
                                suffixes=['MINT_REJECT', 'MINT_ACCEPT'], grammer='',
                                status=statusHandleServerSet, func=func)

    def _handle(self):
        self.messageLayer.persistant.request_id = self.sentence[0]
        self.messageLayer.persistant.blinds = self.sentence[1]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.request_id)
        self.sentence.append(self.messageLayer.persistant.blinds)

class MintReject(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='MINT_REJECT', prefixes=['MINT_REQUEST'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)
        
    def _handle(self):
        self.messageLayer.persistant.reason = self.sentence[0]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.reason)

class MintAccept(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='MINT_ACCEPT', prefixes=['MINT_REQUEST'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        if self.messageLayer.persistant.request_id != self.sentence[0]:
            raise MessageError('request_id changed. Was %s, Now: %s' %
                               (self.messageLayer.persistant.request_id, self.sentence[0]))

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.request_id)

class FetchMintedRequest(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='FETCH_MINTED_REQUEST', prefixes=[Hello],
                                suffixes=['FETCH_MINTED_FAILURE', 'FETCH_MINTED_WAIT', 
                                            'FETCH_MINTED_ACCEPT'],
                                grammer='',
                                status=statusHandleServerSet, func=func)

    def _handle(self):
        self.messageLayer.persistant.request_id = self.sentence[0]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.request_id)

class FetchMintedFailure(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='FETCH_MINTED_FAILURE', 
                                prefixes=['FETCH_MINTED_REQUEST'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        if self.messageLayer.persistant.request_id != self.sentence[0]:
            raise MessageError('transaction_id changed. Was %s, Now: %s' %
                               (self.messageLayer.persistant.transaction_id, self.sentence[0]))
        self.messageLayer.persistant.reason = self.sentence[1]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.request_id)
        self.sentence.append(self.messageLayer.persistant.reason)

class FetchMintedWait(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='FETCH_MINTED_WAIT', 
                                prefixes=['FETCH_MINTED_REQUEST'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        if self.messageLayer.persistant.request_id != self.sentence[0]:
            raise MessageError('request_id changed. Was %s, Now: %s' %
                               (self.messageLayer.persistant.request_id, self.sentence[0]))
        self.messageLayer.persistant.reason = self.sentence[1]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.request_id)
        self.sentence.append(self.messageLayer.persistant.reason)

class FetchMintedAccept(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='FETCH_MINTED_ACCEPT', 
                                prefixes=['FETCH_MINTED_REQUEST'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        if self.messageLayer.persistant.request_id != self.sentence[0]:
            raise MessageError('request_id changed. Was %s, Now: %s' %
                               (self.messageLayer.persistant.request_id, self.sentence[0]))
        self.messageLayer.persistant.signatures = self.sentence[1]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.request_id)
        self.sentence.append(self.messageLayer.persistant.signatures)

class DSDBKeyRequest(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='DSDB_KEY_REQUEST', prefixes=[Hello],
                                suffixes=['DSDB_KEY_PASS'], grammer='',
                                status=statusHandleServerSet, func=func)

    def _handle(self):
        pass

    def _encode(self):
        pass

class DSDBKeyPass(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='DSDB_KEY_PASS', 
                                prefixes=['DSDB_KEY_REQUEST'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        self.messageLayer.persistant.dsdb_certificate = self.sentence[0]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.dsdb_certificate)

class RedeemCoinsRequest(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='REDEEM_COINS_REQUEST', prefixes=[Hello],
                                suffixes=['REDEEM_COINS_ACCEPT', 'REDEEM_COINS_REJECT'], 
                                grammer='',
                                status=statusHandleServerSet, func=func)

    def _handle(self):
        self.messageLayer.persistant.transaction_id = self.sentence[0]
        self.messageLayer.persistant.target = self.sentence[1]
        self.messageLayer.persistant.coins = self.sentence[2]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.transaction_id)
        self.sentence.append(self.messageLayer.persistant.target)
        self.sentence.append(self.messageLayer.persistant.coins)

class RedeemCoinsAccept(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='REDEEM_COINS_ACCEPT', 
                                prefixes=['REDEEM_COINS_REQUEST'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        pass

    def _encode(self):
        pass

class RedeemCoinsReject(MessageHandler):
    def __init__(self, func=None):
        MessageHandler.__init__(self, identifier='REDEEM_COINS_REJECT',
                                prefixes=['REDEEM_COINS_REQUEST'],
                                suffixes=[Goodbye], grammer='',
                                status=statusHandleClient, func=func)

    def _handle(self):
        self.messageLayer.persistant.reason = self.sentence[0]

    def _encode(self):
        self.sentence.append(self.messageLayer.persistant.reason)
        
class HelloGoodbye(object):
    def __init__(self, identifier):
        self.identifier = identifier
        self.suffixes = [self]
        self.prefixes = [self]

Hello = Goodbye = HelloGoodbye('Hello')

del HelloGoodbye

class MessageError(Exception): pass    

class MessageStatus(object):
    pass

class MessageStatusBase(MessageStatus):
    def __init__(self, basestatus, status=[]):
        """basestatus is a tuple of statuses that are supported."""
        self.status = status
        self.basestatus = basestatus

    def elevate(self, status):
        """Adds a privilege to a base class.
        If we already have the privilege, nothing is done
        If we can not, MessagError is raised.
        """
        if status in self.basestatus:
            if status not in self.status:
                self.status.append(status)
        else:
            raise MessageError('Unable to elevate to "%s"' % status.status)

    def restrict(self, status):
        if status in self.status:
            self.status.remove(status)
        else:
            raise MessageError('Unable to restrict from %s"' % status.status)

    def reset(self):
        """Removes all privileges."""
        self.status = []

    def can(self, status):
        """Returns if a base class can elevate to a privilege."""
        return status in self.basestatus

    def has(self, status):
        """Returns if a base class is elevated to a privilege."""
        return status in self.status
        
class MessageStatusPrivilege(MessageStatus):
    def __init__(self, status):
        self.status = status
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.status == other.status
        return NotImplemented

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result


class MessageStatusesClass(object):
    PrivilegeClient = MessageStatusPrivilege('Client')
    PrivilegeServer = MessageStatusPrivilege('Server')
    def getBaseClient(self):
        return MessageStatusBase([MessageStatusesClass.PrivilegeClient])
    def getBaseServer(self):
        return MessageStatusBase([MessageStatusesClass.PrivilegeServer])
    def getBaseNode(self):
        return MessageStatusBase([MessageStatusesClass.PrivilegeClient, 
                                  MessageStatusesClass.PrivilegeServer])
   
MessageStatuses = MessageStatusesClass()


statusHandleClient = (MessageStatuses.PrivilegeClient,
                      MessageStatuses.PrivilegeServer, True)

statusHandleServer = (MessageStatuses.PrivilegeServer,
                      MessageStatuses.PrivilegeClient, True)

statusHandleServerSet = (MessageStatuses.PrivilegeServer,
                         MessageStatuses.PrivilegeClient, False)



   
