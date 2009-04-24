from entity import *
from protocols import *
from container import *
import occrypto
import messages

class Wallet(Entity):

    def _makeBlank(self,cdd,mkc):
        blank = container.Coin()
        blank.standardId = cdd.standardId
        blank.currencyId = cdd.currencyId
        blank.denomination = mkc.denomination
        blank.keyId = mkc.keyId
        blank.setNewSerial()
        return blank

    def blanksFromCoins(self,coins):
        pass

    def makeSerial(self):
        return occrypto.createSerial()
    
    def addOutgoing(self,message):
        self.storage.setdefault('outgoing',{})[message.transactionId] = message

    def getOutgoing(self,tid):
        return self.storage.setdefault('outgoing',{})[tid]

    def addIncoming(self,message):
        self.storage.setdefault('incoming',{})[message.transactionId] = message
        
    def getIncoming(self,tid):
        return self.storage.setdefault('incoming',{}).get(tid,None)

    def getApproval(self,message):
        amount = message.amount
        target = message.target
        approval = getattr(self,'approval',True) #get that from ui
        if approval == True:
            self.addIncoming(message)
        return approval
        

    def askLatestCDD(self,transport):
        response = transport(messages.AskLatestCDD())
        return response.cdd


    def fetchMintKeys(self,transport,denominations=None,keyids=None):
        if denominations and keyids:
            raise "you can't ask for denominations and keyids at the same time"
        if not (denominations or keyids):
            raise "you need to ask at least for one"
        
        message = messages.FetchMintKeys()
        message.denominations = denominations
        message.keyids = keyids
        
        response = transport(message)

        if response.header == 'MINTING_KEY_FAILURE':
            raise message
        else:
            return  response.keys
       

    def requestTransfer(self,transport,transactionId,target=None,blinds=None,coins=None):
        if target and blinds:
            requesttype = 'mint'
        elif target and coins:
            requesttype = 'redeem'
        elif blinds and coins:
            requesttype = 'exchange'
        else:
            raise 'Not a valid combination of options'
        
        message = messages.TransferRequest()
        message.transactionId = transactionId
        message.target = target
        message.blinds = blinds
        message.coins = coins
        message.options = dict(type=requesttype).items()

        response = transport(message)
        return response

    def resumeTransfer(self,transport,transactionId):
        message = messages.TransferResume()
        message.transactionId = transactionId
        response = transport(message)
        return response


    def announceSum(self,transport,tid,amount,target):
        message = messages.SumAnnounce()
        message.transactionId = tid
        message.amount = amount    
        message.target = target
        self.addOutgoing(message)
        response = transport(message)
        if response.header == 'SumReject':
            return response.reason
        else:
            return True

    def listenSum(self,message):
        approval = self.getApproval(message)
        if approval == True:
            answer = messages.SumAccept()
        else:
            answer = messages.SumReject()
            answer.reason = approval
        answer.transactionId = message.transactionId            
        return answer

    def requestSpend(self,transport,tid,coins):
        message = messages.SpendRequest() 
        message.transactionId = tid
        message.coins = coins
        response = transport(message)
        if response.header == 'SpendReject':
            raise response
        else:
            return True

    def listenSpend(self,message):
        tid = message.transactionId
        amount = sum([int(m.denomination) for m in message.coins])
        #check transactionid
        orig = self.getIncoming(tid)
        if not orig:
            answer = messages.SpendReject()
            answer.reason = 'unknown transactionId'
            return answer
        #check sum
        if amount != int(orig.amount):
            answer = messages.SpendReject()
            answer.reason = 'amount of coins does not match announced one'
            return answer
        #do exchange


        answer = messages.SpendAccept()
        answer.transactionId = tid
        return answer

