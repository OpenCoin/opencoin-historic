r"""
>>> import occrypto as occrypto
>>> (priv,pub) = occrypto.KeyFactory(1024)
>>> text = 'foobar'
>>> secret,blinded = pub.blind(text)
>>> signedblind = priv.signblind(blinded)
>>> signature = pub.unblind(secret,signedblind)
>>> pub.verifySignature(signature,text)
True
>>> sig2 = priv.sign('foobar')
>>> pub.verifySignature(sig2,'foobar')
True
"""
"""

>>> from container import Token
>>> t = Token()
>>> t.currency='opencent'
>>> t.amount = 2
>>> t.toString()
'[["currency", "opencent"], ["amount", 2]]'
>>> t.toString(True)
'[["currency", "opencent"], ["amount", 2], ["signature", ""]]'
>>> t.getData()
[('currency', 'opencent'), ('amount', 2)]
>>> t2 = Token(t.getData())
>>> t2.getData()
[('currency', 'opencent'), ('amount', 2)]
>>> t.signature = 'mysignature'
>>> t.toString(True)
'[["currency", "opencent"], ["amount", 2], ["signature", "mysignature"]]'

>>> from container import Message
>>> m = Message()
>>> m.subject = 'test'
>>> m.tokens = [t,t2]
>>> m.toString()
'[["subject", "test"], ["tokens", [[["currency", "opencent"], ["amount", 2]], [["currency", "opencent"], ["amount", 2]]]]]'
>>> m.getData()
[('subject', 'test'), ('tokens', [[('currency', 'opencent'), ('amount', 2)], [('currency', 'opencent'), ('amount', 2)]])]
>>> m2 = Message(m.getData())
>>> m2.getData() == m.getData()
True
>>> m2.toString() == m2.toString()
True

"""



if __name__ == "__main__":
    import doctest
    doctest.testmod(optionflags=doctest.ELLIPSIS)
