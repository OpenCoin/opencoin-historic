
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

def testspend(tokens,amount):
    picked = []
    tokens.sort()
    tokens.reverse()
    for token in tokens:
        rest = amount - sum(picked)
        if rest > 0 and token <= rest:
            picked.append(token)
    return picked         

if __name__ == '__main__':
    dl = [[1,2,5,10,20,50,100],[1,3,9,27],[1,3,5,7,11,13,17,19,23],[1,17,33]]
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
