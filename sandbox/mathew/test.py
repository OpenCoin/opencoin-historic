if __name__=='__main__':
    import crypto
    reload(crypto)
    import merchantwallet
    reload(merchantwallet)
    import consumerwallet
    reload(consumerwallet)
    import issuer
    reload(issuer)
    import dsdb
    reload(dsdb)
    import containers
    reload(containers)

    import entity
    reload(entity)

    universe = entity.UniverseContainer()

    # make a new CDD for our IS
    myCDD = entity.createCDD()

    # verify the self-signed CDD
    if not myCDD.verify_self():
        raise Exception('verification failed')


    import time
    now = int(time.time())
    now = now - (now % 86400)

    mintingKeys = []
    for i in myCDD.denominations:
        mk = entity.createMK(i, myCDD, now - 2*86400, now + 2*86400, now + 3*86400)
        mintingKeys.append(mk)

    dsdb_key = entity.createDSDBCertificate(myCDD, now, now + 10*365*86400)

    print 'we have a CCD, a slew of MintKeys and a DSDBKey!'

    #make the entity for the IS and DSDB
    issuerEntity = entity.IssuerDSDBEntity(myCDD, dsdb_key, mintingKeys)

    #add them to the universe
    universe.addIS(issuerEntity, myCDD.issuer_service_location)
    universe.addDSDB(issuerEntity, dsdb_key.key_identifier)

    #make some coins to put in my wallet
    coinsOne = []
    coinsTwo = []
    for i in mintingKeys:
        for j in range(10):
            if j % 2:
                coinsOne.append(entity.makeCoin(myCDD, i))
            else:
                coinsTwo.append(entity.makeCoin(myCDD, i))

    #make some wallets
    def makeWallet(coins, cddlist, mintingKeys, universe):
        cdds = {}
        for cdd in cddlist:
            cdds[cdd.currency_identifier] = cdd

        return entity.WalletEntity(cdds, mintingKeys, coins, universe=universe)

    walletOierw = makeWallet(coinsOne, (myCDD,), mintingKeys, universe)
    walletNils = makeWallet(coinsTwo, (myCDD,), mintingKeys, universe)

    universe.addMerchantWallet(walletOierw, 'oierw')
    universe.addMerchantWallet(walletNils, 'nils')

    print 'gah! we have coins and wallets too!'

    # test out the entire obfuscation/unobfuscation
    aCoin = coinsOne[0]
    aMK = mintingKeys[0]
    obfuscated = aCoin.newObfuscatedBlank(dsdb_key)
    if not aCoin.validate_with_CDD_and_MintingKey(myCDD, aMK):
        pass
        #raise Exception('Ahh!')
    
    print 'And this is the last thing I expect to work. the spending is broken.'
    walletNils.spendCoins('oierw', coinsTwo[0].currency_identifier, ['1', '1', '5'])

    print 'Wow. we spent. That means I implemented the rest of the work with entities (becuase we have to remove coins from nils, add them to me, etc...)'

    
