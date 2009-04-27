"""
>>> import wallet
>>> import storage
>>> w = wallet.Wallet(storage.Storage().setFilename('data/test.bin'))
>>> import transports
>>> transport = transports.HTTPTransport('http://localhost:9090/')
>>> w.buyCoins(transport,97,'foobar')


"""


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
