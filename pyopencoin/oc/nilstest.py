from entities import Wallet, Issuer
from transports import ServerTestTransport, ClientTest
import tests
walletA = Wallet()
walletA.coins = [tests.coinB]

walletB = Wallet()
issuer = tests.makeIssuer()
t = ClientTest(walletB.listen,
                clientnick='walletA',
                autocontinue=1,
                autoprint='json',
                servernick='walletB')
t2 = ClientTest(issuer.listen,
                clientnick='walletB',
                autocontinue=1,
                autoprint='json',
                servernick='issuer')

walletB.issuer_transport = t2
walletA.sendCoins(t,amount=1,target='a book')





