class Protocol(object):

    def __init__(self):
        self.digest = self.dummy

    def dummy(self,message):
        
        return ''



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
    

class requestCDD(Protocol):
    
    def __init__(self,cdd_version):
        self.cdd_version = cdd_version


    def getCDD(self,message):
        return ''

class giveCDD(Protocol):

    def giveCDD(self,message):
        return ''
