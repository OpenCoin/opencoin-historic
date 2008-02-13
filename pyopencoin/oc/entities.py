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
        protocol = protocols.answerHandshakeProtocol(sendMoney=protocols.WalletRecipientProtocol(self))
        transport.setProtocol(protocol)
        transport.start()

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

    def getKeyByDenomination(self,denomination):
        try:
            return self.mint.getCurrentKey(denomination)
        except KeyError:            
            raise 'KeyFetchError'
    
    def getKeyById(self,keyid):
        try:
            return self.mint.getKeyById(keyid)
        except KeyError:            
            raise 'KeyFetchError'

    def createKeys(self,keylength=1024):
        import crypto
        keys = crypto.createRSAKeyPair(keylength)
        self.keys = keys
     
    def giveMintingKey(self,transport):
        protocol = protocols.giveMintingKeyProtocol(self)
        transport.setProtocol(protocol)
        transport.start()

    def createMintKey(self, issuer_signing_key, denomination, not_before,
                      key_not_after, coin_not_after, size=1024):
        """Create a new MintKey and register it with the Mint."""
        #Note: I'm assuming RSA/SHA256. It should really use the CDD defined ones
        #      hmm. And it needs the CDD for the currency_identifier
        import crypto
        private = crypto.createRSAKeyPair(size)
        public = private.newPublicKeyPair()

        hash_alg = crypto.SHA256HashingAlgorithm

        import containers
        mintKey = containers.MintKey(key_identifier=public.key_id(hash_alg),
                                     currency_identifier='http://...Cent/',
                                     denomination=denomination,
                                     not_before=not_before,
                                     key_not_after=key_not_after,
                                     coin_not_after=coin_not_after,
                                     public_key=public)

        sign_alg = crypto.RSASigningAlgorithm
        signer = sign_alg(issuer_signing_key)
        sig = Signature(keyprint = issuer_signing_key.key_id(hash_alg),
                        signature = signer.sign(mintKey.content_part()))

        mintKey.signature = sig


        self.mint.addMintKey(mintKey, private)
        
        

class KeyFetchError(Exception):
    pass


class DSDB:
    pass

class Mint:
    """A Mint is the minting agent for a a currency. It has the 
    >>> m = Mint()

    >>> def makeFakeMintKey():
    ...     pass

    #>>> pub1 = m.createNewKeys('1','now','later',256)
    #>>> pub2 = m.createNewKeys('1','now','later',256)
    #>>> m.getCurrentKey('1') == pub2
    #True
    #>>> m.getKeyById(pub1.key_id()) == pub1
    #True
    """
    def __init__(self):
        self.keyvault = {}
        self.keyids = {}
        self.privatekeys = {}


    def getCurrentKey(self,denomination):
        return self.keyvault[denomination][-1]['public']

    def getKeyById(self,keyid):
        return self.keyids[keyid]

    def getKey(self,denomination,notbefore,notafter):
        pass

    def getPrivateKey(self, keyid):
        return self.privatekeys[keyid]

    def addMintKey(self, mintKey, privateKey):
        self.keyvault.setdefault(mintKey.denomination, [])
        self.keyvault[mintKey.denomination].append(mintKey)
        self.keyids[mintKey.key_id] = mintKey
        self.privatekeys[mintKey.key_id] = privateKey




if __name__ == "__main__":
    import doctest
    doctest.testmod()
