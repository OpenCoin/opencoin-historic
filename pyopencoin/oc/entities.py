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


class KeyFetchError(Exception):
    pass


class DSDB:
    pass

class Mint:
    """
    >>> m = Mint()
    >>> pub1 = m.createNewKeys('1','now','later',256)
    >>> pub2 = m.createNewKeys('1','now','later',256)
    >>> m.getCurrentKey('1') == pub2
    True
    >>> m.getKeyById(pub1.key_id()) == pub1
    True
    """
    def __init__(self):
        self.keyvault = {}    
        self.keyids = {}


    def createNewKeys(self,denomination,not_before,not_after,keylength=1024):
        import crypto
        keys = crypto.createRSAKeyPair(keylength)
        public = keys.newPublicKeyPair()
        #XXX Ugly,ugly,ugly
        pos = len(self.keyvault.setdefault(denomination,[]))
        self.keyvault[denomination].append(dict(not_before=not_before,
                                                not_after=not_after,
                                                keys = keys,
                                                public = public))
        self.keyids[keys.key_id()] = [denomination,pos]
        return public

    def getCurrentKey(self,denomination):
        return self.keyvault[denomination][-1]['public']

    def getKeyById(self,keyid):
        denomination,pos = self.keyids[keyid]
        return self.keyvault[denomination][pos]['public']

    def getKey(self,denomination,notbefore,notafter):
        pass



class Blank:
    pass

class Coin:
    pass

class Key:
    pass

class PubKey:
    pass



if __name__ == "__main__":
    import doctest
    doctest.testmod()
