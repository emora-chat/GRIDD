
from GRIDD.data_structures.id_map_spec import IdMapSpec

from structpy.map import Bimap
from GRIDD.utilities import identification_string


class IdMap(Bimap):

    def __init__(self, items=None, namespace=None, chars=None, start_index=0, condition=None, contains=None):
        Bimap.__init__(self)
        self.namespace = namespace
        self.chars = chars
        self.index = start_index
        self.condition = condition
        self.contains = contains if contains else lambda x: x in self.reverse()
        if items is not None:
            for item in items:
                self.get(item)

    def get(self, item=None):
        namespace = self.namespace if self.namespace is not None else ''
        if item is None:
            if namespace is not int:
                ident = namespace + identification_string(int(self.index), self.chars)
            else:
                ident = self.index
            while self.contains(ident):
                self.index += 1
                if namespace is not int:
                    ident = namespace + identification_string(int(self.index), self.chars)
                else:
                    ident = self.index
            self.index += 1
            return ident
        elif item in self:
            return self[item]
        elif self.condition is None or self.condition(item):
            ident = self.get()
            self[item] = ident
            return ident
        else:
            self[item] = item
            return item

    def identify(self, id):
        return self.reverse()[id] if id in self.reverse() else None


if __name__ == '__main__':
    print(IdMapSpec.verify(IdMap))