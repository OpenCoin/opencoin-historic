import UserDict, cPickle
class Storage(UserDict.UserDict):

    def setFilename(self,filename):
        self.filename = filename
        return self

    def save(self):
        cPickle.dump(self.data,open(self.filename,'w'))
        return self

    def restore(self):
        try:
            self.data = cPickle.load(open(self.filename))
        except:            
            pass
        return self

