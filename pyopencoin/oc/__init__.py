"""
This some playground for me to understand some of the problems involved in getting
our system working.

This is basically taking Mathews ideas (as far as I understood them), adding a bit of 
my little ideas, and coming to the following idea:

- Protocols that are basically state machines (or workflow engines, me is coming
  from a plone background). So you have a protocol, which has a state and can consume messages.

- Messages are little objects that have a type and carry data. They can serialize themselves,
  e.g. to Json.

- Transports, that bascially reflect one side of a communication. They transport messages,
  and are hooked to protocols. A protocol writes to a transport, and the transport stuffs
  new messages into the the protocol when it gets some.

- Entities like Wallets. These will then do things, as triggered by the gui (no gui yet)

Testing is done by using a TestTransport, which basically can be connected to any other
transport (end) to manually communicate with the other side. Check the TestTransport 
for the use of send instead of write!

This alltogether should allow something along the line of:
    >>> from entities import Wallet
    >>> from transports import SimpleTestTransport

    >>> w = Wallet()
    >>> tt = SimpleTestTransport() 
    
    Pass the wallets side transport to the wallet. With sendMoney it will
    immediately start to communicate
    >>> w.sendMoney(tt)

    See, it sends us (we are the other side, pretending to be a wallet
    receiving money) a message. These are no real messages at all
    >>> tt.read()
    <Message('sendMoney',[1, 2])>
    
    Any new messages, after we have been doing nothing?
    >>> tt.read()

    Nope, there weren't. Lets send some nonsense
    >>> tt.send('foobar')
    <Message('Please send a receipt',None)>

    Ok, the protocol does not like other message, but wanted us
    to send a receipt. If it insists...
    >>> tt.send('Receipt')
    <Message('Goodbye',None)>
    
   This was so fun, lets see if we can do some more?
    >>> tt.send('Another receipt')
    <Message('finished',None)>

    Ok, we are done
    
"""

def _test():

    import doctest
    doctest.testmod()
    import protocols, messages, entities, transports, containers
    doctest.testmod(protocols)
    doctest.testmod(messages)
    doctest.testmod(entities)
    doctest.testmod(transports)
    doctest.testmod(containers)
    doctest.testfile("tests.txt",optionflags=doctest.ELLIPSIS)

if __name__ == "__main__":
    _test()
