from collections import defaultdict

class SpanningNode:

    def __init__(self, node_id, parent, pred_type=None, type=None):
        self.node_id = node_id
        self.pred_type = pred_type
        self.type = type
        self.children = defaultdict(list)
        self.parent = parent

    def equal(self, n):
        if self.node_id != n.node_id or self.type != n.type: return False
        if set(self.children.keys()) != set(n.children.keys()): return False
        all_found = True
        for key, children in self.children.items():
            n_children = n.children[key]
            if len(children) != len(n_children): return False
            options = list(n_children)
            for c in children:
                found = False
                for nc in options:
                    if c.equal(nc):
                        found = True
                        options.remove(nc)
                        break
                if not found:
                    break
            if len(options) != 0:
                all_found = False
                break
        return all_found

    def __str__(self):
        if self.type is not None:
            return f"{self.type}-{self.node_id}"
        else:
            return self.node_id

    def __repr__(self):
        return str(self)