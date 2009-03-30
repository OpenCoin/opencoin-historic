r"""
>>> from storage import Item
>>> from issuer import Issuer
>>> issuer = Issuer(Item())
>>> issuer.createMasterKeys()
>>> cdd = issuer.makeCDD('OpenCentA',
...                      'oca',
...                      [str(d) for d in [0,1,2,5,10,20]],
...                      'http://localhost:8000',
...                      '')
>>> issuer.getMasterPubKey().verifyContainerSignature(cdd)
True
>>> issuer.getCDD('oca') == cdd
True

>>> from mint import Mint
>>> mint = Mint(Item())
>>> mint.setCDD(cdd)
>>> keys = mint.newMintKeys()
>>> mkcs = issuer.signMintKeys('oca',keys=keys,cdd = cdd)
>>> issuer.getMasterPubKey().verifyContainerSignature(mkcs['20'])
True
"""


if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
