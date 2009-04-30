import BaseHTTPServer
import protocols, issuer, mint,authorizer,storage
from testserver import Handler






port = 9090

issuerstorage = storage.Storage().setFilename('data/issuerstorage.bin').restore()
mintstorage = storage.Storage().setFilename('data/mintstorage.bin').restore()
authorizerstorage = storage.Storage().setFilename('data/authorizerstorage.bin').restore()

issuer = issuer.Issuer(issuerstorage)
mint = mint.Mint(mintstorage)
authorizer = authorizer.Authorizer(authorizerstorage)

if not issuerstorage.has_key('masterPrivKey'):
    print 'Issuer: setting up master keys'
    issuer.createMasterKeys()

    print 'issuer: setup currency discription'
    denominations=[0,1,2,5,10,20]
    cdd = issuer.makeCDD('TestCent','tc',[str(d) for d in denominations],'http://192.168.2.101:%s/' % port,'')
    mint.setCDD(cdd)
    
    print 'mint: setting up mintkeys'
    keys = mint.newMintKeys()
    
    print 'issuer: signing mintkeys'
    mkcs = issuer.signMintKeys(keys=keys,cdd = cdd)


    print 'authorizer: creating keys'
    authpub = authorizer.createKeys()

    print 'mint: add authorizer key'
    mint.addAuthKey(authpub)
    print 'authorizer: set mkcs'
    authorizer.setMKCs(mkcs.values()) #FIXME - signMintKeys and fetchMintKeys return different

    print 'saving everything'
    issuerstorage.save()
    mintstorage.save()
    authorizerstorage.save()

print 'Starting up server'
Handler.issuer = issuer
Handler.mint = mint
Handler.authorizer = authorizer
httpd = BaseHTTPServer.HTTPServer(("", port), Handler)
httpd.serve_forever()
