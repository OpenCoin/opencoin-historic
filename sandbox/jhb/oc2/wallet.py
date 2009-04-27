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
        message.denominations = [str(d) for d in denominations]
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


    def getCurrency(self,id):
        if self.storage.has_key(id):
            return self.storage[id]
        else:
            currency = dict(cdds=[],
                            blanks = {},
                            coins = [],
                            transactions = {})
            self.storage[id]=currency
            return currency

    def listCurrencies(self):
        out = []
        for key,currency in self.storage.items():
            cdd = currency['cdds'][-1]
            amount = sum([int(coin.denomination) for coin in currency['coins']])
            out.append((cdd,amount))
        return out            

    def deleteCurrency(self,id):
        del(self.storage[id])


    def tokenizeForBuying(self,amount,denominations):
        denominations = [int(d) for d in denominations]
        denominations.sort()
        denominations.reverse()

        out = []
        for d in denominations:
            while amount and amount >= d:
                out.append(d)
                amount -= d
        return out                

        

#################################higher level#############################

    def addCurrency(self,transport):
        cdd = self.askLatestCDD(transport)
        id = cdd.currencyId
        currency = self.getCurrency(id)
        if cdd.version not in [cdd.version for cdd in currency['cdds']]:
            currency['cdds'].append(cdd)

    def buyCoins(self,transport,amount,target):
        cdd = self.askLatestCDD(transport)
        currency = self.getCurrency(cdd.currencyId)
        tokenized =  self.tokenizeForBuying(amount,cdd.denominations) #what coins do we need
        wanted = list(set(tokenized)) #what mkcs do we want
        
        keys = self.fetchMintKeys(transport,denominations=wanted)
        mkcs = {}
        for mkc in keys:
            if not cdd.masterPubKey.verifyContainerSignature(mkc):
                raise 'Invalid signature on mkc'
            mkcs[mkc.denomination] = mkc
        
        secrets = []
        data = []
        print tokenized
        for denomination in tokenized:
            mkc = mkcs[str(denomination)]
            blank = self._makeBlank(cdd,mkc)
            secret,blind = mkc.publicKey.blindBlank(blank)
            secrets.append((blank,blind,mkc,secret))
            data.append((mkc.keyId,blind))

        tid = self.makeSerial() 
        response = self.requestTransfer(transport,tid,target,data,[])                 
        i = 0
        signatures = response.signatures
        for signature in signatures:
            blank,blind,mkc,secret = secrets[i]
            key = mkc.publicKey
            blank.signature = key.unblind(secret,signature)
            coin = blank
            if not key.verifyContainerSignature(coin):
                raise 'Invalid signature' 
            currency['coins'].append(coin)
            i += 1
            self.storage.save()
