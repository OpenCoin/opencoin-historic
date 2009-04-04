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
