# (c) 2007 Nils Toedtmann, Joerg Baach, License GPL
#The purse
#foobar
from Coin import Coin
from util import *

class Wallet:

    def __init__(self,issuers):
        """
        Setup an issuer and two wallets:
        >>> import Issuer
        >>> url = 'http://opencoin.net/cur1'
        >>> i   = Issuer.Issuer(url,[1,2,4,8])
        >>> w1  = Wallet({url:i})
        >>> w2  = Wallet({url:i})

        Wallet #1 creates blank (=unsigned) coins
        >>> coin_values, rest = partition(i.mint.keys.keys(),20)
        >>> w1.createCoins(coin_values,url)
        >>> w1.createCoins(17,url)
        >>> w1.getBalance()
        {}

        Wallet #1 sends the blinds to the issuer and fetcher their sigs:
        >>> w1.fetchSignedBlinds()
        >>> w1.getBalance()
        {}
        >>> w1.fetchSignedBlinds()
        >>> {url:37} == w1.getBalance()
        True
        
        #>>> `w1.getBalance()`
        #>>> `w2.getBalance()`
        >>> w1coins =  w1.valid.values()

        Wallet #1 sends coins #0 and #1 to wallet #2:
        >>> w1.sendCoins(w2,[w1coins[0],w1coins[1]])
        >>> w2.getBalance()[url] == w1coins[0].value + w1coins[1].value 
        True

        Wallet #1 sends coin #1 twice:
        >>> w1.sendCoins(w2,[w1coins[1]])
        Traceback (most recent call last):
        ...
        REJECT COIN: already in wallet

        Wallet #1 sends coin #2 with wrong value/pubkey pair:
        >>> if     w1coins[2].value == 1 : w1coins[2].pubkey = i.getPubKeys()[2]
        >>> if not w1coins[2].value == 1 : w1coins[2].pubkey = i.getPubKeys()[1]
        >>> w1.sendCoins(w2,[w1coins[2]])
        Traceback (most recent call last):
        ...
        REJECT COIN: bad issuer pubKey

        Wallet #1 sends coin #3 with wrong signature
        >>> w1coins[3].signature += 1
        >>> w1.sendCoins(w2,[w1coins[3]])
        Traceback (most recent call last):
        ...
        REJECT COIN: bad signature

        Wallet #1 redeems coin #4 before sending it to wallet #2:
        >>> w1.sendCoins(i, [w1coins[4]],'my account: 121')
        money redeemed
        >>> w1.sendCoins(w2,[w1coins[4]])
        Traceback (most recent call last):
        ...
        REJECT COIN: double spending


        #>>> `w1.getBalance()`
        #>>> `w1.valid`
        #>>> `w2.getBalance()`

        >>> w2coins = w2.valid.values()

        Wallet #2 redeems coin #0 two times:
        >>> w2.sendCoins(i,[w2coins[0]],'my account: 123')
        money redeemed
        >>> w2.sendCoins(i,[w2coins[0]],'my account: 124')
        Traceback (most recent call last):
        ...
        REJECT COIN: double spending

        Wallet #2 redeems coin #1 with invalid sig:
        >>> w2coins[1].signature += 1
        >>> w2.sendCoins(i,[w2coins[1]],'my account: 124')
        Traceback (most recent call last):
        ...
        REJECT COIN: bad signature
        """

        #init
        self.issuers = issuers
        self.blanks = []
        #TODO: replace dicts with lists/properties whatever
        self.coins = {}
        self.new = {}
        self.pending = {}
        self.valid = {}
        self.cointainers = ['coins','valid','pending','new']
        self.callbacks = {}

    def values(self):
        #returns the values of all holded coins
        return []

    def coins(self):
        #returns all holded coins
        return []

    def createCoins(self,values,issuerurl):
        """requests a coin of a value from the specified issuer
        """
        issuer = self.issuers[issuerurl]    
         
        if type(values) != type([]):
            values, rest = partition(issuer.getPubKeys().keys(),int(values))

        for v in values:
            #create blanks
            coin = Coin(issuer.getUrl(),decodeKey(issuer.getPubKeys_encoded()[str(v)]),v)
            blind = coin.getBlind()
            hash = coin.getHash()
            self.coins[hash] = coin
            self.pending[hash] = coin

        #self.fetchSignedBlinds()


    def fetchSignedBlinds(self):
        
        for hash,coin in self.pending.items():
            issuer = self.issuers[coin.issuerurl]
            #print  (str(coin.getBlind()).encode('base64'),coin.value)
            status,message = issuer.getSignedBlind(str(coin.getBlind()).encode('base64'),coin.value)
            if status == 200:
                coin.setSignature(long(message))
                # TODO: What if the Sig does not verify? 
                self.valid[hash] = coin
                del(self.pending[hash])

            elif status in range(300,400):
                pass

            elif status >=400:
                #Mmm, the issuer did not like our attempt
                del(self.pending[hash])
                del(self.coins[hash])
                
    def getBalance(self):
        #out = dict([(i,0) for i in self.issuers.keys()])
        out = {}
        for coin in self.valid.values():
            out[coin.issuerurl] = out.setdefault(coin.issuerurl,0) + coin.value
        return out


    def sendCoins(self,receiver,coins,message=None):
        coins_encoded = [encodeCoin(coin) for coin in coins] 
        result = receiver.receiveCoins(coins_encoded,message)
        if result:
            for coin in coins:
                self.deleteCoin(coin)


    def receiveCoins(self,coins_encoded,message=None):
        coins = [decodeCoin(coin) for coin in coins_encoded] 
        for callback in getCallbacks(self,'receiveCoins'):
            callback(self,coins_encoded,message)
        for coin in coins:
            hash = coin.getHash()
            #TODO: check if coin.issuerurl in $allowedbanks
            if   not True :
                raise 'REJECT COIN: bad issuer'
            issuer = self.issuers[coin.issuerurl]
            if not coin.pubkey == issuer.getPubKeys()[coin.value] :
                raise 'REJECT COIN: bad issuer pubKey' 
            elif not coin.verifySignature() :
                raise 'REJECT COIN: bad signature'
            elif not issuer.checkDoubleSpending([coin.getHash()]) :
                raise 'REJECT COIN: double spending'
            elif self.coins.has_key(hash) :
                raise 'REJECT COIN: already in wallet'
            else:
                self.coins[hash] = coin
                self.valid[hash] = coin
        return True


    def deleteCoin(self,coin):
        for var in self.cointainers:
            d = getattr(self,var,{})
            hash = coin.getHash()
            if d.has_key(hash):
               del(d[hash])
        coin.deleted = True


    def createCoin(self,value):
        #creates a coin, keeps it, return it as well
        return 'coin'

    def requestChange(self,oldcoins,newcoins,bank=None):
        #request the old coins being exchanged for new ones
        #would be good if old and new ones matched in sum of value
        return []

    def spent(self,value,otherpurse):
        #spent some money
        return true

    def receive(self,coins):
        #receive some money
        return 'value'

from SimpleXMLRPCServer import SimpleXMLRPCServer
class WalletServer (Wallet):

    def __init__(self,issuers,ip="0.0.0.0",port="8000"):
        Wallet.__init__(self,issuers)
        server = SimpleXMLRPCServer((ip, port))
        server.register_function(self.receiveCoins)
        server.serve_forever()





def debug():
    url = 'http://localhost'
    i = Issuer.Issuer(url,[1,2])
    w = Wallet({url:i})
    print w.getBalance()
    w.createCoins([1,1,2],url)
    print w.getBalance()
    return w

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
        


