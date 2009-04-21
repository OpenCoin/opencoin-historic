from entity import *
from protocols import *
from container import *
import occrypto

class Wallet(Entity):

    def _makeBlank(self,cdd,mkc):
        blank = container.Coin()
        blank.standardId = cdd.standardId
        blank.currencyId = cdd.currencyId
        blank.denomination = mkc.denomination
        blank.keyId = mkc.keyId
        blank.setNewSerial()
        return blank

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
        

