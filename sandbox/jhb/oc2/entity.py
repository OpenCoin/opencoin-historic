import occrypto,container
from storage import Item

class Entity(object):
    
    def __init__(self,storage=None):
        self.storage = storage

    def get(self,key,default=None):
        return getattr(self.storage,key,default)
    
    def has(self,key):
        return hasattr(self.storage,key)

    def set(self,key,value):
        return setattr(self.storage,key,value)
