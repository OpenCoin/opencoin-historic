
def tokenizer(denominations,amount):
    denominations.sort()
    tokens = []
    i = 0
    max_i = len(denominations)
    while sum(tokens)<amount:
        if i>=max_i:
            i = max_i -1
        d = denominations[i]
        rest = amount - sum(tokens)
        if d == 1:
            tokens.append(1)
            i +=1
        elif d <= rest-d + denominations[i-1]+1:
            tokens.append(d)
            i +=1
        elif d > rest -d + denominations[i-1]+1:
            i -= 1
    return tokens            

def prepare_for_exchange(denominations,oldcoins,newcoins):
    """returns ([value to keep,..],[value for paying,...],[value for blank,...]),
     assumes that all newcoins are exchanged anyhow"""

    oldcoins = list(oldcoins)
    oldcoins.sort()
    oldcoins.reverse()

    newcoins = list(newcoins)
    newcoins.sort()
    newcoins.reverse()

    amountold = sum([int(o) for o in oldcoins])
    amountnew = sum([int(n) for n in newcoins])
    amount = amountold + amountnew

    targettokens = tokenizer(denominations,amount)
    targettokens.sort()
    targettokens.reverse()
    keepold = []
    makenew = []
    for tt in targettokens:
        try:
            keepold.append(oldcoins.pop(oldcoins.index(tt)))
        except ValueError:
            makenew.append(tt)
                
    return (keepold,oldcoins,makenew)            


def testspend(tokens,amount):
    picked = []
    tokens.sort()
    tokens.reverse()
    for token in tokens:
        rest = amount - sum(picked)
        if rest > 0 and token <= rest:
            picked.append(token)
    return picked         


def test_tokenizer():
    problems = 0
    for denominations in dl:
        print 'DENOMINATIONS %s' % denominations
        print
        for i in range(1,max(denominations)*3):
            print 'Tokenize %i, ' % i,
            tokens = tokenizer(denominations,i)
            print 'tokens %s (%s)' % (tokens,sum(tokens))
            if sum(tokens) != i:
                print 'fuckup'
                break;
            for j in range(1,i+1):
                picked = testspend(tokens,j)
                if sum(picked) != j:
                    problems += 1
                    print 'testing: %s, picked %s, sum %s, worked: %s' % (j,picked,sum(picked),sum(picked)==j)
    print
    print
    print 'Problems: %s' % problems
                    
    amount = 137
    print tokenizer(dl[0],amount)

def test_prepare_for_exchange():
    denominations = dl[0]
    startvalue = max(denominations)
    for i in range(1,startvalue * 2 +1):
        print '#'*20,' i: %s ' % i, '#' * 20
        start = tokenizer(denominations,i)
        for j in range(1,i*3 +1):
            print 'j: %s - ' % j,
            newcoins = tokenizer(denominations,j)
            keepold,paywith,makenew = prepare_for_exchange(denominations,start,newcoins)
            sumkeep = sum(keepold)
            sumnew = sum(makenew)
            total = sumkeep + sumnew
            print "keep: %s, tomake: %s, paywith: %s, %s, sum: %s" % (keepold,makenew,paywith,newcoins,total)

if __name__ == '__main__':
    
    dl = [[1,2,5,10,20,50,100],[1,3,9,27],[1,3,5,7,11,13,17,19,23],[1,17,33]]
    #test_tokenizer()
    #test_prepare_for_exchange() 
    print "keep: %s, paywith: %s, makenew: %s" %prepare_for_exchange(dl[0],[10],[5,2])




