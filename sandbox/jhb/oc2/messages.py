from containerbase import *
import container
import occrypto

class Message(Container):
    fields = [
        Field('header'),
    ]

    def __init__(self,data={}):
        Container.fromData(self,data)
        self.header = self.__class__.__name__

class AskLatestCDD(Message):
    pass

class GiveLatestCDD(Message):
    fields = Message.fields + [
        OneItemField('cdd',klass=container.CDD)
    ]

class FetchMintKeys(Message):
    fields = Message.fields + [
        Field('denominations'),
        Field('keyids')
    ]

class GiveMintKeys(Message):
    fields = Message.fields + [
        SubitemsField('keys',klass=container.MKC)
    ]



