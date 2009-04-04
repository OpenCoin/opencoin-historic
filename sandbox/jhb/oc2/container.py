from containerbase import *
import occrypto


class CDD (Container):
    "Currency Description Document"

    fields = [
        Field('standardId'),
        Field('currencyId'),
        Field('shortCurrencyId'),
        Field('issuerServiceLocation'),
        Field('denominations'),
        Field('issuerCipherSuite'),
        Field('options'),
        OneItemField('masterPubKey',klass=occrypto.PubKey),
        Field('issuer'),
        Field('version'),
        Field('signature',signing=False)
    ]


class MKC(Container):
    "Mint Key Certificate"

    fields = [
        Field('keyId'),
        Field('currencyId'),
        Field('denomination'),
        DateField('notBefore'),
        DateField('keyNotAfter'),
        DateField('coinNotAfter'),
        OneItemField('publicKey',klass=occrypto.PubKey),
        Field('issuer'),
        Field('signature',signing=False)
    ]


class Coin(Container):
    fields = [
        Field('standardId'),
        Field('currencyId'),
        Field('denomination'),
        Field('keyId'),
        Field('serial'),
        Field('signature',signing=False)
    ]

    def setNewSerial(self):
        self.serial = occrypto.createSerial()




if __name__ == "__main__":
    import doctest,sys
    if len(sys.argv) > 1 and sys.argv[-1] != '-v':
        name = sys.argv[-1]
        gb = globals()
        verbose = '-v' in sys.argv 
        doctest.run_docstring_examples(gb[name],gb,verbose,name)
    else:        
        doctest.testmod(optionflags=doctest.ELLIPSIS)
