from message import BlankPresent
from message import BlankReject
from message import BlankFailure
from message import BlankAccept
from message import CoinsRedeem
from message import CoinsReject
from message import CoinsAccept
from message import MintingKeyFetchKeyID
from message import MintingKeyFetchDenomination
from message import MintingKeyPass
from message import MintingKeyFailure
from message import MintRequest
from message import MintReject
from message import MintAccept
from message import FetchMintedRequest
from message import FetchMintedFailure
from message import FetchMintedWait
from message import FetchMintedAccept
from message import LockCoinsRequest
from message import LockCoinsAccept
from message import LockCoinsFailure
from message import UnlockCoinsRequest
from message import UnlockCoinsPass
from message import UnlockCoinsFailure
from message import RedeemCoinsRequest
from message import RedeemCoinsReject
from message import RedeemCoinsAccept

from message import MessageType
from message import MessageStatuses
from message import MessageError
from message import Hello as MessageHello

import containers
from crypto import CryptoError

class MerchantWalletManager(object):
    def __init__(self, walletMessageType, entity):
        
        # isMessageType, dsdbMessageType, amount):
        self.walletMessageType = walletMessageType
        self.entity = entity

        #self.isMessageType = isMessageType
        #self.dsdbMessageType = dsdbMessageType
        if not self.walletMessageType.globals.status.can(MessageStatuses.PrivilegeServer):
            raise MessageError('given messageType does not have PrivilegeServer')

        class messages: pass
        self.walletMessages = messages()
        self.isMessages = messages()
        self.dsdbMessages = messages()
        del messages

        # All the responses we can get from the IS (we are client)
        #self.isMessages.MKP = MintingKeyPass(self.resumeConversation) # this are being handled elsewhere (BlankAndMintingKey)
        #self.isMessages.MKF = MintingKeyFailure(self.resumeConversation) # this is being handled elsewhere (BlankAndMintingKey)
        self.isMessages.MA = MintAccept(self.resumeConversation)
        self.isMessages.MR = MintReject(self.resumeConversation)
        self.isMessages.FMF = FetchMintedFailure(self.resumeConversation)
        self.isMessages.FMW = FetchMintedWait(self.resumeConversation)
        self.isMessages.FMA = FetchMintedAccept(self.resumeConversation)
        self.isMessages.RCR = RedeemCoinsReject(self.resumeConversation)
        self.isMessages.RCA = RedeemCoinsAccept(self.resumeConversation)

        # All messages can get from the other wallet (we are server)
        self.walletMessages.CR = CoinsRedeem(self.resumeConversation)
        self.walletMessages.BP = BlankPresent(self.resumeConversation)
        
        # All the responses we can get from the DSDB
        self.dsdbMessages.LCA = LockCoinsAccept(self.resumeConversation)
        self.dsdbMessages.LCF = LockCoinsFailure(self.resumeConversation)
        self.dsdbMessages.UCP = UnlockCoinsPass(self.resumeConversation)
        self.dsdbMessages.UCF = UnlockCoinsFailure(self.resumeConversation)

        # Add handlers for all the messages using walletMessages if starts conversation
        self.walletMessageType.addMessageHandler(self.walletMessages.BP)
        self.walletMessageType.addMessageHandler(BlankReject())
        self.walletMessageType.addMessageHandler(BlankFailure())
        self.walletMessageType.addMessageHandler(BlankAccept())
        self.walletMessageType.addMessageHandler(self.walletMessages.CR)
        self.walletMessageType.addMessageHandler(CoinsReject())
        self.walletMessageType.addMessageHandler(CoinsAccept())

        class state:
            __slots__ = ('blanks', # the blanks given in BlankPresent
                         'dsdb_certificate', # the dsdb certificate given in BlankPresent
                         'mintBlanks', # blanks we created for use with a MintRequest (to make new coins)
                         'dsdb_lock', # the lock we receive when we perform a LockRequest
                         'coins', # the coins received from the other wallet with a CoinsRedeem
                         'mintingKeysKeyID', # the minting key certificates for all coins received
                         'mintingKeysDenomination', # the minting key certificates for all denominations of all coins received
                         'mintRequestID', # the request id generated for the MintRequest
                         'target', # the target for the MintRequest
                         'signatures', # the signatures returned from IS via FetchMintedRequest
                         'newCoins', # our newly minted coins after
                         'mintingFailures' # any coins where the signature was invalid. Nothing we can really do with this though.
                         )
        self.persistant = state()
        del state

        self.lastMessageIdentifier = None


    # an explaination of how this class treats the exchange. We first wait for a BlankPresent from the wallet. We look at the issuer and 
    # let the client decide if he wants to accept.
    # if he does, we make matching blanks and depending on the issuer, MintRequest now (may do after RedeemCoins.
    # we verify the blanks against the DSDB and then BlankAccept. We get the CoinsRedeem, test them, then CoinsAccept.
    # now we RedeemCoinsRequest, and potentially MintRequest at this point. Finally, we FetchMintedRequest to get the new coins. Done. Whew!

    # More information. If isRequiresMRbeforeRCR is true, the chain when the wallet accepts the coins goes:
    #   MINT_REQUEST -> (MINT_ACCEPT) -> REDEEM_COINS_REQUEST -> (REDEEM_COINS_ACCEPT) -> FETCH_MINTED_REQUEST -> (FETCH_MINTED_ACCEPT)
    # If isRequiresMRbeforeRCR is false, the chain when the wallet sends the COINS_REQUEST goes:
    #   REDEEM_COINS_REQUEST -> (REDEEM_COINS_ACCEPT) -> MINT_REQUEST -> (MINT_ACCEPT) -> FETCH_MINTED_REQUEST -> (FETCH_MINTED_ACCEPT

    
    def resumeConversation(self, message, result):
        if isinstance(message, BlankPresent):
            self.setHandler(BlankAndMintingKey(self, message)) # First we receive the blanks
        elif isinstance(message, MintAccept) or isinstance(message, MintReject):
            self.setHandler(Mint(self, message)) # Then we (may) try to mint our own blanks
        elif isinstance(message, LockCoinsFailure) or isinstance(message, LockCoinsAccept):
            self.setHandler(LockCoins(self, message)) # We also have to try to lock the coins...
        elif isinstance(message, CoinsRedeem):
            self.setHandler(Coins(self, message)) # We locked the coins, and they are valid. We sent a BlankAccept. Next we get told to redeem them
        elif isinstance(message, RedeemCoinsReject) or isinstance(message, RedeemCoinsAccept):
            self.setHandler(RedeemCoins(self, message)) # Now we redeem them (note: the next step may be to try to mint them...)
        elif isinstance(message, FetchMintedWait) or isinstance(message, FetchMintedFailure) or isinstance(message, FetchMintedAccept):
            self.setHandler(FetchMinted(self, message)) # And finally, get the coins.
        elif isinstance(message, UnlockCoinsPass) or isinstance(message, UnlockCoinsFailure):
            self.setHandler(UnlockCoins(self, message)) # If we erred, we unlock to be nice
        else:
            raise MessageError('Message %s does not continue a conversation' % message.identifier)

    def setHandler(self, handler):
        self.handler = handler

    def connectToDSDB(self, dsdb_certificate):
        """sets up the dsdbMessageType and links the callbacks."""
        client = MessageStatuses.getBaseClient()
        self.dsdbMessageType = MessageType(client)

        # Add handlers for all the messages using dsdbMessages if it continues conversation
        self.dsdbMessageType.addMessageHandler(LockCoinsRequest())
        self.dsdbMessageType.addMessageHandler(self.dsdbMessages.LCF)
        self.dsdbMessageType.addMessageHandler(self.dsdbMessages.LCA)
        self.dsdbMessageType.addMessageHandler(UnlockCoinsRequest())
        self.dsdbMessageType.addMessageHandler(self.dsdbMessages.UCF)
        self.dsdbMessageType.addMessageHandler(self.dsdbMessages.UCP)        

        self.entity.connectToDSDB(self.dsdbMessageType, dsdb_certificate)

    def connectToIS(self, currency_description_document):
        """sets up the isMessageType and links the callbacks."""
        client = MessageStatuses.getBaseClient()
        self.isMessageType = MessageType(client)

        # Add handlers for all the messages using isMessages if it continues the conversation
        self.isMessageType.addMessageHandler(MintingKeyFetchKeyID())
        self.isMessageType.addMessageHandler(MintingKeyFetchDenomination())
        #self.isMessageType.addMessageHandler(self.isMessages.MKP)
        #self.isMessageType.addMessageHandler(self.isMessages.MKF)
        self.isMessageType.addMessageHandler(MintingKeyPass()) # These normally would continue, but are folded into BlankAndMintingKey
        self.isMessageType.addMessageHandler(MintingKeyFailure()) # These normally would continue, but are folded into BlankAndMintingKey
        self.isMessageType.addMessageHandler(MintRequest())
        self.isMessageType.addMessageHandler(self.isMessages.MA)
        self.isMessageType.addMessageHandler(self.isMessages.MR)
        self.isMessageType.addMessageHandler(FetchMintedRequest())
        self.isMessageType.addMessageHandler(self.isMessages.FMF)
        self.isMessageType.addMessageHandler(self.isMessages.FMW)
        self.isMessageType.addMessageHandler(self.isMessages.FMA)
        self.isMessageType.addMessageHandler(RedeemCoinsRequest())
        self.isMessageType.addMessageHandler(self.isMessages.RCR)
        self.isMessageType.addMessageHandler(self.isMessages.RCA)
    
        self.entity.connectToIS(self.isMessageType, currency_description_document)

    def success(self, message, handler):
        print 'Received a success! Message class: %s. Handler class: %s' % (message.__class__, handler.__class__)

    def failure(self, message, handler):
        print 'Receive a failure. :( Message %s Sentence: %s' % (message.identifier, message.sentence)
        print 'We should do something like un-hook ourselves or something.'

    def waitForFetchMint(self, message, handler):
        print 'We were told to wait on our FetchMintedRequest. Reason: %s' % message.messageLayer.globals.reason


