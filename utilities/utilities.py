
from math import log
import os
from inspect import getmembers, isfunction

CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def _get_digit(x, i, n=10):
    return x // n**i % n

def _get_num_digits(x, n=10):
    if x > 0:
        digits = int(log(x, n)) + 1
    elif x == 0:
        digits = 1
    else:
        digits = int(log(-x, n)) + 2
    return digits

def identification_string(x, chars=None):
    string = ''
    if chars is None:
        chars = '0123456789'
    n = len(chars)
    for i in range(_get_num_digits(x, n)):
        d = _get_digit(x, i, n)
        string = chars[d] + string
    return string

def collect(*files_folders_or_strings, extension=None, directory=None):
    collected = []
    files_or_strings = []
    for ffs in files_folders_or_strings:
        if isinstance(ffs, str) and os.path.isdir(ffs):
            for fs in os.listdir(ffs):
                if not extension or fs.endswith(extension):
                    files_or_strings.append(os.path.join(ffs, fs))
        else:
            files_or_strings.append(ffs)
    for ffs in sorted(files_or_strings):
        if not extension or (isinstance(ffs, str) and ffs.endswith(extension)):
            with open(ffs, 'r') as f:
                collected.append(f.read())
        else:
            collected.append(ffs)
    return collected

class hashabledict(dict):
  def __key(self):
    return tuple((k,self[k]) for k in sorted(self))
  def __hash__(self):
    return hash(self.__key())
  def __eq__(self, other):
    self_id = self.__key()
    other_id = other.__key()
    return self_id == other_id

class Counter:
    def __init__(self, value=0):
        self.value = value
    def __iadd__(self, other):
        self.value += other
        return self
    def __int__(self):
        return self.value

def uniquify(collection):
    ids = {}
    for item in collection:
        ids[id(item)] = item
    return list(ids.values())

def combinations(*itemsets):
    c = [[]]
    for itemset in list(itemsets):
        if itemset:
            cn = []
            for item in list(itemset):
                ce = [list(e) for e in c]
                for sol in ce:
                    sol.append(item)
                cn.extend(ce)
            c = cn
    return c

def operators(module):
    d = dict(getmembers(module, isfunction))
    for v in list(d.values()):
        if hasattr(v, 'aliases'):
            for alias in v.aliases:
                d[alias] = v
    return {k: v for k, v in d.items() if not k.startswith('_')}

class aliases:
    def __init__(self, *aliases):
        self.aliases = aliases
    def __call__(self, fn):
        fn.aliases = self.aliases
        return fn

#################################
# ConceptGraph to Spanning Tree
#################################

from GRIDD.data_structures.spanning_node import SpanningNode

def spanning_tree_of(cg):
    exclude = {'expr', 'def', 'ref', 'assert', 'type', 'link', 'is_type'}
    roots = []
    # main root is the asserted predicate
    ((assertion_node, _, _, _),) = cg.predicates(predicate_type='assert')
    # get all span focus nodes as additional potential roots
    ref_preds = cg.predicates(predicate_type='ref')
    additional_roots = [focal_node for _,_,focal_node,_ in ref_preds if focal_node != assertion_node]
    visited = set()
    for node in [assertion_node] + additional_roots:
        if node not in visited:
            root = SpanningNode('__root__', None)
            roots.append(root)
            frontier = [(root, node, None, 'link')]
            while len(frontier) > 0:
                parent, id, node_type, label_type = frontier.pop(0)
                if id not in visited:
                    visited.add(id)
                    if cg.has(predicate_id=id):
                        s, t, o, _ = cg.predicate(id)
                        if node_type == '_rev_': tmp = o; o = s; s = tmp;
                        pred_node = SpanningNode(id, parent, t, node_type)
                        if parent.node_id != s:
                            frontier.append((pred_node, s, None, 'arg0'))
                        if o is not None:
                            frontier.append((pred_node, o, None, 'arg1'))
                    else:
                        pred_node = SpanningNode(id, parent, None, node_type)
                    parent.children[label_type].append(pred_node)
                    if parent.pred_type != 'time': # do not get descendants of objects of `time` predicates
                        for pred in cg.predicates(id):
                            if pred[1] not in exclude and pred[3] not in {id, parent.node_id}: frontier.append((pred_node, pred[3], None, 'link'))
                        for pred in cg.predicates(object=id):
                            if pred[1] not in exclude and pred[3] not in {id, parent.node_id}: frontier.append((pred_node, pred[3], '_rev_', 'link'))
                else: # still need to attach node to parent if subj or obj of non-reversed predicate, but do not need to process links or node's children
                    if label_type != 'link' and parent.type != '_rev_':
                        if cg.has(predicate_id=id):
                            s, t, o, _ = cg.predicate(id)
                            pred_node = SpanningNode(id, parent, t, node_type)
                        else:
                            pred_node = SpanningNode(id, parent, None, node_type)
                        parent.children[label_type].append(pred_node)
                    elif parent.type == '_rev_': # remove the reverse predicate from spanning tree since it has already been handled
                        parent.parent.children['link'].remove(parent)
    return roots

def spanning_tree_string_of(cg, root=None, tab=1):
    s = ""
    if root is None:
        roots = spanning_tree_of(cg)
        for r in roots:
            root = r.children['link'][0]
            expression = _get_expr(cg, root)
            s += expression + '\n'
            s += spanning_tree_string_of(cg, root, tab)
    else:
        for label, nodes in root.children.items():
            if label in {'arg0', 'arg1'}:
                node = nodes[0]
                prefix = node.type + ' ' if node.type is not None else ''
                expression = _get_expr(cg, node)
                s += '%s%s%s: %s\n'%('\t'*tab, prefix, label, expression)
                s += spanning_tree_string_of(cg, node, tab+1)
            elif label == 'link':
                for node in nodes:
                    prefix = node.type + ' ' if node.type is not None else ''
                    expression = _get_expr(cg, node)
                    if len(node.children) > 0:
                        s += '%s%s%s:\n'%('\t'*tab, prefix, expression)
                        s += spanning_tree_string_of(cg, node, tab+1)
                    else:
                        s += '%s%s%s\n' % ('\t' * tab, prefix, expression)
    return s

def _get_expr(cg, node):
    # Return label of concept as one of the following, in priority order:
    #   (1) Definitions
    #   (2) Expressions
    #   (3) Types
    #   (4) Concept
    # SPECIAL CASES: return `user` or `bot` as label of those concepts
    if isinstance(node, str):
        concept = node
    else:
        concept = node.pred_type if node.pred_type is not None else node.node_id
    label = set()
    if concept in {'user','emora'}:
        label.add(concept)
    else:
        definitions = cg.subjects(concept, 'def')
        if len(definitions) > 0:
            for def_expression in definitions:
                expression = cg.features[def_expression]['span_data'].expression
                label.add(expression)
        else:
            for expression in cg.subjects(concept, 'expr'):
                label.add(expression.replace('"', ''))
                break
        if len(label) == 0:
            for _, _, supertype, predinst in cg.predicates(concept, 'type'):
                label.add(_get_expr(cg, supertype))
        if len(label) == 0:
            return concept.strip()
    return ' '.join(label)

def spanning_tree_linearized(wm):
    rep = spanning_tree_string_of(wm)
    rep = rep.replace('\n', ' ').replace('\t', '').replace(':',' :')
    rep = rep.replace('user', 'EMORA').replace('emora', 'USER')
    rep = rep.replace('EMORA', '_bot_').replace('USER', '_user_')
    return rep

if __name__ == '__main__':
    pass
