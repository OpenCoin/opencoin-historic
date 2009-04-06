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
            return (response.text,response.signatures)
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
            if value:
                answer = messages.TransferAccept()
                answer.text = text
                answer.signatures = value
            else:
                raise 'something went wrong'
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



