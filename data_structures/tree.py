
from GRIDD.data_structures.tree_spec import TreeSpec


class Tree:

    def __init__(self, root, edges=None):
        self._root = root
        self.nodes = {root: {}}
        self._children = {self._root: None}
        for edge in edges:
            self.add(*edge)

    def root(self):
        return self._root

    def has(self, node, child=None, label=None):
        if node not in self.nodes:
            return False
        if child is not None and child not in self.nodes[node]:
            return False
        if label is not None and self.nodes[node][child] != label:
            return False
        return True

    def children(self, node):
        return dict(self.nodes[node])

    def parent(self, node):
        return self._children[node]

    def add(self, parent, child, label=None):
        assert not self.has(child)
        assert self.has(parent)
        self.nodes.setdefault(parent, {})[child] = label
        self._children[child] = parent



if __name__ == '__main__':
    print(TreeSpec.verify(Tree))