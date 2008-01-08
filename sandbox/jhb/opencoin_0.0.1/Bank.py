# (c) 2007 Nils Toedtmann, Joerg Baach, License GPL

class Bank(object):

    def __init__(self):
        """
        >>> b = Bank()
        >>> b.addAccount('nils',-20,100)
        >>> b.addAccount('jhb',0,0)
        >>> b.addAccount('tom',-100,0)
        >>> b.deposit('jhb',20)
        20

        >>> b.payout('jhb',10)
        10
        
        >>> b.payout('jhb',15)
        Traceback (most recent call last):
        ...
        OverLimit
        """
        
        self.accounts = {}
        

    def addAccount(self,id,limit=0,balance=0):
        self.accounts[id]= dict(limit=limit,balance=balance)
    
    def delAccount(self,id):
        del(self.accounts[id])

    def getAccount(self,id):
        return self.accounts[id]

    def deposit(self,id,amount):
        self.getAccount(id)['balance'] += amount
        return self.getBalance(id)

    def getBalance(self,id):
        return self.getAccount(id)['balance']

    def payout(self,id,amount):
        account = self.getAccount(id)
        if (account['balance'] - amount) < account['limit']:
            raise 'OverLimit'
        else:
            account['balance'] -= amount
            return account['balance']


def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()



