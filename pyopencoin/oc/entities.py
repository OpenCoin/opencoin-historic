import protocols
from messages import Message

class Wallet:
    "Just a testwallet. Does nothing, really"

    def __init__(self):
        self.coins = []

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

class Issuer:

    def __init__(self):
        self.dsdb = DSDB()
        self.mint = Mint()

    def getKeyByDenomination(self,denomination):
        raise 'KeyFetchError'
    
    def getKeyById(self,keyid):
        raise 'KeyFetchError'


class KeyFetchError(Exception):
    pass


class DSDB:
    pass

class Mint:
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
