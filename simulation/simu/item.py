import utils

class Item:
    def __init__(self, size: utils.Size):
        self._size = size
        self._name = f"item_{size.name.lower()}_{size.value}"

    def __eq__(self, other):
        return self._size == other.get_size()

    def get_name(self):
        return self._name
    
    def get_size(self):
        return self._size

    def __repr__(self):
        return "Item size %s" % self._size
