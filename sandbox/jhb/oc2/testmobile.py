import sys
print sys.path
import occrypto as occrypto
(priv,pub) = occrypto.KeyFactory(1024)
text = 'foobar'
secret,blinded = pub.blind(text)
signedblind = priv.signblind(blinded)
signature = pub.unblind(secret,signedblind)
pub.verifySignature(signature,text)
p1 = pub.toString()
p2 = occrypto.PubKey(p1).toString()
p1 == p2

from container import CDD
cdd = CDD()
cdd.issuer_public_master_key = pub
tmp = priv.signContainer(cdd)
print pub.verifyContainerSignature(cdd)

print 'fini'
