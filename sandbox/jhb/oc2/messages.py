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

class MessageException(Message,Exception):

    def __str__(self):
		return str(self.reason)

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

class TransferRequest(Message):
     fields = Message.fields + [
        Field('transactionId'),
        Field('target'),
        Field('blinds'),
        SubitemsField('coins',klass=container.Coin),
        Field('options'),
    ]

class TransferAccept(Message):
    fields = Message.fields + [
        Field('signatures'),
    ]

class AuthorizedMessage(Message):
    fields = Message.fields + [
        OneItemField('message',klass=Message),
        Field('keyId'),
        Field('signature',signing=False)
    ]
class Error(Message, Exception):
    fields = Message.fields + [
        Field('text'),
        Field('data'),
        Field('keyId'),
        Field('signature',signing=False)
    ]

class TransferReject(Message):
    pass

class TransferDelay(Message):
     fields = Message.fields + [
        Field('transactionId'),
        Field('reason'),
    ]

class TransferResume(Message):
     fields = Message.fields + [
        Field('transactionId'),
    ]

class TransferResume(Message):
     fields = Message.fields + [
        Field('transactionId'),
    ]

class TransferResume(Message):
     fields = Message.fields + [
        Field('transactionId'),
    ]

class SumAnnounce(Message):
     fields = Message.fields + [
        Field('transactionId'),
        Field('amount'),
        Field('target'),
    ]

class SumAccept(Message):
     fields = Message.fields + [
        Field('transactionId'),
    ]

   
class SumReject(Message,Exception):
     fields = Message.fields + [
        Field('transactionId'),
        Field('reason'),
    ]

class SpendRequest(Message):
     fields = Message.fields + [
        Field('transactionId'),
        SubitemsField('coins',klass=container.Coin),
    ]

class SpendAccept(Message):
     fields = Message.fields + [
        Field('transactionId'),
    ]


class SpendReject(MessageException):
     fields = Message.fields + [
        Field('transactionId'),
        Field('problems'),
        Field('reason'),
    ]



