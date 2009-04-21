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

class TransferRequest(Protocol):
    def __init__(self,transport,transactionId,target=None,blinds=None,coins=None):
        self.transport = transport
        self.transactionId=transactionId
        self.target = target
        self.blinds = blinds
        self.coins = coins

    def run(self,message=None):
        if self.target and self.blinds:
            requesttype = 'mint'
        elif self.target and self.coins:
            requesttype = 'redeem'
        elif self.blinds and self.coins:
            requesttype = 'exchange'
        else:
            raise 'Not a valid combination of options'
        
        message = messages.TransferRequest()
        message.transactionId = self.transactionId
        message.target = self.target
        message.blinds = self.blinds
        message.coins = self.coins
        message.options = dict(type=requesttype).items()

        response = self.transport(message)
        header = response.header
        if header == 'TransferReject':
            return ('TransferReject','')
        elif header == 'TransferDelay':
            return ('TransferDelay','')
        elif header == 'TransferAccept':
            return ('TransferAccept',response.signatures)
        else:
            raise 'unknown thing'

class TransferHandling(Protocol):

    def __init__(self,mint,authorizer):
        self.mint = mint
        self.authorizer = authorizer

    def run(self,message):
        options = dict(message.options)
        requesttype = options['type']
        if requesttype == 'mint':
            authorizedMessage = self.authorizer.authorize(message)
            if type(authorizedMessage) == messages.Error:
                return messages.TransferReject()
                 
            response  = self.mint.handleTransferRequest(authorizedMessage)
            if type(response) == messages.Error:
                return messages.TransferReject()

            text,value = response
            if text=='minted':
                answer = messages.TransferAccept()
                answer.signatures = value
            elif text =='delayed':
                answer = messages.TransferDelay()
                answer.transactionId = message.transactionId
                answer.reason = value
            else:
                raise 'something went wrong'
        return answer    

class TransferResume(Protocol):

    def __init__(self,transport,transactionId):
        self.transport = transport
        self.transactionId = transactionId

    def run(self,message=None):
        message = messages.TransferResume()
        message.transactionId = self.transactionId
        response = self.transport(message)
        header = response.header
        if header == 'TransferReject':
            return ('TransferReject','')
        elif header == 'TransferDelay':
            return ('TransferDelay','')
        elif header == 'TransferAccept':
            return ('TransferAccept',response.signatures)
        else:
            raise 'unknown thing'

        return response.cdd 

class TransferResumeHandling(Protocol):

    def __init__(self,issuer):
        self.issuer = issuer

    def run(self,message):
            
        signatures = self.issuer.getTransactionResult(message.transactionId)
        if signatures:
            answer = messages.TransferAccept()
            answer.signatures = signatures
        else:
            answer = messages.TransferDelay()
            answer.transactionId = message.transactionId
            answer.reason = 'issuer has no coins yet'
        return answer    

class SumAnnounce(Protocol):

    def __init__(self,transport,wallet,tid,amount,target):
        self.transport = transport
        self.amount = amount
        self.target = target
        self.tid = tid
        self.wallet = wallet
    
    def run(self,message=None):
        message = messages.SumAnnounce()
        message.transactionId = self.tid
        message.amount = self.amount    
        message.target = self.target
        self.wallet.addOutgoing(message)
        response = self.transport(message)
        if response.header == 'SumReject':
            return response.reason
        else:
            return True


class SumAnnounceListen(Protocol):
    
    def __init__(self,wallet):
        self.wallet = wallet
    
    def run(self,message=None):
        approval = self.wallet.getApproval(message)
        if approval == True:
            answer = messages.SumAccept()
        else:
            answer = messages.SumReject()
            answer.reason = approval
        answer.transactionId = message.transactionId            
        return answer


class SpendRequest(Protocol):

    def __init__(self,transport,wallet,tid,coins):
        self.transport = transport
        self.wallet = wallet
        self.tid = tid
        self.coins = coins
    
    def run(self,message=None):
        message = messages.SpendRequest() 
        message.transactionId = self.tid
        message.coins = self.coins
        response = self.transport(message)
        if response.header == 'SpendReject':
            raise response
        else:
            return True

class SpendListen(Protocol):
    
    def __init__(self,wallet):
        self.wallet = wallet
    
    def run(self,message=None):
        tid = message.transactionId
        amount = sum([int(m.denomination) for m in message.coins])
        #check transactionid
        orig = self.wallet.getIncoming(tid)
        if not orig:
            answer = messages.SpendReject()
            answer.reason = 'unknown transactionId'
            yield answer
            return
        #check sum
        if amount != int(orig.amount):
            answer = messages.SpendReject()
            answer.reason = 'amount of coins does not match announced one'
            yield answer
            return
        yield 'trying to exchange' 
        #try to exchange. To yield or not to yield?
        import pdb; pdb.set_trace()
        #return answer
        answer = messages.SpendAccept()
        answer.transactionId = tid
        yield answer

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