class Handler(object):
    def _createAndOutput(self, message, messageType):
        m = message()
        messageType.addOutput(m)

    def _createAndOutputIS(self, message):
        self._createAndOutput(message, self.manager.isMessageType)
    
    def _createAndOutputWallet(self, message):
        self._createAndOutput(message, self.manager.walletMessageType)
        
    def _createAndOutputDSDB(self, message):
        self._createAndOutput(message, self.manager.dsdbMessageType)

    def _setLastState(self, state):
        print 'setting last state: %s' % state
        self.manager.lastMessageIdentifier = state

    def _verifyLastState(self, state):
        """_verifyLastState is used to make sure that we are progressing properly through messages which can start at Hello.
        For any message which can start at Hello, perform a check to make sure that we have the required lastState in the manager.
        A lastState of None is the beginning.
        """
        return #FIXME: lastState isn't being set due to function calls. Figure this out later. (Note: not having this breaks verification)
        if not self.manager.lastMessageIdentifier in state:
            raise MessageError('Did not find expected last state. Found: %s, Wanted: %s' % (self.manager.lastMessageIdentifier, state))


class BlankAndMintingKey(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.walletMessageType.addCallback(self.handle)
        # do this later self.manager.isMessageType.addCallback(self.handle)
        self.mintingKeysDenomination = {}
        self.mintingKeysKeyID = {}
        self.mkfReturn = None

    def handle(self, message):
        if not isinstance(message, BlankPresent) and not isinstance(message, MintingKeyFetchDenomination) and not \
                isinstance(message, MintingKeyFailure) and not isinstance(message, MintingKeyPass) and not isinstance(message, MintingKeyFetchKeyID):
            if message.messageLayer.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('BlankAndMintingKey should have already been removed. It was not. Very odd. Message: %s LastWalletMessage: %s LastISMessage: %s' 
                        % (message.identifier, self.manager.walletMessageType.globals.lastState, self.manager.isMessageType.globals.lastState))
            else:
                raise MessageError('We somehow called BlankAndMintingKey.handle() but cannot be there. Message: %s' % message.identifier)

        if isinstance(message, BlankPresent):
            self._verifyLastState([None])

            self.dsdb_certificate = self.manager.walletMessageType.persistant.dsdb_certificate
            self.blanks = self.manager.walletMessageType.persistant.blanks
            
            self.manager.persistant.blanks = self.blanks
            self.manager.persistant.dsdb_certificate = self.dsdb_certificate

            # connect to IS
            # FIXME: Gah. What a hack. Only supports one IS
            result = self.getCDD(self.manager.entity.cdds, self.blanks)
            if result != 'Unknown issuer':
                self.manager.connectToIS(result)

                # add the required callback
                self.manager.isMessageType.addCallback(self.handle)

                # connect to dsdb
                self.manager.connectToDSDB(self.manager.persistant.dsdb_certificate)

                # self.performMagic is a special function doing anything we want.
                self.performMagic(self.blanks, self.dsdb_certificate)
            else:
                self.manager.walletMessageType.persistant.reason = result
                self._createAndOutputWallet(BlankReject)
                
        
        elif isinstance(message, MintingKeyPass): # we've received a key
            minting_certificate = self.manager.isMessageType.persistant.minting_certificate
            print 'received minting_certificate: %s' % str(minting_certificate)
            self.mkfType[self.mkfSearch] = minting_certificate

            self.mkfReturn()

        elif isinstance(message, MintingKeyFailure):        
            self.reason = message.messageLayer.persistant.reason
            self.manager.failure(message, self)

        elif isinstance(message, MintingKeyFetchKeyID) or isinstance(message, MintingKeyFetchDenomination):
            self._verifyLastState(['BlankAndMintingKey']) # make sure we started in here
            # but we did send these messages, so do nothing else
            
        self._setLastState('BlankAndMintingKey') # There are many different ways to exit this. Just cover them all.

    def listUnknownKeysKeyID(self, blanks, entity):
        """Returns a list of all the KeyIDs we need to request."""
        needed = []
        for b in blanks:
            if b.key_identifier not in needed:
                needed.append(b.key_identifier)

        dontHave = []
        for key_id in needed:
            if key_id not in entity.minting_keys_key_id:
                dontHave.append(key_id)

        return dontHave
        
    def listUnknownKeysDenomination(self, blanks, entity):
        """Returns a list of all the Denominations we need to request."""
        denominations = []
        for b in blanks:
            if b.denomination not in denominations:
                denominations.append(b.denomination)

        return denominations
        
    def removeKnownKeysDenomination(self, blanks, entity):
        raise NotImplementedError
    
    def performMagic(self, blanks, dsdb_certificate):
        self.neededKeyIDs = self.listUnknownKeysKeyID(blanks, self.manager.entity)
        self.neededDenominations = self.listUnknownKeysDenomination(blanks, self.manager.entity)

        self.getMintingKeyAndContinue()

    def getMintingKeyAndContinue(self):
        if len(self.neededKeyIDs) > 0:  # Get a key_id
            self.mkfType = self.mintingKeysKeyID
            self.mkfSearch = self.neededKeyIDs.pop()
            self.mkfReturn = self.getMintingKeyAndContinue

            self.manager.isMessageType.persistant.key_id = self.mkfSearch
            self._createAndOutputIS(MintingKeyFetchKeyID)

        elif len(self.neededDenominations) > 0: #get a denomination
            self.mkfType = self.mintingKeysDenomination
            self.mkfSearch = self.neededDenominations.pop()
            self.mkfReturn = self.getMintingKeyAndContinue

            self.manager.isMessageType.persistant.denomination = self.mkfSearch
            self._createAndOutputIS(MintingKeyFetchDenomination)
        
        else: # We have all the keys we need. Make new blanks. Verify blanks against DSDB (For now, we don't support trying to do a MintRequest right now
            # Add all the keys to the entity
            self.manager.entity.addMintingKeys(self.collapseMintingKeys(self.mintingKeysKeyID, self.mintingKeysDenomination))
                    
            # Make blanks
            self.manager.persistant.mintBlanks = self.makeBlanks(self.blanks, self.manager.entity.cdds, self.mintingKeysDenomination)
            self.manager.persistant.mintingKeysDenomination = self.mintingKeysDenomination
            self.manager.persistant.mintingKeysKeyID = self.mintingKeysKeyID

            #Verify blanks
            type, result = self.checkValidObfuscatedBlanksAndKnownIssuers(self.blanks, self.manager.entity.cdds, self.manager.entity.minting_keys_key_id)
            if type == 'PASS': 
                # setup the requirements for the LockCoinsRequest
                self.manager.dsdbMessageType.persistant.key_id = self.dsdb_certificate.key_identifier
                self.manager.dsdbMessageType.persistant.transaction_id = self.makeTransactionID()

                # the message to the dsdb, LOCK_COINS_REQUEST only gets sent the obfuscated serial and the minting_key. Get that information
                self.lockRequestBlanks = []
                for b in self.blanks:
                    self.lockRequestBlanks.append((b.key_identifier, b.serial))
                self.manager.dsdbMessageType.persistant.blanks = self.lockRequestBlanks

                # setup future minting
                self.manager.isMessageType.persistant.transaction_id = self.manager.dsdbMessageType.persistant.transaction_id # it's the same id for a different thing
                self.manager.isMessageType.persistant.blanks = self.manager.persistant.mintBlanks
        
                # The result will be handled by a different Handler. Remove ourselves as a callback
                self.manager.walletMessageType.removeCallback(self.handle)
                self.manager.isMessageType.removeCallback(self.handle)

                # And finally output
                self._createAndOutputDSDB(LockCoinsRequest)
            elif type == 'FAILED': # Send a BlankReject
                self.manager.walletMessageType.persistant.reason = result
                self._createAndOutputWallet(BlankReject)
            else:
                raise MessageError('Received an impossible type: %s' % type)

    def makeBlanks(self, blanks, cdds, mintingKeys):
        """I have no idea why we take the inputs we do. It looks like it makes new CurrencyBlanks. Why do we input the blanks? 
        it makes no sense. We do need the cdd though, I think.
        """
        # Okay. This is how this function is going to work. It goes through and sees if the values of coins is the same as the
        # blanks. If it is... Fuck. That doesn't work. Okay... just making copies of coins for now.

        newBlanks = []

        for b in blanks:
            # FIXME: This will break if the old key cannot be used to mint.
            newBlank = containers.CurrencyBlank(b.standard_identifier, b.currency_identifier, b.denomination, mintingKeys[b.denomination].key_identifier)
            newBlank.generateSerial()
            newBlanks.append(newBlank)

        return newBlanks
            
    def makeTransactionID(self):
        import crypto
        return crypto._r.getRandomNumber(128)
        
    def checkValidObfuscatedBlanksAndKnownIssuers(self, blanks, cdds, mintingKeysKeyID):
        failure = False
        failures = []

        if len(blanks) == 0:
            raise MessageError('Need atleast one blank!')

        for b in blanks:
            if not self.checkValidObfuscatedBlank(b, cdds, mintingKeysKeyID):
                failure = True
                failures.append( (b, 'Malformed blank') )
            elif not self.checkKnownIssuer(b, self.manager.entity.cdds):
                failure = True
                failures.append( (b, 'Unknown issuer') )

        if failure:
            return 'FAILED', failures
        else:
            return 'PASS', None

    def checkValidObfuscatedBlank(self, blank, cdds, mintingKeysKeyID):
        return blank.validate_with_CDD_and_MintingKey(cdds[blank.currency_identifier],
                                                      mintingKeysKeyID[blank.key_identifier])

    def checkKnownIssuer(self, blank, cdds):
        found = blank.currency_identifier in cdds

        if not found:
            return false

        return self.checkWantIssuer(cdds[blank.currency_identifier])

    def checkWantIssuer(self, cdd):
        """checkWantIssuer checks a known issuer to see if we want to agree to use them. It may ask the user themselves
        or check against a list of always trusted issuers to give an affermative.
        """

        # FIXME: this should be somehow superceded by the client
        return True
        
    
    def getCDD(self, cdds, blanks):
        """Returns the CDD for the blanks. Assumes only one CDD (Raise MessageError if multiple)."""
        try:
            currency_identifier = blanks[0].currency_identifier
        except IndexError:
            raise MessageError('No blanks')

        #FIXME: somehow allow multiple cdds?
        for b in blanks:
            if currency_identifier != b.currency_identifier:
                raise MessageError('This client is too stupid to deal with more than one currency.')

        if not cdds.has_key(currency_identifier):
            return 'Unknown issuer'
        else:
            return cdds[currency_identifier]
    
    def collapseMintingKeys(self, mk_keyid, mk_denomination):
        """This takes mk_keyid and mk_denomination and makes a list of each of them once."""
        result = []
        for key in mk_keyid.values():
            if key not in result:
                result.append(key)
        for key in mk_denomination.values():
            if key not in result:
                result.append(key)

        return result
        
class LockCoins(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.dsdbMessageType.addCallback(self.handle)

    def handle(self, message):
        if not isinstance(message, LockCoinsRequest) and not isinstance(message, LockCoinsAccept) and not isinstance(message, LockCoinsFailure):
            if message.messageLayer.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('LockCoins should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                message.messageLayer.globals.lastState))
            else:
                raise MessageError('We somehow called LockCoins.handle() but cannot be there. Message: %s' % message.identifier)


        self._verifyLastState(['BlankAndMintingKey', 'LOCK_COINS_REQUEST'])

        if isinstance(message, LockCoinsRequest):
            # we output this. Previous step was in BlankAndMintingKey
            print 'Got a LockCoinsRequest. I did not know we got these.'

        elif isinstance(message, LockCoinsAccept):
            self.dsdb_lock = self.manager.dsdbMessageType.persistant.dsdb_lock
            self.manager.persistant.dsdb_lock = self.dsdb_lock

            if not self.validDSDBLock(self.dsdb_lock, self.timeNow()):
                raise MessageError('Invalid DSDB Lock')
            
            self.manager.dsdbMessageType.removeCallback(self.handle) #remove the callback to the DSDB. Not coming here again

            self._createAndOutputWallet(BlankAccept)

        elif isinstance(message, LockCoinsFailure):
            self.reason = self.manager.dsdbMessageType.persistant.reason
            # undo the damage and tell someone
            self.manager.failure(message, self)

        self._setLastState(message.identifier)

    def validDSDBLock(self, dsdb_lock, now):
        """validDSDBLock returns whether dsdb_lock is still valid or not.
        dsdb_lock is really just a time, so we test if we are before the time or not.
        """

        return now < dsdb_lock
    
    def timeNow(self):
        import time
        return time.time()

class Coins(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.walletMessageType.addCallback(self.handle)

        #FIXME: this is a hack
        self.isRequiresMRbeforeRCR = True # set a value for if the issuer supports (or requires) mint requests prior to redeem coin requests

    def handle(self, message):
        if not isinstance(message, CoinsRedeem) and not isinstance(message, CoinsAccept) and not isinstance(message, CoinsReject):
            if message.messageLayer.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('Coins should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                message.messageLayer.globals.lastState))
            else:
                raise MessageError('We somehow called Coins.handle() but cannot be there. Message: %s' % message.identifier)


        if isinstance(message, CoinsRedeem):
            self.coins = self.manager.walletMessageType.persistant.coins
            self.manager.persistant.coins = self.coins

            type, result = self.verifyCoins(self.coins, self.manager.entity.minting_keys_key_id, self.manager.persistant.blanks,
                                            self.manager.persistant.dsdb_certificate, self.manager.entity.cdds)

            if type == 'ACCEPT':
                self.dsdb_lock = self.manager.persistant.dsdb_lock
                if not self.validDSDBLock(self.dsdb_lock, self.timeNow()):
                    raise MessageError('Invalid DSDB lock. You are an idiot for letting this happen.')

                self._createAndOutputWallet(CoinsAccept)

            elif type == 'REJECT':
                self.manager.walletMessageType.persistant.reason = result

                self._createAndOutputWallet(CoinsReject)

            else:
                raise MessageError('Went to an impossible type: %s' % type)

        elif isinstance(message, CoinsReject):
            # We are done. We should be nice though and Unlock the coins
            if self.validDSDBLock(self.manager.dsdbMessageType.persistant.dsdb_lock, self.timeNow()):

                # FIXME: The else below removes two callbacks. Which one of them is wrong?
                self.manager.walletMessageType.removeCallback(self.handle)
                self._createAndOutputDSDB(UnlockCoinsRequest)
            else: # the DSDB lock has already expired.
                self.manager.walletMessageType.removeCallback(self.handle)
                self.manager.isMessageType.removeCallback(self.handle)
                self.manager.failure(self, message)
        
        elif isinstance(message, CoinsAccept):
            self.manager.walletMessageType.removeCallback(self.handle)

            #figure out what request ID we will be using
            self.manager.persistant.mintRequestID = self.newRequestID()
            self.manager.persistant.target = self.newTarget()

            if self.isRequiresMRbeforeRCR:
                self.manager.isMessageType.persistant.request_id = self.manager.persistant.mintRequestID

                # setup blinds only for the MintRequest message
                blinds = []
                for b in self.manager.persistant.mintBlanks:
                    b.blind_blank(self.manager.entity.cdds, self.manager.entity.minting_keys_key_id) # XXX should this be in makeBlanks() instead?
                    blinds.append((b.key_identifier, b.blind_value))
                self.manager.isMessageType.persistant.blinds = blinds

                #self.manager.walletMessageType.removeCallback(self.handle)
                self._createAndOutputIS(MintRequest)

            else:
                self.manager.isMessageType.persistant.trasaction_id = self.dsdb_lock #this is probably the wrong one! look it up
                raise MessageError('look at comment above')
                self.manager.isMessageType.persistant.target = self.manager.persistant.target
                self.manager.isMessageType.persistant.coins = self.manager.persistant.coins

                #self.manager.isMessageType.removeCallback(self.handle)
                self._createAndOutput(RedeemCoinsRequest)
                
        self._setLastState(message.identifier)

    def validDSDBLock(self, dsdb_lock, now):
        """validDSDBLock returns whether dsdb_lock is still valid or not.
        dsdb_lock is really just a time, so we test if we are before the time or not.
        """

        return now < dsdb_lock

    def newRequestID(self):
        import crypto
        return crypto._r.getRandomNumber(128)

    def newTarget(self):
        # FIXME: This should be more involved and defined somewhere. Just use a number for now
        import crypto
        return crypto._r.getRandomNumber(128)

    def verifyCoins(self, coins, mintingKeys, blanks, dsdb_keycertificate, cdds):
        failure = False
        failures = []

        if len(coins) != len(blanks):
            raise MessageError('Different amounts of coins and blanks')

        if len(coins) == 0:
            raise MessageError('Need atleast one coin')
            # this *should* be impossible due to the previus error.

        for i in range(len(coins)):
            type, result = self.verifySingleCoin(coins[i], mintingKeys, blanks[i], dsdb_keycertificate, cdds)
            if type == 'VALID':
                pass
            elif type == 'FAILURE':
                failure = True
                failures.append( (coins[i], result) )
            else:
                raise MessageError('Got an imposisble type: %s' % type)

        if failure:
            return 'REJECT', failures
        else:
            return 'ACCEPT', None

    def verifySingleCoin(self, coin, mintingKeys, blank, dsdb_keycertificate, cdds):
        """verifySingleCoin takes a coin and ensures the coin is valid and the coin and the obfuscated blank are the same."""
        # First check the coin values against the blank values.
        # Then check the obfuscated serial against the serial
        # If those both pass, verify the coin itself.
        # This ordering attempts to reduce the chances of exception raising

        if not coin.check_similar_to_obfuscated_blank(blank):
            return 'FAILURE', 'Unknown coin'

        if not coin.check_obfuscated_blank_serial(blank, dsdb_keycertificate):
            return 'FAILURE', 'Unknown coin'

        if not coin.validate_with_CDD_and_MintingKey(cdds[coin.currency_identifier], mintingKeys[coin.key_identifier]):
            return 'FAILURE', 'Invalid coin'

        return 'VALID', None
        
    def timeNow(self):
        import time
        return time.time()

class Mint(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.isMessageType.addCallback(self.handle)

        #FIXME: this is a hack
        self.isRequiresMRbeforeRCR = True # set a value for if the issuer supports (or requires) mint requests prior to redeem coin requests

    def handle(self, message):
        if not isinstance(message, MintRequest) and not isinstance(message, MintAccept) and not isinstance(message, MintReject):
            if message.messageLayer.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('Mint should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                message.messageLayer.globals.lastState))
            else:
                raise MessageError('We somehow called Mint.handle() but cannot be there. Message: %s' % message.identifier)


        self._verifyLastState(['']) # I have no idea what will actually be here, nor to I care right now. This will show us.

        if isinstance(message, MintRequest):
            # we output this. Previous step was in ?????
            print 'Got a MintRequest. I did not know we got these.'

        elif isinstance(message, MintAccept):
            if self.manager.persistant.mintRequestID != self.manager.isMessageType.persistant.request_id:
                raise MessageError('request_id changed. Was: %s Now %s' % (self.manager.persistant.mintingRequestID, self.manager.isMessageType.persistant.request_id))
                        
            self.manager.isMessageType.removeCallback(self.handle) #remove the callback. Not coming here again

            if self.isRequiresMRbeforeRCR:
                # We've already done the MintRequest. Nothing stopping us from trying to Redeem now.
                self.manager.isMessageType.persistant.trasaction_id = self.manager.persistant.mintRequestID 
                self.manager.isMessageType.persistant.target = self.manager.persistant.target
                self.manager.isMessageType.persistant.coins = self.manager.persistant.coins

                #FIXME: why isn't the callback registered?
                #self.manager.isMessageType.removeCallback(self.handle)
                self._createAndOutputIS(RedeemCoinsRequest)
            else:
                # We already did the RedeemRequest. Time to fetch
                self.manager.isMessageType.persistant.request_id = self.manager.persistant.mintRequestID

                self.manager.isMessageType.removeCallback(self.handle)
                self._createAndOutputIS(FetchMintedRequest)
            
        elif isinstance(message, MintReject):
            self.reason = self.manager.isMessageType.persistant.reason

            self.manager.isMessageType.removeCallback(self.handle)
            
            # undo the damage and tell someone
            self.manager.failure(message, self)

        self._setLastState(message.identifier)


class RedeemCoins(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.isMessageType.addCallback(self.handle)

        #FIXME: this is a hack
        self.isRequiresMRbeforeRCR = True # set a value for if the issuer supports (or requires) mint requests prior to redeem coin requests

    def handle(self, message):
        if not isinstance(message, RedeemCoinsRequest) and not isinstance(message, RedeemCoinsAccept) and not isinstance(message, RedeemCoinsReject):
            if message.messageLayer.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('RedeemCoins should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                message.messageLayer.globals.lastState))
            else:
                raise MessageError('We somehow called RedeemCoins.handle() but cannot be there. Message: %s' % message.identifier)


        self._verifyLastState(['']) # we should have two of them in here when it works. (maybe three with REDEEM_COINS_REQUEST)

        if isinstance(message, RedeemCoinsRequest):
            # we output this. Previous step was in ????
            print 'Got a RedeemCoinsRequest. I did not know we got these.'

        elif isinstance(message, RedeemCoinsAccept):
            if self.isRequiresMRbeforeRCR:
                # We have our MintRequest and RedeemCoinsRequests in. All to do now is Fetch our coins!

                self.manager.isMessageType.persistant.request_id = self.manager.persistant.mintRequestID

                self.manager.isMessageType.removeCallback(self.handle) #remove the callback. Not coming here again
                self._createAndOutputIS(FetchMintedRequest)

            else:
                # We have done our RedeemCoinsRequest. Now do a MintRequest, and then finaly a FetchMintedRequest

                self.manager.isMessageType.persistant.request_id = self.manager.persistant.mintRequestID

                # setup blinds only for the MintRequest message
                blinds = []
                for b in self.manager.persistant.mintBlanks:
                    b.blind_blank(self.manager.entity.cdds) # XXX should this be in makeBlanks() instead?
                    blinds.append((b.key_identifier, b.blind_value))
                self.manager.isMessageType.persistant.blinds = blinds

                self.manager.isMessageType.removeCallback(self.handle)
                self._createAndOutputIS(MintRequest)

        elif isinstance(message, RedeemCoinsReject):
            self.reason = self.manager.isMessageType.persistant.reason
            # undo the damage and tell someone
            self.manager.failure(message, self)

        self._setLastState(message.identifier)

class FetchMinted(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.isMessageType.addCallback(self.handle)

    def handle(self, message):
        if not isinstance(message, FetchMintedRequest) and not isinstance(message, FetchMintedAccept) and not \
                        isinstance(message, FetchMintedFailure) and not isinstance(message, FetchMintedWait):
            if message.messageLayer.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('FetchMinted should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                message.messageLayer.globals.lastState))
            else:
                raise MessageError('We somehow called FetchMinted.handle() but cannot be there. Message: %s' % message.identifier)


        self._verifyLastState(['REDEEM_COINS_ACCEPT', 'MINT_ACCEPT', 'FETCH_MINTED_REQUEST'])

        if isinstance(message, FetchMintedRequest):
            # we output this. Previous step was in ????
            print 'Got a FetchMintedRequest. I did not know we got these.'

        elif isinstance(message, FetchMintedAccept):
            self.manager.isMessageType.removeCallback(self.handle) #remove the callback. Not coming here again

            self.signatures = self.manager.isMessageType.persistant.signatures
            self.manager.persistant.signatures = self.signatures

            successes, failures = self.verifySignatures(self.signatures, self.manager.persistant.mintingKeysDenomination, self.manager.persistant.mintBlanks,
                                                        self.manager.entity.cdds)
            self.manager.persistant.newCoins = successes
            self.manager.persistant.mintingFailures = failures

            if successes:
                self.depositCoins(self.manager.entity.coins, successes)
                self.manager.success(self, message)
            if failures:
                self.manager.failure(self, message)

            #FIXME: Why isn't it in the callbacks?
            #self.manager.isMessageType.removeCallback(self.handle)

        elif isinstance(message, FetchMintedWait) or isinstance(message, FetchMintedFailure):
            self.reason = self.manager.isMessageType.persistant.reason
            # undo the damage and tell someone
            self.manager.failure(message, self)

            self.manager.isMessageType.removeCallback(self.handle)

        self._setLastState(message.identifier)

    def verifySignatures(self, signatures, minting_keys, minting_blanks, cdds):
        """verifies the signatures received and makes coins out of blanks."""
        successes = []
        failures = []

        if len(minting_blanks) != len(signatures):
            #FIXME: logging
            #pass # nothing we can do here. Try to salvage what we can. We are going to assume they still line up
            raise MessageError('minting_blanks and signatures are different lengths') # screw it

        for i in range(len(signatures)):
            sig = signatures[i]
            bnk = minting_blanks[i]
            #FIXME another 'Only one CDD per transaction' belief. This one may be valid -- talking to IS
            cdd = cdds[minting_blanks[0].currency_identifier]
            unblinded = bnk.unblind_signature(sig)
            try:
                coin = bnk.newCoin(unblinded, cdd, minting_keys[bnk.denomination])
                # the call to newCoin verifies the signature
                successes.append(coin)
            except CryptoError:
                failures.append(bnk, sig)

        return successes, failures

    def depositCoins(self, entity_coins, coins):
        """Adds the coins to our wallet."""
        entity_coins.extend(coins)

class UnlockCoins(Handler):
    def __init__(self, manager, firstMessage):
        self.manager = manager
        self.manager.dsdbMessageType.addCallback(self.handle)

    def handle(self, message):
        if not isinstance(message, UnlockCoinsRequest) and not isinstance(message, UnlockCoinsPass) and not isinstance(message, UnlockCoinsFailure):
            if message.messageLayer.globals.lastState == MessageHello: # we are now on a different message. Oops.
                raise MessageError('UnlockCoins should have already been removed. It was not. Very odd. Message: %s LastMessage: %s' % (message.identifier,
                                                                                                                message.messageLayer.globals.lastState))
            else:
                raise MessageError('We somehow called UnlockCoins.handle() but cannot be there. Message: %s' % message.identifier)


        self._verifyLastState([]) # FIXME: Figure it out later

        if isinstance(message, UnlockCoinsRequest):
            # we output this. Previous step was in ?????
            print 'Got a UnlockCoinsRequest. I did not know we got these.'

        elif isinstance(message, UnlockCoinsPass):
            #FIXME: do something USEFUL here
            self.manager.dsdbMessageType.removeCallback(self.handle)
        
        elif isinstance(message, UnlockCoinsFailure):
            #FIXME: do something USEFUL here
            self.manager.dsdbMessageType.removeCallback(self.handle)
            #self.manager.failure(message, self)

        self._setLastState(message.identifier)

    def timeNow(self):
        import time
        return time.time()

