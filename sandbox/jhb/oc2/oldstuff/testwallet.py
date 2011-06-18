"""
>>> import wallet
>>> import storage
>>> w = wallet.Wallet(storage.Storage().setFilename('data/test.bin'))
>>> import transports
>>> transport = transports.HTTPTransport('http://baach.de:9090/')
>>> w.addCurrency(transport)
>>> w.mintCoins(transport,13,'foobar')
>>> transport = transports.HTTPTransport('http://localhost:9091/wallet.cgi')
>>> w.spendCoins(transport,'BaachBuck',5,'foobar')

"""


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
