
from math import log
import os
from inspect import getmembers, isfunction
from itertools import cycle, islice
from itertools import chain
from GRIDD.globals import *
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

def collect(*files_folders_or_strings, extension=None):
    files_or_strings = []
    for ffs in files_folders_or_strings:
        if isinstance(ffs, str) and os.path.isdir(ffs):
            for fs in os.listdir(ffs):
                if not extension or fs.endswith(extension):
                    files_or_strings.append(os.path.join(ffs, fs))
        else:
            files_or_strings.append(ffs)
    counter = 0
    collected = {}
    for ffs in sorted(files_or_strings):
        if not extension or (isinstance(ffs, str) and ffs.endswith(extension)):
            if os.path.isdir(ffs):
                collected.update(collect(ffs))
            elif os.path.isfile(ffs):
                with open(ffs, 'r') as f:
                    collected[ffs] = f.read()
            else:
                collected[str(counter)] = ffs
                counter += 1
        else:
            collected[str(counter)] = ffs
            counter += 1
    return collected


def dict_of_sets_merge(*dictionaries):
    result = {}
    for d in dictionaries:
        for k, v in d.items():
            result.setdefault(k, v).update(v)
    return result


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
    def __add__(self, other):
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
    return d


class aliases:
    def __init__(self, *aliases):
        self.aliases = aliases
    def __call__(self, fn):
        fn.aliases = self.aliases
        return fn

def interleave(*iterables):
    "interleave('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    num_active = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while num_active:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            # Remove the iterator we just exhausted from the cycle.
            num_active -= 1
            nexts = cycle(islice(nexts, num_active))

def _process_requests(cg):
    # add req_unsat to all unresolved requests
    for s,t,o,i in chain(cg.predicates(predicate_type=REQ_ARG), cg.predicates(predicate_type=REQ_TRUTH)):
        if not cg.has(i, REQ_SAT):
            cg.add(i, REQ_UNSAT)

def _process_answers(cg, request):
    cg.add(request, REQ_SAT)
    cg.remove(request, REQ_UNSAT)


#################################
# ConceptGraph to Spanning Tree
#################################

from GRIDD.data_structures.spanning_node import SpanningNode

def spanning_tree_of(cg):
    exclude = {'expr', 'def', 'ref', 'assert', 'type', 'link', 'user_aware'}
    roots = []
    pred_types_visited = set() # save the predicate type of predicate intances that have been visited to avoid outputting just the predicate type again like in cases of copular_ids
    # main root is the asserted predicate
    ((_, _, assertion_node, _),) = cg.predicates(predicate_type='assert')
    # get all span focus nodes as additional potential roots
    ref_preds = cg.predicates(predicate_type='ref')
    additional_roots = [focal_node for _,_,focal_node,_ in ref_preds if focal_node != assertion_node]
    visited = set()
    for node in [assertion_node] + additional_roots:
        if node not in visited and node not in pred_types_visited:
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
                        pred_types_visited.add(t)
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
                    if label_type != 'link': # and parent.type != '_rev_':
                        if cg.has(predicate_id=id):
                            s, t, o, _ = cg.predicate(id)
                            pred_node = SpanningNode(id, parent, t, node_type)
                        else:
                            pred_node = SpanningNode(id, parent, None, node_type)
                        parent.children[label_type].append(pred_node)
                    # elif parent.type == '_rev_': # remove the reverse predicate from spanning tree since it has already been handled
                    #     parent.parent.children['link'].remove(parent)
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

def spanning_tree_linearized(wm, nlg_training_mode=True):
    rep = spanning_tree_string_of(wm)
    rep = rep.replace('\n', ' ').replace('\t', '').replace(':',' :')
    if nlg_training_mode:
        rep = rep.replace('user', 'EMORA').replace('emora', 'USER')
    else:
        rep = rep.replace('user', 'USER').replace('emora', 'EMORA')
    rep = rep.replace('EMORA', '_bot_').replace('USER', '_user_')
    return rep

class TensorDisplay:

    def __init__(self, displaying=True):
        self.displaying = displaying

    def __call__(self, x, *ids, label=None):
        """
        Print tensor in a readable form with IdMaps to show element meanings.

        ids: IdMap for each column (or dimension if 2D tensor)
        label: label for display
        """
        return self.display(x, *ids, label=label)

    def display(self, x, *ids, label=None):
        """
        Print tensor in a readable form with IdMaps to show element meanings.

        ids: IdMap for each column (or dimension if 2D tensor)
        label: label for display
        """
        if self.displaying:
            if label is not None:
                print(label, ':')
            ids = [(e.reverse() if e is not None else e) for e in ids]
            if len(ids) == x.size()[1]:
                for row in x:
                    to_print = []
                    for i, e in enumerate(row):
                        if hasattr(ids[i], '__getitem__'):
                            e_ = ids[i].get(int(e), int(e))
                        else:
                            e_ = int(e)
                        if isinstance(e_, tuple):
                            _, e_ = e_
                        to_print.append(str(e_))
                    print(('{:13}'*len(row)).format(*to_print))
            else:
                colnames = [(str(ids[1][i]) if ids[1] is not None else '') for i in range(x.size(1))]
                print((' '*9+'{:>9}'*x.size(1)).format(*colnames))
                for i in range(x.size(0)):
                    s = x.size(1)
                    fmtstr = '{:>9}'+'{:>9}'*int(s)
                    args = [ids[0][i], *[int(j) for j in x[i]]]
                    for i, arg in enumerate(args):
                        if isinstance(arg, tuple):
                            args[i] = arg[1]
                    print(fmtstr.format(*[str(arg) for arg in args]))
            print()

if __name__ == '__main__':
    pass
