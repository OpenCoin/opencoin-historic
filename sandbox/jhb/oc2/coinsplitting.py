
def tokenizer(denominations,amount):
    denominations.sort()
    tokens = []
    i = 0
    while sum(tokens)<amount:
        d = denominations[i]
        rest = amount - sum(tokens)
        if d == 1:
            #print 'append %s' % d
            tokens.append(1)
            i +=1
        elif d <= rest-d:
            #print 'append %s' % d
            tokens.append(d)
            i +=1
        elif d > rest -d:
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

denominations = [1,2,5,10,20,50,100,200,500]    
problems = 0
for i in range(1,max(denominations)+1):
    print 'Tokenize %i, ' % i,
    tokens = tokenizer(denominations,i)
    print 'tokens %s (%s)' % (tokens,sum(tokens))
    
    for j in range(1,i+1):
        picked = testspend(tokens,j)
        if sum(picked) != j:
            problems += 1
            print 'testing: %s, picked %s, sum %s, worked: %s' % (j,picked,sum(picked),sum(picked)==j)
print
print
print 'Problems: %s' % problems
                

