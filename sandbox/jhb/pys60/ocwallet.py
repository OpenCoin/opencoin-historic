import appuifw,e32,socket,httplib, urllib
from graphics import *
from key_codes import EKeyLeftArrow, EKeyRightArrow


class WalletClient:

    def __init__(self,wallet):
        self.wallet = wallet
        self.makeWalletMenu()
        self.displayWalletMenu()        
        self.actions=[(u'Send',u'Send coins to someone',self.getDetails),
                      (u'Receive',u'Receive coins',self.getReceiveDetails),
                      (u'Freshen up',u'Freshen up the coins',self.getFreshenUpDetails),
                      (u'Buy',u'Buy new coins',self.getDetails),
                      (u'Sell',u'Sell coins',self.getDetails),
                      (u'Details',u'See what coins you hold',self.inspect),]

        self.methods=[(u'Internet',u'Use the net'),
                      (u'Bluetooth',u'Mobile to mobile')]
        
        self.todo = {}


    def makeWalletMenu(self):
        self.wallet_list = [(u'12 hubtokens',u'the-hub.net'),(u'14 greenbucks',u'opencoin.org')]
        self.wallet_menu =  appuifw.Listbox(self.wallet_list,self.displayActionMenu)
        self.wallet_menu.bind(EKeyRightArrow,self.displayActionMenu)

    def displayWalletMenu(self):
        appuifw.app.body =  self.wallet_menu
        appuifw.app.title = u'opencoin - main\nchoose your currency'

    def displayActionMenu(self):

        action_list = [(action[0],action[1]) for action in self.actions]
        self.action_menu = appuifw.Listbox(action_list,self.selectAction)
        self.action_menu.bind(EKeyRightArrow,self.selectAction)
        self.action_menu.bind(EKeyLeftArrow,self.displayWalletMenu)
        appuifw.app.body = self.action_menu
        appuifw.app.title = u'opencoin - currency\nSelect the action'
        #print 'displayActionMenu'

    def selectAction(self):
        current = self.action_menu.current()
        self.todo['action'] = self.actions[current][0]
        self.actions[current][2]()

    def getDetails(self):
        amount = appuifw.query(u'amount','number')
        self.todo['amount'] = amount

        target = appuifw.query(u'subject','text')
        self.todo['target'] = target

        method = self.getMethod()
        if method ==1:
            url = appuifw.query(u'url','text',u'http://')
            self.todo['url'] = url

        self.execute()

    def getReceiveDetails(self):
        method = self.getMethod()
        if method ==1:
            appuifw.note(u'we are reachable at:','conf')
        self.execute()

    def getFreshenUpDetails(self):
        self.getMethod()
        self.execute()

    def getMethod(self):
        methodlist = [u'mobile to mobile',u'internet']
        method = appuifw.popup_menu(methodlist)
        self.todo['method'] = method
        return method
                              
    def inspect(self):
        #print 'inspect'
        pass
        
    def execute(self):
        #print 'execute'
        print self.todo

#appuifw.app.screen='full'
app_lock = e32.Ao_lock()
w = WalletClient({})
appuifw.app.screen='normal'
appuifw.app.exit_key_handler = app_lock.signal
import time
app_lock.wait()
print 'fini'
