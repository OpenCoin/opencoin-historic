import messages

class Protocol(object):

    def __init__(self,transport):
        self.transport = transport

    def getResponse(self):
        return self.transport.readMessage()

class AskLatestCDD(Protocol):

    def __init__(self,wallet,transport):
        self.transport = transport
        self.wallet = wallet
    
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


class FetchMintKeys(Protocol):

    def __init__(self,denomination,keyids,time):
        self.denominations = denominations
        self.keyids = keyids
        self.time = time

    def getKeys(self,message):
        return ''

class GiveMintKeys(Protocol):

    def giveKeys(self,message):
        pass    


