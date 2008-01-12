def decodeHumanReadable(text):
    tmp = [line.strip() for line in text.strip().split('\n')]
    tmp = tmp[tmp.index('{')+1:tmp.index('}')]
    tmp = [[e.strip() for e in line.split(' = ')] for line in tmp if line]
    tmp = [[l[0].replace(' ','_'),l[1]] for l in tmp]
    return tmp

def encodeHumanReadable(data):
    out = ['{\n']
    m = max([len(l[0]) for l in data])
    format = (" %%-%ss = %%s" % m)
    for l in data:
        out.append(format % (l[0].replace('_',' '),l[1]))
        out.append('\n')
    out.append('}')
    return ''.join(out)

if __name__=='__main__':
    cdd = """{
     standard version          = http://opencoin.org/OpenCoinProtocol/1.0
     currency identifier       = http://opencent.net/OpenCent
     short currency identifier = OC
     issuer service location   = opencoin://issuer.opencent.net:8002
     denominations             = strlist(1, 2, 5, 10, 20, 50, 100, 200, 500, 1000)  #list of strings seperated by commas
     issuer cipher suite       = HASH-ALG, SIGN-ALG, BLINDING-ALG
     issuer public master key  = base64(pM)

     signature = 02f08dced9c62169af793f70b569ca67
    }""".replace('\n    ','\n')


    data = decodeHumanReadable(cdd)
    print data
    data2 = decodeHumanReadable(encodeHumanReadable(data))
    print cdd
    cdd2 = encodeHumanReadable(data2)
    print cdd2
    print cdd2==cdd

    #tmp['foo'] = dict(dict(foo=1),bar=2)
    import json
    out =  json.write(data)
    print out
    #out = out.replace('","','",\n "')
    #out = out.replace('":"','" : "')
    #print out
    #print json.read(out)







