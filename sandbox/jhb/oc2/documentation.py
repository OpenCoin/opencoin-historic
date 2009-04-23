"""
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 

      This is just a todo for jhb, and not the real spec

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 

OpenCoin Project                                            N. Toedtmann
http://opencoin.org/                                         J. H. Baach
Category: Draft                                                 M. Ryden

                      OpenCoin Formats and Protocol

Status of this Memo

   This draft is work in heavy progress. Do not consider it's content
   stable in any sense as long as this note is present. Get in touch
   with opencoin.org [1] and fetch a recent copy [2].
   

Copyright Notice

   Copyright (c) N. Toedtmann, J. H. Baach, M. Ryden (2008).


Abstract

   This document describes the OpenCoin protocol which seeks to
   implement David Chaum's concept of "untraceable payments" [3].


ToDo

   - licence of this document (GNU FDL, CC-BY-SA, Public Domain)?
   - "Introduction", including scope of protocol
   - JSON, 7-bit ASCII
   - define token/certificate format, encryption padding
   - define validity of certificates and tokens
   - add note on randomness
   - add PROTOCOL_ERROR
   - add HANDSHAKE, CONTINUE, GOODBYE; warning that GOODBYE will disappear
   - throw out reduntant "TRANSFER_TOKEN" explanatoins
   - add authentication and authorization, at least for "target"
     when minting
   - add mandatory trusted channel (Bluetooth, TLS)
   - reformat this into RFC-XML
   - add warning on differences to scientific notation


Table of Contents

   1. Introduction
      1.1  Object of the OpenCoin protocol
      1.2  Limited scope of the OpenCoin protocol
      1.3  General Layout of the OpenCoin protocol
      1.4  Encoding of messages, tokens and certificates
   2. General guidelines
   3. The OpenCoin protocol
      3.1.  Issuer setup
      3.2.  Wallet setup
      3.3.  Wallet creates blanks
      3.3.5."TRANSFER_TOKEN": A generic wallet-issuer request
      3.4.  Wallet send minting request to issuer  
      3.5.  Wallet gets token back
      3.6.  Wallet to wallet
      3.7.  Redeeming tokens
   4. References


1. Introduction

1.1 Object of the OpenCoin protocol

The OpenCoin protocol aims to implement David Chaum's concept of "untraceable 
payments" [3]. The general procedure is this:

* Minting
  * A payer creates a yet unsigned, 'blank' token according to the rules 
    published by the issuer. It includes a serial number.
  * He obfuscates this blank, yielding the 'blind'. He send the blind to the
    issuer and request signing with a special minting key.
  * If the issuer's requirements for minting (which may include a payment) 
    are met, he signs the payer's  blind with the nominated minting key.
  * The payer fetches the signed blind from the issuer and 'unblinds'. The 
    result is a token including a valid signature from the issuer.

* Spending
    A payer sends the token to a payee. The payee verifies that the token is
    valid according to the issuer's rules (format, data, signature, ...). In
    the standard online case, he also checks it against the issuer's double 
    spending database (DSDB). He tells the payer if he accepts the token.

* Redemption
    The payee sends the token to the issuer. The issuer verifies that the 
    token is valid and checks it against his DSDB. If he accepts the token, 
    he adds its serial number to the DSDB. He may offer the payee something 
    in exchange for the token (like a payment).

In the standard case of online payment, spending and redemption are actually 
entwined to one simultanious operation.

Tokens include a reference to this protocol, a reference to the issuer, a 
denomination, a random serial and the mint's signature over this data. The
minting key used to sign the token is deticated to mint exclusivly tokens 
of this denomination.

This protocol is designed such that tokens are unforgable and untracable:

* Unforgeability/balance
  Without knowledge of the issuer's private minting keys, no combination of 
  payers and payees can successfully redeem tokens of a total denomination 
  higher than the total denomination of tokens minted by the issuer for them. 
  In Particular, no one (except the issuer) can produce N+1 valid tokens 
  from N valid tokens ('one-more-forgery').

* Untraceability
  No combination of the issuer and a set of payees are able to correlate 
  blinds and tokens of a payer just by looking at them (but maybe by traffic
  analysis).


1.2 Limited scope of the OpenCoin protocol

[ToDo]


1.3 General Layout of the OpenCoin protocol

The OpenCoin protocol typically involves three parties: the issuer, a sender/
payer (Alice) and a receiver/payee (Bob). We call the OpenCoin user agents of 
payer and payee 'wallets'. The issuer consists of four parts:
* The 'master key holder' (MHK) generates and keeps the master key pair 
  and signes and publishes the 'currency description document' (CDD) and 
  all the certificates.
* The mint generates and keeps the minting keys and signes blinds.
* The 'double spending database' (DSDB) keeps track of the serials of 
  tokens which got redeemed.
* The 'issuer service' (IS) is the public interface of the issuer on the
  internet.

The participants send each other messages in request/response pairs. The 
universal scheme is this:

     * session initiation *

   -- [ HANDSHAKE, DATA ] -->
  <-- [ HANDSHAKE, null ] --

   -- [ REQUEST_1, DATA ] -->
  <-- [ RESPONSE_1,DATA ] --

   -- [ REQUEST_2, DATA ] -->
  <-- [ RESPONSE_2,DATA ] --

   -- [ CONTINUE,  null ] -->
  <-- [ CONTINUE,  null ] --

          * pause *

   -- [ REQUEST_3, DATA ] -->
  <-- [ RESPONSE_3,DATA ] --

   -- [ REQUEST_4, DATA ] -->
  <-- [ RESPONSE_4,DATA ] --

   -- [ GOODBYE,   null ] -->
  <-- [ GOODBYE,   null ] --

     * session termination *

The standard case involves three sessions:

   Payer Alice  --[minting]--------------------------------->  Issuer
   Payer Alice  --[spending]-->  Payee Bob  --[redemption]-->  Issuer

the latter two usually happening at the same time ('online case').


1.4 Encoding of messages, tokens and certificates

[ToDo]



2. General guidelines

[ToDo]


3. The OpenCoin protocol
 
3.1 Issuer setup

* issuer generates master key pair (ALG,pM,sM)
###############################################################################

>>> from storage import Item
>>> from issuer import Issuer
>>> issuer = Issuer({})
>>> issuer.createMasterKeys()

###############################################################################

* issuer sets up "currency description document" = CDD (like a root certificate)

   {
     standard version             = http://opencoin.org/OpenCoinProtocol/1.0
     currency identifier          = http://opencent.net/OpenCent
     short currency identifier    = OC 
     issuer service location      = opencoin://issuer.opencent.net:8002
     denominations                = strlist(1, 2, 5, 10, 20, 50, 100, 200, 500, 1000)  #list of strings seperated by commas
     issuer cipher suite          = HASH-ALG, SIGN-ALG, BLINDING-ALG
     issuer public master key     = base64(pM)
     
     issuer                       = base64(hash(pM))
     base64(sig(sM,hash(content part)))
   }

   (question: is the "short currency identifier" needed?)
   (question: "not use after")
   (future: add additionial signatures, e.g. from wallet software vendors (set up in containers already))


###############################################################################

>>> port = 9090
>>> denominations = [0,1,2,5,10,20]
>>> cdd = issuer.makeCDD('OpenCentA',
...                      'oca',
...                      [str(d) for d in denominations],
...                      'http://localhost:%s/' % port,
...                      '')
>>> issuer.getMasterPubKey().verifyContainerSignature(cdd)
True

###############################################################################


* issuer publishes CDD at "currency identifier" URL

* mint (regularily) creates keypairs (pP,sP) for all denominations and id(p).
  Master key holder generates keys certificate

  {
    key identifier      = base64(hash(pP))
    currency identifier = http://opencent.net/OpenCent
    denomination        = denomination
    not_before          = TIME(...)
    key_not_after       = TIME(...)
    token_not_after      = TIME(...)
    public key          = base64(pP)

    issuer              = base64(hash(pM))
    base64(sig(sM, hash(content part)))
  }


###############################################################################

>>> from mint import Mint
>>> mint = Mint({})
>>> mint.setCDD(cdd)
>>> keys = mint.newMintKeys()
>>> mkcs = issuer.signMintKeys(keys=keys,cdd = cdd)
>>> issuer.getMasterPubKey().verifyContainerSignature(mkcs['20'])
True

###############################################################################

  
  Questions:
  * CDD?

* issuer fires up issuer service (=IS) at <opencoin://issuer.opencent.net:8002>


3.2 Wallet setup

* fetch "currency description document" from issuer

###############################################################################

>>> #faked request
>>> from wallet import Wallet
>>> wallet = Wallet({})
>>> import protocols
>>> serverside = protocols.GiveLatestCDD(issuer)
>>> clientside = protocols.AskLatestCDD(serverside.run)
>>> cdd == clientside.run()
True

>>> #using http
>>> import transports
>>> import testserver
>>> transport = transports.HTTPTransport('http://localhost:%s/' % port)
>>> clientside = protocols.AskLatestCDD(transport)
>>> testserver.run_once(port,issuer)
>>> cdd2 =  clientside.run()
>>> cdd2.toString(True) == cdd.toString(True)
True

###############################################################################


3.3 Wallet creates blanks

* Wallet: fetches current public minting keys for denomination

Wallet:
    MINTING_KEY_FETCH_DENOMINATION(denomination) or MINTING_KEY_FETCH_KEYID(key_id)
IS:
    MINTING_KEY_PASS(keycertificate) or MINTING_KEY_FAILURE(reason)

###############################################################################

>>> clientside = protocols.FetchMintKeys(transport,denominations=['1','5'])
>>> testserver.run_once(port,issuer)
>>> mkcs =  clientside.run()
>>> mkcs[0].toString() == issuer.getCurrentMKCs()['1'].toString()
True

###############################################################################

* Wallet: creates blank according to CDD:

  {
      standard identifier = http://opencoin.org/OpenCoinProtocol/1.0
      currency identifier = http://opencent.net/OpenCent 
      denomination        = denomination
      key identifier      = key_id(signing key)
      serial              = base64(128bit random number)
  }

#XXX: ist key id wirklich vom secret key, oder vom public key?


* Wallet: create random r, calculate 

    blind = blinding(r, pub_minting_key, hash(blank))
 
  Calculate a collision-free random transaction ID (128 bit)

  Keep (r, blank, blind) in mind. 
  
###############################################################################

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


3.3.5 "TRANSFER_TOKEN": A generic wallet-issuer request

The atom for this transaction is a list of tokens - if one of the tokens /blanks
fail, the whole transaction fails.

* Client sends
   
        TRANSFER_TOKEN_REQUEST( 
            transaction_id, target, list_of_blinds+keyids, 
            list_of_tokens, list_of_options )

  [ WARNING: In future versions of this protocol, it wll change to
        TRANSFER_TOKEN_REQUEST (
            transaction_id, list_of_options,
            target, list_of_blinds+keyids, list_of_tokens )
  ]

  to IS (issuer service), where 

  * transaction_id is a base64(random(128bit)) referencing this transaction
    e.g. for later resume after an abort.
  * list_of_option may contain variable=value pairs like "JITM=mandatory".
    It must contain the option "type", which can have three values:
    * mint    : A minting request. target is a payment reference, 
                list_of_tokens must be empty.
    * redeem  : A token redemption. target is an account reference,
                list_of_blinds+keyids must be empty.
    * exchange: A request to mint new tokens for old ones. target must be 
                empty, value of blinds must equal value of tokens.

  If at least one of the blinds or tokens is rejected, the issuer answers

        TRANSFER_TOKEN_REJECT( 
            transaction_id, reason,
            list( (blind1.key_id, reason1), ... ),
            list( (token1.key_id,  reason1), ... )  )

  where "reason" may be some general failure like "500 minting not available".
  If the request is accepted with no delay, IS answers

        TRANSFER_TOKEN_ACCEPT( 
            transaction_id, message, list_of_signed_blinds)

  (with list_of_singed_blinds empty if no minting was required)
  If minting was requested and acccepted but postponed, IS answers

        TRANSFER_TOKEN_DELAY( transaction_id, message )

  In this case, the wallet can fetch the signed blinds later by 

        TRANSFER_TOKEN_RESUME( transaction_id )


3.4 Wallet send minting request to issuer  

* Send

        TRANSFER_TOKEN_REQUEST( transaction_id, target, 
            list_of_blinds+keyids, (empty list) , list_of_options, )

  to issuer service
  
  
###############################################################################

We first need to setup an authorizer, to (surpise) authorize the request. Nils says
the mint should more or less just mint

>>> from authorizer import Authorizer
>>> authorizer = Authorizer({})
>>> authpub = authorizer.createKeys() 
>>> mint.addAuthKey(authpub)
>>> authorizer.setMKCs(mkcs)
>>> clientside = protocols.TransferRequest(transport,tid,'foo',[[mkc.keyId,blind]],[])

###############################################################################

* Issuer: if request will not be minted (e.g., "Bad Key ID" if the key_id
  is not current):

        TRANSFER_TOKEN_REJECT( transaction_id, reason,
            list( (blind1.key_id, reason1), ... ), (empty list1)  )
        
###############################################################################
>>> import time
>>> time.sleep(1)
>>> authorizer.deny = True
>>> testserver.run_once(port,mint=mint,authorizer=authorizer)
>>> clientside.run().header
'TransferReject'


###############################################################################

  ElseIf minting is done just-in-time, IS answers

        TRANSFER_TOKEN_ACCEPT( transaction_id, message, list_of_signed_blinds)

###############################################################################

>>> authorizer.deny = False
>>> testserver.run_once(port,mint=mint,authorizer=authorizer)
>>> response = clientside.run()
>>> response.header
'TransferAccept'
>>> blindsign = response.signatures[0]
>>> blank.signature = key.unblind(secret,blindsign)
>>> coin = blank
>>> key.verifyContainerSignature(coin)
True

We don't have a transport between mint and issuer yet. Lets have the mint
stuff coins directly into the issuer 

>>> mint.addToTransactions = issuer.addToTransactions


###############################################################################

  Else IS queues blind to the mint and tells wallet to wait

        TRANSFER_TOKEN_DELAY( transaction_id, reason )


###############################################################################

>>> mint.delay = True
>>> testserver.run_once(port,mint=mint,authorizer=authorizer)
>>> clientside.run().header
'TransferDelay'
>>> mint.delay = False

###############################################################################


  Session is terminated.


  In case of delayed minting, mint processes request (signs blind with key_id)
  some time later and passes "signed blind"="blind token" back to IS 







3.5 Wallet gets token back

* Wallet asks issuer service

        TRANSFER_TOKEN_RESUME( transaction_id )

* IS either rejects finally

        TRANSFER_TOKEN_REJECT( transaction_id, reason,
            list( (blind1.key_id, reason1), ... ), (empty list) )
 
  with reasons like "TID Unknown", "TID expired", "TID rejected", ...,
  or tells to wait longer

        TRANSFER_TOKEN_DELAY( transaction_id, reason )

###############################################################################

>>> issuer.delay = True
>>> clientside = protocols.TransferResume(transport,tid)
>>> testserver.run_once(port,issuer=issuer)
>>> clientside.run().header
'TransferDelay'
>>> issuer.delay = False

###############################################################################

  (question: what about key expiration while request is in mining queue)
  (oierw thinks: as long as the key is valid for minting when the request is made, we are good)

  or passes signed blinds to wallet Bob, must preserve order

        TRANSFER_TOKEN_ACCEPT( transaction_id, message, list_of_singed_blinds )
   

###############################################################################

>>> clientside = protocols.TransferResume(transport,tid)
>>> testserver.run_once(port,issuer=issuer)
>>> response = clientside.run()
>>> response.header
'TransferAccept'

###############################################################################

  Session terminates

* wallet checks if blind fits request id and if blind was correctly signed. 
  If not, delete blind and inform user (optional: inform issuer about error)
  (optional: if yes, inform issuer that he may delete the request)

* Wallet unblinds signed blind and yields token  (or reblinds)

###############################################################################

>>> blindsign = response.signatures[0]
>>> blank.signature = key.unblind(secret,blindsign)
>>> coin = blank
>>> key.verifyContainerSignature(coin)
True

###############################################################################


3.6 Wallet to wallet

Alice - sends a token
Bob   - receives the token

  [ Warning: 
    The messages "SPEND_TOKEN_*" may get exchanged by "TRANSFER_TOKEN_*" of 
    type "redeem" or "spend" in future versions of this protocol. ]

* Prerequisites
  * Wallet Alice locates Wallet Bob and sets up (secure) connection
  * Alice knows how much to send and tells her Wallet
  * Wallet Alice calculates a splitting of sum into tokens (units)
    and reates a list of tokens to send
  * Wallet Alice and Wallet Bob are synchronized to UTC (within some small 
    margin of error)


* [ToDo] Handshake


* Wallet Alice announces sum of tokens she wishes to spend for a certain
  prupose=target, wallet Bob decides if it is going to accept them:

    A:      SUM_ANNOUNCE( transaction_id, sum, target )
    B:      SUM_ACCEPT( transaction_id )
        or  SUM_REJECT( transaction_id, "Reason" )

###############################################################################

>>> bobport = 9091
>>> bobwallet = Wallet({})
>>> import test
>>> alicetid = wallet.makeSerial()
>>> bob = protocols.SumAnnounceListen(bobwallet)
>>> alice = protocols.SumAnnounce(bob.run, wallet, alicetid, 5, 'foobar') 
>>> bobwallet.approval = "I don't like odd sums"
>>> alice.run()
"I don't like odd sums"

>>> bobwallet.approval = True
>>> alice.run()
True

###############################################################################

* Wallet Alice sends tokens to Wallet Bob (this time including their clear 
  serial and signature)
  
    A:      SPEND_TOKEN_REQUEST( transaction_id, list(token1, ...) )

* The atom for a SPEND_TOKEN_REQUEST is the entire list of tokens

* Wallet Bob checks if the sum of their values matches the announced sum, if 
  they are valid and (if the former tests do not fail) tries itself to spent
  the tokens at the issuer with a TRANSFER_TOKEN_REQUEST of type "redeem" or
  "exchange", using a new, different transaction_id. If one of these fail,
  wallet Bob rejects the request it with a reason/reasons, otherwise accepts
  them:

    B:      SPEND_TOKEN_REJECT( transaction_id, list( (tokenN, "ReasonN") ) )
        or  SPEND_TOKEN_REJECT( transaction_id, emptylist, "Reason")
        or  SPEND_TOKEN_ACCEPT( transaction_id )

  Possible reasons are "unknown", "invalid" ... [ToDo].

  In case of rejection, wallet Alice itself should immediatly exchange these 
  tokens at the issuer as an emergancy countermeasure against token theft.

  In case of acceptance, wallet Alice must delete all instances of the spent
  tokens.

###############################################################################

>>> bob = protocols.SpendListen(bobwallet)
>>> #transport = transports.YieldTransport(bob.run,[])
>>> alice = protocols.SpendRequest(bob.run, wallet, 'foobar', [coin]) 
>>> alice.run()
Traceback (most recent call last):
    ....
SpendReject: unknown transactionId

>>> alice = protocols.SpendRequest(bob.run, wallet, alicetid, []) 
>>> alice.run()
Traceback (most recent call last):
    ....
SpendReject: amount of coins does not match announced one

>>> alice = protocols.SpendRequest(bob.run, wallet, alicetid, [coin]) 
>>> alice.run()
True

Now, lets first pretend we are on Bobs side. Fix that later, but assume we 
received the coins, we know what cdd and mkc to use. We need to exchange now

>>> coins = [coin]
>>> key = mkc.publicKey
>>> bobblank = bobwallet._makeBlank(cdd,mkc)
>>> bobsecret, bobblind = key.blindBlank(bobblank)
>>> blinds = [[mkc.keyId,bobblind]]
>>> bobtid = wallet.makeSerial()

>>> clientside = protocols.TransferRequest(transport,tid,blinds = blinds, coins = coins)
>>> testserver.run_once(port,issuer=issuer,mint=mint)
>>> response = clientside.run()
>>> bobblank.signature = key.unblind(bobsecret,response.signatures[0])
>>> bobcoin = bobblank
>>> key.verifyContainerSignature(bobcoin)
True




###############################################################################

3.7 Redeeming tokens 

* Wallet sends tokens + target to IS

    W:  TRANSFER_TOKEN_REQUEST(
            transaction_id, list_of_options, target, (empty list), list_of_tokens 
        )

  target may be an account and is of the form:

        MINT_REQUEST=#base64(request_id)
        ONLINE_BANKING_ACCOUNT=#string(account_identifier)
        and so on... to be defined with relationship between IS and individual


* IS checks if tokens and target are valid
    - if minting keys are still valid (XXX token has not expired)
    - if serial is still valid (against DSDB)
    - if signature is valid

  If not, IS rejects with reason (key id unknown, token outdated, token spent, 
  signature invalid) per token or sweeping

    IS: TRANSFER_TOKEN_REJECT( 
            transaction_id, reason, (empty list), list( (token1.key_id,  reason1), ... )  )
        )

  If tokens and target are valid, IS enters the serials of the tokens into the
  DSDB, servers the target and replies

    IS: TRANSFER_TOKEN_ACCEPT( 
            transaction_id, message, (empty list)
        )


4. References

[1]         The OpenCoin project <http://opencoin.org/>

[2]         The OpenCoin project, "OpenCoin protocol v1.0"
            <https://trac.opencoin.org/trac/opencoin/browser/trunk/standards/protocol.txt>

[3]         David Chaum, "Blind signatures for untraceable payments", Advances
            in Cryptology - Crypto '82, Springer-Verlag (1983), 199-203.

[RFC4086]   D. Eastlake, J. Schiller and S. Crocker, "Randomness Requirements 
            for Security", RFC 4086, June 2005

[RFC4627]   D. Crockford, "The application/json Media Type for JavaScript 
            Object Notation (JSON)", RFC 4627, July 2006
"""


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
