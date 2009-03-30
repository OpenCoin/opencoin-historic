import pickle,base64
class Item(object):
    
    def dump(self,path):
        return base64.b64encode(pickle.dumps(self))

    def load(self,path):
        return pickle.loads(base64.decode(open(path).read()))
