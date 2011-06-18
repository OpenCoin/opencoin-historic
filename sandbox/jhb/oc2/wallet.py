from entity import *
from container import *
import occrypto
import messages
import coinsplitting
import sys

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
        #sys.stderr.write(str(self.storage.filename))

    def getIncoming(self,tid):
        #sys.stderr.write(str(tid)) 
        #sys.stderr.write(str(self.storage.filename)) 
        transaction = self.storage.setdefault('incoming',{}).get(tid,None)
        if transaction != None:
            del(self.storage['incoming'][tid])
        return transaction            

        

    def askLatestCDD(self,transport):
        self.feedback('Talking to issuer: fetching latest CDD')
        response = transport(messages.AskLatestCDD())
        if not isinstance(response,messages.GiveLatestCDD):
            raise Exception, 'Not a valid message'
        if not response.cdd.masterPubKey.verifyContainerSignature(response.cdd):
            raise Exception, 'Could not verify cdd'
        return response.cdd


    def fetchMintKeys(self,transport,cdd,denominations=None,keyids=None):
        if denominations and keyids:
            raise Exception, "you can't ask for denominations and keyids at the same time"
        if not (denominations or keyids):
            raise Exception, "you need to ask at least for one"
        message = messages.FetchMintKeys()
        denominations = [str(d) for d in denominations]
        message.denominations = denominations
        message.keyids = keyids
        self.feedback('Talking to issuer: fetching mintkeys')
        response = transport(message)
        
        if response.header == 'MINTING_KEY_FAILURE':
            raise message
        
        if not isinstance(response,messages.GiveMintKeys):
            raise Exception, 'Not a valid message'
        
        if set(denominations).difference(set([key.denomination for key in response.keys])):
            raise Exception, 'Not all denominations met'

        for key in response.keys:
            if not cdd.masterPubKey.verifyContainerSignature(key):
                raise Exception, 'Could not verify key'
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
        self.feedback('Talking to issuer: request %s' % requesttype)
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
            self.addIncoming(message)
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


    def listenSpend(self,message,transport=None):
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
            answer.reason = 'amount of coins does not match announced one. Announced: %s, got %s' % (orig.amount, amount)
            return answer

        #do exchange
        if transport:
            cdd = self.askLatestCDD(transport)
            currency = self.getCurrency(cdd.currencyId)
            newcoins = message.coins 
            answer = self.freshenUp(transport,cdd,newcoins)
            if answer.header != 'TransferAccept':
                answer = messages.SpendReject()
                answer.reason = 'did not go through'
                return answer
        
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
            try:
                cdd = currency['cdds'][-1]
                amount = sum([int(coin.denomination) for coin in currency['coins']])
                out.append((cdd,amount))
            except:
                #del(self.storage[key]) XXX why was that?
                pass
        return out            

    def deleteCurrency(self,id):
        del(self.storage[id])
    
    def tokenizeForBuying(self,amount,denominations):
        return coinsplitting.tokenizer([int(d) for d in denominations],amount)                   

    def pickForSpending(self,amount,coins):
        tmp = [(int(c.denomination),c) for c in coins]
        tmp.sort()
        tmp.reverse()
        mycoins = [t[1] for t in tmp]
        picked = []
        for coin in mycoins:
            sumpicked = sum([int(c.denomination) for c in picked])
            if sumpicked < amount:
                if int(coin.denomination) <= (amount - sumpicked):
                    picked.append(coin)
            else:
                break
        return picked                

    def getApproval(self,message):
        amount = message.amount
        target = message.target
        approval = getattr(self,'approval',True) #get that from ui
        return approval

    def feedback(self,message):
        #print message
        pass

