"""

###############################################################################
Setup an issuer

>>> from issuer import Issuer
>>> issuer = Issuer({})
>>> issuer.createMasterKeys()



issuer sets up "currency description document" = CDD (like a root certificate)

>>> port = 9090
>>> denominations = [0,1,2,5,10,20]
>>> cdd = issuer.makeCDD('OpenCentA','oca',[str(d) for d in denominations],'http://localhost:%s/' % port,'')
>>> issuer.getMasterPubKey().verifyContainerSignature(cdd)
True



###############################################################################
mint (regularily) creates keypairs (pP,sP) for all denominations and id(p). 
Master key holder generates keys certificate

>>> from mint import Mint
>>> mint = Mint({})
>>> mint.setCDD(cdd)
>>> keys = mint.newMintKeys()
>>> mkcs = issuer.signMintKeys(keys=keys,cdd = cdd)
>>> issuer.getMasterPubKey().verifyContainerSignature(mkcs['20'])
True



Wallet fetches cdd from issuer

>>> #faked request
>>> from wallet import Wallet
>>> wallet = Wallet({})
>>> import protocols
>>> cdd == wallet.askLatestCDD(issuer.giveLatestCDD)
True

>>> #using http
>>> import transports
>>> import testserver
>>> transport = transports.HTTPTransport('http://localhost:%s/' % port)
>>> testserver.run_once(port,issuer)
>>> cdd2 = wallet.askLatestCDD(transport)
>>> cdd2.toString(True) == cdd.toString(True)
True



###############################################################################
Wallet: fetches current public minting keys for denomination

>>> testserver.run_once(port,issuer)
>>> mkcs = wallet.fetchMintKeys(transport,denominations=['1','5'])
>>> mkcs[0].toString() == issuer.getCurrentMKCs()['1'].toString()
True



Wallet creates  blank and blinds it

>>> mkc = mkcs[1]
>>> cdd.masterPubKey.verifyContainerSignature(mkc)
True
>>> blank = wallet._makeBlank(cdd,mkc)
>>> blank.denomination == '5'
True
>>> key = mkc.publicKey
>>> secret, blind = key.blindBlank(blank)
>>> tid = wallet.makeSerial()
>>> int(mkc.denomination)
5



###############################################################################
Lets try to get a coin minted

We first need to setup an authorizer, to (surpise) authorize the request. Nils says
the mint should more or less just mint

>>> from authorizer import Authorizer
>>> authorizer = Authorizer({})
>>> authpub = authorizer.createKeys() 
>>> mint.addAuthKey(authpub)
>>> authorizer.setMKCs(mkcs)

Lets have the authorizer denying the request

>>> authorizer.deny = True
>>> testserver.run_once(port,issuer=issuer,mint=mint,authorizer=authorizer)
>>> wallet.requestTransfer(transport,tid,'foo',[[mkc.keyId,blind]],[]).header
'TransferReject'

Now have a well working one

>>> authorizer.deny = False
>>> testserver.run_once(port,issuer=issuer,mint=mint,authorizer=authorizer)
>>> response = wallet.requestTransfer(transport,tid,'foo',[[mkc.keyId,blind]],[])
>>> response.header
'TransferAccept'

And check it

>>> blindsign = response.signatures[0]
>>> blank.signature = key.unblind(secret,blindsign)
>>> coin = blank
>>> key.verifyContainerSignature(coin)
True

We don't have a transport between mint and issuer yet. Lets have the mint
stuff coins directly into the issuer 

>>> mint.addToTransactions = issuer.addToTransactions

The mint can also be a bit slow

>>> mint.delay = True
>>> testserver.run_once(port,issuer=issuer,mint=mint,authorizer=authorizer)
>>> wallet.requestTransfer(transport,tid,'foo',[[mkc.keyId,blind]],[]).header
'TransferDelay'

>>> mint.delay = False

Or the issuer is slow

>>> issuer.delay = True
>>> testserver.run_once(port,issuer=issuer)
>>> wallet.resumeTransfer(transport,tid).header
'TransferDelay'
>>> issuer.delay = False

So we need to resume

>>> testserver.run_once(port,issuer=issuer)
>>> wallet.resumeTransfer(transport,tid).header
'TransferAccept'

And we have a valid coin

>>> blindsign = response.signatures[0]
>>> blank.signature = key.unblind(secret,blindsign)
>>> coin = blank
>>> key.verifyContainerSignature(coin)
True



###############################################################################
Now, wallet to wallet. We setup an alice and a bob side. Alice announces
a sum, and bob dedices if he wants to accept it

>>> alice = wallet
>>> bobport = 9091
>>> bob = Wallet({})
>>> import test
>>> bob.approval = "I don't like odd sums"
>>> alicetid = alice.makeSerial()
>>> alice.announceSum(bob.listenSum, alicetid, 5, 'foobar') 
"I don't like odd sums"

>>> bob.approval = True
>>> wallet.announceSum(bob.listenSum, alicetid, 5, 'foobar') 
True



Wallet Alice sends tokens to Wallet Bob (this time including their clear 
serial and signature)

Lets have first a wrong transactionId
>>> #transport = transports.YieldTransport(bob.run,[])
>>> alice.requestSpend(bob.listenSpend,'foobar',[coin])
Traceback (most recent call last):
    ....
SpendReject: unknown transactionId

Or lets try to send a wrong amount

>>> alice.requestSpend(bob.listenSpend,alicetid,[])
Traceback (most recent call last):
    ....
SpendReject: amount of coins does not match announced one

>>> alice.requestSpend(bob.listenSpend, alicetid, [coin]) 
True



###############################################################################
Now, lets first pretend we are on Bobs side. Fix that later, but assume we 
received the coins, we know what cdd and mkc to use. We need to exchange now

>>> coins = [coin]
>>> key = mkc.publicKey
>>> bobblank = bob._makeBlank(cdd,mkc)
>>> bobsecret, bobblind = key.blindBlank(bobblank)
>>> blinds = [[mkc.keyId,bobblind]]
>>> bobtid = wallet.makeSerial()

>>> testserver.run_once(port,issuer=issuer,mint=mint)
>>> response = bob.requestTransfer(transport,tid,blinds = blinds, coins = coins)
>>> bobblank.signature = key.unblind(bobsecret,response.signatures[0])
>>> bobcoin = bobblank
>>> key.verifyContainerSignature(bobcoin)
True

Lets try to double spend

>>> import messages
>>> bobblank = bob._makeBlank(cdd,mkc)
>>> bobsecret, bobblind = key.blindBlank(bobblank)
>>> blinds = [[mkc.keyId,bobblind]]
>>> bobtid = wallet.makeSerial()
>>> testserver.run_once(port,issuer=issuer,mint=mint)
>>> wallet.requestTransfer(transport,tid,blinds = blinds, coins = coins).header
'TransferReject'



###############################################################################
Last step - bob wants to redeem the coins

>>> bobtid = wallet.makeSerial()
>>> testserver.run_once(port,issuer=issuer,mint=mint)
>>> bob.requestTransfer(transport,tid,target='foo', coins = [bobcoin]).header
'TransferAccept'

"""


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
