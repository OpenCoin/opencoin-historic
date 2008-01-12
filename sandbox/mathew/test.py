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
    walletPoor = makeWallet([], (myCDD,), [], universe)

    universe.addMerchantWallet(walletOierw, 'oierw')
    universe.addMerchantWallet(walletNils, 'nils')
    universe.addMerchantWallet(walletPoor, 'poor')

    # test out the entire obfuscation/unobfuscation
    aCoin = coinsOne[0]
    aMK = mintingKeys[0]
    obfuscated = aCoin.newObfuscatedBlank(dsdb_key)
    if not aCoin.validate_with_CDD_and_MintingKey(myCDD, aMK):
        pass
    
    # test out blinding/unblinding
    aCoin = coinsOne[0]
    aMK = mintingKeys[0]
    aBlind = containers.CurrencyBlank(aCoin.standard_identifier, aCoin.currency_identifier, aCoin.denomination, aMK.key_identifier)
    aBlind.generateSerial()
    aBlind.blind_blank({myCDD.currency_identifier: myCDD}, {aMK.key_identifier: aMK})
    aBlindValue = aBlind.blind_value

    aSigning = myCDD.issuer_cipher_suite.signing.__class__(aMK.public_key)
    aBlindedSignature = aSigning.sign(aBlindValue)

    aSignature = aBlind.unblind_signature(aBlindedSignature)
    aNewCoin = aBlind.newCoin(aSignature, myCDD, aMK)

    walletNils.spendCoins('oierw', coinsTwo[0].currency_identifier, ['1', '1', '5'])

    # give a cent to the poor
    walletOierw.spendCoins('poor', coinsOne[0].currency_identifier, ['1'])
    
    # and now the poor is sneaky
    doubleCoin = walletPoor.coins[0]
    walletPoor.spendCoins('poor', coinsOne[0].currency_identifier, ['1'])
    walletPoor.coins.append(doubleCoin) # add the original coin and try to double spend it
    walletPoor.spendCoins('poor', coinsOne[0].currency_identifier, ['1', '1']) # spend both coins to make sure we include it

    