#################################higher level#############################

    def addCurrency(self,transport):
        cdd = self.askLatestCDD(transport)
        id = cdd.currencyId
        currency = self.getCurrency(id)
        if cdd.version not in [cdd.version for cdd in currency['cdds']]:
            currency['cdds'].append(cdd)

    def mintCoins(self,transport,amount,target):
        cdd = self.askLatestCDD(transport)
        currency = self.getCurrency(cdd.currencyId)
        tokenized =  self.tokenizeForBuying(amount,cdd.denominations) #what coins do we need
        tid = self.makeSerial()
        secrets,data = self.prepareBlanks(transport,cdd,tokenized)
        response = self.requestTransfer(transport,tid,target,data,[])
        signatures = response.signatures
        currency['coins'].extend(self.unblindWithSignatures(secrets,signatures))
        self.storage.save()

    def prepareBlanks(self,transport,cdd,values):        
        wanted = list(set(values)) #what mkcs do we want
        keys = self.fetchMintKeys(transport,cdd,denominations=wanted)
        mkcs = {}
        for mkc in keys:
            if not cdd.masterPubKey.verifyContainerSignature(mkc):
                raise Exception, 'Could not verify mkc'
            mkcs[mkc.denomination] = mkc
        
        secrets = []
        data = []
        self.feedback('Talking to issuer: preparing blanks')
        for denomination in values:
            mkc = mkcs[str(denomination)]
            blank = self._makeBlank(cdd,mkc)
            secret,blind = mkc.publicKey.blindBlank(blank)
            secrets.append((blank,blind,mkc,secret))
            data.append((mkc.keyId,blind))
        return secrets,data


       
    def unblindWithSignatures(self,secrets,signatures):        
        i = 0
        coins = []
        for signature in signatures:
            blank,blind,mkc,secret = secrets[i]
            key = mkc.publicKey
            blank.signature = key.unblind(secret,signature)
            coin = blank
            if not key.verifyContainerSignature(coin):
                raise 'Invalid signature' 
            coins.append(coin)
            i += 1
        return coins            

    def getAllCoins(self,currencyId):
        currency = self.getCurrency(currencyId)
        tmp = [(int(c.denomination),c) for c in currency['coins']]
        tmp.sort()
        return [t[1] for t in tmp]



    def redeemCoins(self,transport,amount,target):
        cdd = self.askLatestCDD(transport)
        currency = self.getCurrency(cdd.currencyId)
        coins = currency['coins']
        picked = self.pickForSpending(amount,coins)
        tid = self.makeSerial()
        response = self.requestTransfer(transport,tid,target,[],picked)
        newcoins = [c for c in coins if c not in picked]
        currency['coins'] = newcoins        
        self.storage.save()
        self.freshenUp(transport,cdd)


    def freshenUp(self,transport,cdd,newcoins=[]):        
        currency = self.getCurrency(cdd.currencyId)
        paycoins,secrets,data = self.prepare4exchange(transport,cdd,currency['coins'],newcoins)
        if secrets:
            tid = self.makeSerial()
            response = self.requestTransfer(transport,tid,None,data,paycoins+newcoins)
            if response.header != 'TransferAccept':
                return response
            coins = currency['coins']
            for coin in paycoins:
                coins.pop(coins.index(coin))
            coins.extend(self.unblindWithSignatures(secrets,response.signatures)) 
            self.storage.save()
            return response 
        else:
            return messages.Error()

    def prepare4exchange(self,transport,cdd,oldcoins,newcoins):
        oldcoins = [c for c in oldcoins]
        newcoins = [c for c in newcoins]
        
        oldvalues = [int(c.denomination) for c in oldcoins]
        newvalues = [int(c.denomination) for c in newcoins]
        denominations = [int(d) for d in cdd.denominations]
        keep,pay,blank = coinsplitting.prepare_for_exchange(denominations,oldvalues,newvalues)
        
        if blank:
            paycoins = []
            for value in pay:
                for coin in oldcoins:
                    if int(coin.denomination) == value:
                        paycoins.append(oldcoins.pop(oldcoins.index(coin)))
                        break
        
            secrets,data = self.prepareBlanks(transport,cdd,blank)
            return paycoins,secrets,data
        else:
            return [],[],[]


    def spendCoins(self,transport,currencyId,amount,target):
        currency = self.getCurrency(currencyId)
        coins = currency['coins']
        picked = self.pickForSpending(amount,coins)
        tid = self.makeSerial()
        
        self.feedback(u'Spending coins: wating for confirmation')
        response = self.announceSum(transport,tid,amount,target)
        self.feedback(u'Spending coins: wating for other side')
        response = self.requestSpend(transport,tid,picked)
        if response == True: 
            newcoins = [c for c in coins if c not in picked]
            currency['coins'] = newcoins        
            self.storage.save()


