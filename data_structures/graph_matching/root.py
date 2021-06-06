
class Root:
    def __str__(self):
        return 'ROOT'
    def __repr__(self):
        return str(self)

class RootedEdge:
    def __str__(self):
        return 'ROOTEDGE'
    def __repr__(self):
        return str(self)

root = Root()
rooted_edge = RootedEdge()