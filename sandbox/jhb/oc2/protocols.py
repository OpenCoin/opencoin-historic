import messages

class Protocol(object):

    def __init__(self,transport):
        self.transport = transport

    def getResponse(self):
        return self.transport.readMessage()

class AskLatestCDD(Protocol):

    def __init__(self,transport):
        self.transport = transport
    
    def run(self,message=None):
        message = messages.AskLatestCDD()  
        response = self.transport(message)
        return response.cdd 

class GiveLatestCDD(Protocol):
    
    def __init__(self,issuer):
        self.issuer = issuer
    
    def run(self,message=None):
        if message:
            answer = messages.GiveLatestCDD()
            answer.cdd = self.issuer.getCDD()
            return answer
        else:
            pass

class FetchMintKeys(Protocol):

    def __init__(self,transport,denominations=None,keyids=None):
        if denominations and keyids:
            raise "you can't ask for denominations and keyids at the same time"
        if not (denominations or keyids):
            raise "you need to ask at least for one"
        self.transport = transport
        self.denominations = denominations
        self.keyids = keyids

    def run(self,message=None):
        message = messages.FetchMintKeys()
        message.denominations = self.denominations
        message.keyids = self.keyids

        response = self.transport(message)
        if response.header == 'MINTING_KEY_FAILURE':
            raise message
        else:
            return  response.keys

class GiveMintKeys(Protocol):

    def __init__(self,issuer):
        self.issuer = issuer
 
    def run(self,message):
        keys = []
        if message.denominations:
            keyslist = self.issuer.getCurrentMKCs()
            for d in message.denominations:
                keys.append(keyslist.get(d))
        elif message.keyids:
            for id in message.keyids:
                keys.append(self.issuer.getKeyById(id))
        
        answer = messages.GiveMintKeys()
        answer.keys = keys
        return answer




class CoinsSpendSender(Protocol):

    def __init__(self,coins,target):
        self.coins = coins
        self.target = target

    def spendCoins(self,message):
        return ''

    def announceCoins(self,message):
        return ''


class CoinsSpendRecipient(Protocol):

    def hearCoins(self,message):
        return ''

    def receiveCoins(self,message):
        return ''


class TransferCoinsSender(Protocol):
    
    def __init__(self,target,blinds,coins):
        self.target = target
        self.blinds = blinds
        self.coins = coins



    def transferCoins(self,message):
        return ''


class TransferCoinRecipient(Protocol):
    
    def receiveCoins(self,message):
        return ''



