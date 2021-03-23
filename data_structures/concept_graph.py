
from GRIDD.data_structures.concept_graph_spec import ConceptGraphSpec

from structpy.graph.directed.labeled.multilabeled_parallel_digraph_networkx import MultiLabeledParallelDigraphNX
from structpy.graph.directed.labeled.data.multilabeled_digraph_data import MultiLabeledDigraphDataNX as Graph
from structpy.map.map import Map
from GRIDD.data_structures.id_map import IdMap
from structpy.map.index.index import Index
from GRIDD.data_structures.span import Span
from GRIDD.data_structures.spanning_node import SpanningNode
CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
from collections import defaultdict, deque
import json, copy
from GRIDD.utilities import Counter, collect
import GRIDD.globals

class ConceptGraph:

    def __init__(self, predicates=None, concepts=None, namespace=None, feature_cls=GRIDD.globals.FEATURE_CLS):
        if namespace is not None:
            namespace = namespace
        if isinstance(namespace, IdMap):
            self._ids = namespace
        else:
            self._ids = IdMap(namespace=namespace, start_index=Counter(),
                              contains=lambda x: self.has(x) or self.has(predicate_id=x))
        self._bipredicates_graph = MultiLabeledParallelDigraphNX()
        self._bipredicate_instances = Index()
        self._monopredicates_map = Map()
        self._monopredicate_instances = Index()
        if concepts is not None:
            for concept in concepts:
                self.add(concept)
        if predicates is not None:
            for predicate in predicates:
                self.add(*predicate)
        self.features = feature_cls()

    def add(self, concept, predicate_type=None, object=None, predicate_id=None):
        self._bipredicates_graph.add(concept)
        if predicate_type is None:  # Add concept
            return concept
        elif object is None:        # Add monopredicate
            if predicate_id is None:
                predicate_id = self._ids.get()
            elif self.has(predicate_id=predicate_id): #todo - check signature
                if self.predicate(predicate_id) != (concept, predicate_type, object, predicate_id):
                    raise ValueError("Predicate id '%s' already exists!" % str(predicate_id))
                else:
                    return predicate_id
            self._monopredicates_map[concept].add(predicate_type)
            self._monopredicate_instances[(concept, predicate_type)].add(predicate_id)
            self._bipredicates_graph.add(predicate_type)
            self._bipredicates_graph.add(predicate_id)
            return predicate_id
        else:                       # Add bipredicate
            if predicate_id is None:
                predicate_id = self._ids.get()
            elif self.has(predicate_id=predicate_id): #todo - check signature
                if self.predicate(predicate_id) != (concept, predicate_type, object, predicate_id):
                    raise ValueError("Predicate id '%s' already exists!" % str(predicate_id))
                else:
                    return predicate_id
            self._bipredicates_graph.add(concept, object, predicate_type, edge_id=predicate_id)
            self._bipredicate_instances[(concept, predicate_type, object)].add(predicate_id)
            self._bipredicates_graph.add(predicate_type)
            self._bipredicates_graph.add(predicate_id)
            return predicate_id

    def remove(self, concept=None, predicate_type=None, object=None, predicate_id=None):
        if predicate_id is not None:        # Remove predicate by id
            concept, predicate_type, object, predicate_id = self.predicate(predicate_id)
            if object is not None:
                self._bipredicates_graph.remove(concept, object, predicate_type, predicate_id)
                self._bipredicate_instances[(concept, predicate_type, object)].remove(predicate_id)
                if len(self._bipredicate_instances[(concept, predicate_type, object)]) == 0:
                    del self._bipredicate_instances[(concept, predicate_type, object)]
            else:
                self._monopredicate_instances[(concept, predicate_type)].remove(predicate_id)
                if len(self._monopredicate_instances[(concept, predicate_type)]) == 0:
                    self._monopredicates_map[concept].remove(predicate_type)
                    del self._monopredicate_instances[(concept, predicate_type)]
            self.remove(concept=predicate_id)
        elif predicate_type is not None:    # Remove predicates by type and signature
            for s, t, o, i in self.predicates(concept, predicate_type, object):
                self.remove(predicate_id=i)
        elif object is not None:            # Remove predicates between subject and object
            for s, t, o, i in self.predicates(subject=concept, object=object):
                self.remove(predicate_id=i)
        else:                               # Remove concept
            for s, t, o, i in self.predicates(subject=concept) + self.predicates(object=concept):
                self.remove(predicate_id=i)
            if self._bipredicates_graph.has(concept):
                self._bipredicates_graph.remove(concept)
            del self._monopredicates_map[concept]

    def has(self, concept=None, predicate_type=None, object=None, predicate_id=None):
        if predicate_id is not None:                                    # Check predicate by id
            if predicate_id in self._bipredicate_instances.reverse():
                s, t, o, _ = self.predicate(predicate_id)
                if concept is not None and concept != s:
                    return False
                if predicate_type is not None and predicate_type != t:
                    return False
                if object is not None and object != o:
                    return False
                return True
            elif predicate_id in self._monopredicate_instances.reverse():
                if object is not None:
                    return False
                s, t, _, _ = self.predicate(predicate_id)
                if concept is not None and concept != s:
                    return False
                if predicate_type is not None and predicate_type != t:
                    return False
                return True
            else:
                return False
        elif predicate_type is not None:                                # Check predicate by signature
            if object is not None:
                return self._bipredicates_graph.has(concept, object, predicate_type)
            else:
                return concept in self._monopredicates_map \
                       and predicate_type in self._monopredicates_map[concept]
        elif object is not None:                                        # Check concept link
            return self._bipredicates_graph.has(concept, object)
        else:                                                           # Check concept existence
            return self._bipredicates_graph.has(concept)

    def concepts(self):
        return self._bipredicates_graph.nodes()

    def subject(self, predicate_id):
        if predicate_id in self._bipredicate_instances.reverse():
            return self._bipredicate_instances.reverse()[predicate_id][0]
        if predicate_id in self._monopredicate_instances.reverse():
            return self._monopredicate_instances.reverse()[predicate_id][0]
        raise KeyError("Predicate id %s does not exist!" % str(predicate_id))

    def object(self, predicate_id):
        if predicate_id in self._bipredicate_instances.reverse():
            return self._bipredicate_instances.reverse()[predicate_id][2]
        if predicate_id in self._monopredicate_instances.reverse():
            return None
        raise KeyError("Predicate id %s does not exist!" % str(predicate_id))

    def type(self, predicate_id):
        if predicate_id in self._bipredicate_instances.reverse():
            return self._bipredicate_instances.reverse()[predicate_id][1]
        if predicate_id in self._monopredicate_instances.reverse():
            return self._monopredicate_instances.reverse()[predicate_id][1]
        raise KeyError("Predicate id %s does not exist!" % str(predicate_id))

    def predicate(self, predicate_id):
        if predicate_id in self._bipredicate_instances.reverse():
            return (*self._bipredicate_instances.reverse()[predicate_id], predicate_id)
        if predicate_id in self._monopredicate_instances.reverse():
            return (*self._monopredicate_instances.reverse()[predicate_id], None, predicate_id)
        raise KeyError("Predicate id %s does not exist!" % str(predicate_id))

    def predicates(self, subject=None, predicate_type=None, object=None):
        if subject is not None:
            if predicate_type is not None:
                if object is not None:      # Predicates by (subject, type, object)
                    sig = (subject, predicate_type, object)
                    if sig in self._bipredicate_instances:
                        return [(*sig, id) for id in self._bipredicate_instances[sig]]
                else:                       # Predicates by (subject, type)
                    sig = (subject, predicate_type)
                    if sig in self._monopredicate_instances:
                        monos = [(*sig, None, id) for id in self._monopredicate_instances[sig]]
                    else:
                        monos = []
                    if self._bipredicates_graph.has(subject, label=predicate_type):
                        es = self._bipredicates_graph.out_edges(subject, predicate_type)
                        bis = [(s, l, t, i) for s, t, l, i in es]
                    else:
                        bis = []
                    return monos + bis
            else:
                if object is not None:      # Predicates by (subject, object)
                    if self._bipredicates_graph.has(subject, object):
                        es = self._bipredicates_graph.edges(subject, object)
                        return [(s, l, t, i) for s, t, l, i in es]
                else:                       # Predicates by (subject)
                    if self._bipredicates_graph.has(subject):
                        es = self._bipredicates_graph.out_edges(subject)
                        bis = [(s, l, t, i) for s, t, l, i in es]
                    else:
                        bis = []
                    if subject in self._monopredicates_map:
                        ms = self._monopredicates_map[subject]
                        monos = [(subject, m, None, i) for m in ms for i in self._monopredicate_instances[subject, m]]
                    else:
                        monos = []
                    return monos + bis
        else:
            if predicate_type is not None:
                if object is not None:      # Predicates by (type, object)
                    es = self._bipredicates_graph.in_edges(object, predicate_type)
                    return [(s, l, t, i) for s, t, l, i in es]
                else:                       # Predicates by (type)
                    es = self._bipredicates_graph.edges(label=predicate_type)
                    bis = [(s, l, t, i) for s, t, l, i in es]
                    if predicate_type in self._monopredicates_map.reverse():
                        ss = self._monopredicates_map.reverse()[predicate_type]
                        monos = [(s, predicate_type, None, i) for s in ss for i in self._monopredicate_instances[s, predicate_type]]
                        return monos + bis
                    else:
                        return bis
            else:
                if object is not None:      # Predicates by (object)
                    if self._bipredicates_graph.has(object):
                        es = self._bipredicates_graph.in_edges(object)
                        return [(s, l, t, i) for s, t, l, i in es]
                else:                       # All predicates
                    bis = [(*sig, i) for sig, id in self._bipredicate_instances.items() for i in id]
                    monos = [(*sig, None, i) for sig, id in self._monopredicate_instances.items() for i in id]
                    return monos + bis
        return []

    def subjects(self, concept, type=None):
        return set([predicate[0] for predicate in self.predicates(predicate_type=type,
                                                                  object=concept)])

    def objects(self, concept, type=None):
        return set([predicate[2] for predicate in self.predicates(subject=concept,predicate_type=type)
                    if predicate[2] is not None])

    def related(self, concept, type=None):
        neighbors = self.subjects(concept, type)
        neighbors.update(self.objects(concept, type))
        return neighbors

    def subtypes(self, concept):
        subtypes = set()
        for predicate in self.predicates(predicate_type='type', object=concept):
            subtype = predicate[0]
            subtypes.add(subtype)
            subtypes.update(self.subtypes(subtype))
        return subtypes

    # todo - efficiency check
    #  if multiple paths to same ancestor,
    #  it will pull ancestor's ancestor-chain multiple times
    def supertypes(self, concept):
        types = set()
        for predicate in self.predicates(subject=concept, predicate_type='type'):
            supertype = predicate[2]
            types.add(supertype)
            types.update(self.supertypes(supertype))
        return types

    def id_map(self, other=None):
        if other is None:
            return self._ids
        if not isinstance(other, str):
            other = other._ids.namespace
        else:
            other = other
        return IdMap(namespace=self._ids.namespace,
                     start_index=self._ids.index,
                     condition=(lambda other_id: self.id_map().namespace != other and isinstance(other_id, str)
                                                 and isinstance(other, str) and other_id.startswith(other))
                     )

    def to_graph(self):
        graph = Graph()
        for s, t, o, i in self.predicates():
            graph.add(i, s, 's')
            graph.add(i, t, 't')
            if o is not None:
                graph.add(i, o, 'o')
        for c in self.concepts():
            graph.add(c)
        return graph

    def merge(self, concept_a, concept_b, strict_order=False):
        if not strict_order and concept_a.startswith(self._ids.namespace) and not concept_b.startswith(self._ids.namespace):
            tmp = concept_a
            concept_a = concept_b
            concept_b = tmp
        for s, t, o, i in self.predicates(subject=concept_b):
            self._detach(s, t, o, i)
            self.add(concept_a, t, o, i)
        for s, t, o, i in self.predicates(object=concept_b):
            self._detach(s, t, o, i)
            self.add(s, t, concept_a, i)
        for s, t, o, i in self.predicates(predicate_type=concept_b):
            self._detach(s, t, o, i)
            self.add(s, concept_a, o, i)
        if self.has(predicate_id=concept_a) and self.has(predicate_id=concept_b):
            # merge all arguments, if not the same
            subj_a, type_a, obj_a, inst_a = self.predicate(concept_a)
            subj_b, type_b, obj_b, inst_b = self.predicate(concept_b)
            if subj_a != subj_b:
                subj_a = self.merge(subj_a, subj_b, strict_order=strict_order)
            if type_a != type_b:
                type_a = self.merge(type_a, type_b, strict_order=strict_order)
            if obj_a is not None and obj_b is not None and obj_a != obj_b:
                obj_a = self.merge(obj_a, obj_b, strict_order=strict_order)
            elif obj_b is not None:
                # promote to argument structure of higher ordered predicate (monopredicate < bipredicate)
                self._detach(subj_a, type_a, obj_a, inst_a)
                self.add(subj_a, type_a, obj_b, inst_a)
            self._detach(*self.predicate(inst_b))
        elif self.has(predicate_id=concept_b) and not self.has(predicate_id=concept_a):
            s, t, o, i = self.predicate(concept_b)
            self.add(s, t, o, concept_a)
            self._detach(s, t, o, i)
        self.remove(concept_b)
        self.features.merge(concept_a, concept_b)
        return concept_a

    def _detach(self, subject, predicate_type, object, predicate_id):
        if object is None:  # monopredicate
            self._monopredicate_instances[(subject, predicate_type)].remove(predicate_id)
            if len(self._monopredicate_instances[(subject, predicate_type)]) == 0:
                del self._monopredicate_instances[(subject, predicate_type)]
                self._monopredicates_map[subject].remove(predicate_type)
        else:               # bipredicate
            self._bipredicate_instances[(subject, predicate_type, object)].remove(predicate_id)
            self._bipredicates_graph.remove(subject, object, predicate_type, predicate_id)
            if len(self._bipredicate_instances[(subject, predicate_type, object)]) == 0:
                del self._bipredicate_instances[(subject, predicate_type, object)]

    def concatenate(self, concept_graph, predicate_exclusions=None, concepts=None, id_map=None):
        if id_map is None:
            id_map = self.id_map(concept_graph)
        for s, t, o, i in concept_graph.predicates():
            if (predicate_exclusions is None or t not in predicate_exclusions) and (concepts is None or i in concepts):
                if not self.has(predicate_id=i):
                    self.add(*(id_map.get(x) if x is not None else None for x in (s, t, o, i)))
        for concept in concept_graph.concepts():
            if concept not in id_map:
                if predicate_exclusions is None:
                    if concepts is None or concept in concepts:
                        self.add(id_map.get(concept))
                else:
                    if concept not in predicate_exclusions and (concepts is None or concept in concepts):
                        if not concept_graph.has(predicate_id=concept) \
                           or concept_graph.type(concept) not in predicate_exclusions:
                            self.add(id_map.get(concept))
        self.features.update(concept_graph.features, id_map)
        self.id_map().index = id_map.index
        return id_map

    def graph_component_siblings(self, source, target):
        target = set(self.predicate(target)) if self.has(predicate_id=target) else {target}
        visited = set()
        frontier = deque([source])
        # print('\n %s -> %s'%(source, target))
        while len(frontier) > 0:
            # print(frontier)
            node = frontier.popleft()
            # print(node)
            if node in target:
                return True
            if node not in visited:
                visited.add(node)
                if self.has(predicate_id=node):
                    nodes = self.predicate(node)
                    frontier.extend([nodes[0],nodes[2]])
                else:
                    frontier.extend(self.related(node))
        return False


    def copy(self, namespace=None):
        if namespace is None:
            namespace = self._ids.namespace
        cp = ConceptGraph(namespace=namespace)
        cp.concatenate(self)
        cp.features = self.features.copy()
        return cp

    def save(self, json_filepath=None):
        d = {
            'namespace': self._ids.namespace,
            'next_id': int(self._ids.index),
            'predicates': [],
            'features': self.features.to_json()
        }
        for item in self.predicates():
            item = [e.to_string() if hasattr(e, 'to_string') else str(e) for e in item]
            s, t, o, i = item
            d['predicates'].append([s, t, o, i])
        if json_filepath:
            with open(json_filepath, 'w') as f:
                json.dump(d, f, indent=2)
        else:
            return d

    def load(self, json_file_str_obj):
        if isinstance(json_file_str_obj, str):
            if json_file_str_obj.endswith('.json'):
                with open(json_file_str_obj, 'r') as f:
                    d = json.load(f)
            else:
                d = json.loads(json_file_str_obj)
        else:
            d = json_file_str_obj
        if d['namespace'] != self._ids.namespace:
            for item in d['predicates']:
                id_map = self.id_map(d['namespace'])
                s, t, o, i = item
                if o == 'None':
                    o = None
                self.add(*(id_map.get(x) if x is not None else None for x in (s, t, o ,i)))
                self.features.from_json(d['features'], id_map=id_map)
        else:
            for item in d['predicates']:
                s, t, o, i = item
                if o == 'None':
                    o = None
                self.add(s, t, o, i)
            self._ids.index = Counter(d['next_id'])
            self.features.from_json(d['features'])

    def ugly_print(self, exclusions=None):
        strings = defaultdict(list)
        preds = ['type', 'ref', 'def', 'instantiative', 'referential', 'question']
        for pred in preds:
            if exclusions is None or pred not in exclusions:
                for s, t, o, i in self.predicates(predicate_type=pred):
                    if s not in exclusions and o not in exclusions:
                        if o is not None:
                            strings[pred].append('%s/%s(%s,%s)\n' % (i, t, s, o))
                        else:
                            strings[pred].append('%s/%s(%s)\n' % (i, t, s))
        strings['mono'] = []
        strings['bi'] = []
        for s, t, o, i in self.predicates():
            if (exclusions is None or (t not in exclusions and s not in exclusions and o not in exclusions)) and t not in preds:
                if o is not None:
                    strings['bi'].append('%s/%s(%s,%s)\n' % (i, t, s, o))
                else:
                    strings['mono'].append('%s/%s(%s)\n' % (i, t, s))
        strings['type'] = sorted(strings['type'])
        full_string = '\n'.join([''.join(value) for value in strings.values()])
        return full_string.strip()

    def pretty_print(self, exclusions=None):
        name_counter = defaultdict(int)
        id_map = {}
        visited = set()
        type_string = ""
        bi_string = ""
        mono_string = ""
        for sig in self.predicates():
            type_string, bi_string, mono_string = self._get_representation(sig, id_map, name_counter, visited,
                                                                           type_string, bi_string, mono_string,
                                                                           exclusions)
        full_string = type_string + '\n' + mono_string + '\n' + bi_string
        return full_string.strip()

    def _get_representation(self, predicate_signature, id_map, name_counter, visited,
                            type_string, bi_string, mono_string, exclusions):
        if predicate_signature not in visited:
            s, t, o, i = predicate_signature
            if exclusions is None or (t not in exclusions and s not in exclusions and o not in exclusions):
                id_map[t] = t
                concepts = [s, o] if o is not None else [s]
                for concept in concepts:
                    if concept not in id_map:
                        if isinstance(concept, str) and concept.startswith(self.id_map().namespace):
                            if self.has(predicate_id=concept):
                                type_string, bi_string, mono_string = self._get_representation(self.predicate(concept),
                                                                                               id_map, name_counter,
                                                                                               visited,
                                                                                               type_string, bi_string,
                                                                                               mono_string,
                                                                                               exclusions)
                            else:
                                types = self.predicates(concept, 'type')
                                if len(types) > 0:
                                    ctype = types[0][2]
                                    name_counter[ctype] += 1
                                    id_map[concept] = '%s_%d' % (ctype, name_counter[ctype])
                                else:
                                    id_map[concept] = concept
                        elif isinstance(concept, Span):
                            id_map[concept] = concept.string
                        else:
                            id_map[concept] = concept
                if o is not None:
                    pname = id_map[s].replace('_', '')[0] + id_map[t].replace('_', '')[0] + id_map[o].replace('_', '')[
                        0]
                else:
                    pname = id_map[s].replace('_', '')[0] + id_map[t].replace('_', '')[0]
                name_counter[pname] += 1
                if name_counter[pname] == 1:
                    id_map[i] = pname
                else:
                    id_map[i] = '%s_%d' % (pname, name_counter[pname])
                if o is not None:
                    to_add = '%s/%s(%s,%s)\n' % (id_map[i], id_map[t], id_map[s], id_map[o])
                    if id_map[t] == 'type':
                        type_string += to_add
                    else:
                        bi_string += to_add
                else:
                    mono_string += '%s/%s(%s)\n' % (id_map[i], id_map[t], id_map[s])
                visited.add(predicate_signature)
        return type_string, bi_string, mono_string

    def to_spanning_tree(self):
        exclude = {'expr', 'def', 'ref', 'assert', 'type'}
        root = SpanningNode('__root__')
        ((assertion_node,_,_,_), ) = self.predicates(predicate_type='assert')
        frontier = [(root, assertion_node, None, 'link')]
        visited = set()
        while len(frontier) > 0:
            parent, id, node_type, label_type = frontier.pop(0)
            if id not in visited:
                visited.add(id)
                if self.has(predicate_id=id):
                    s, t, o, _ = self.predicate(id)
                    if node_type == '_rev_': tmp = o; o = s; s = tmp;
                    pred_node = SpanningNode(id, t, node_type)
                    if parent.node_id != s:
                        frontier.append((pred_node, s, None, 'arg0'))
                    if o is not None:
                        frontier.append((pred_node, o, None, 'arg1'))
                else:
                    pred_node = SpanningNode(id, None, node_type)
                parent.children[label_type].append(pred_node)
                for pred in self.predicates(id):
                    if pred[1] not in exclude and pred[3] not in {id, parent.node_id}: frontier.append((pred_node, pred[3], None, 'link'))
                for pred in self.predicates(object=id):
                    if pred[1] not in exclude and pred[3] not in {id, parent.node_id}: frontier.append((pred_node, pred[3], '_rev_', 'link'))
            else: # still need to attach node to parent if subj or obj, but do not need to process links or node's children
                if label_type != 'link':
                    if self.has(predicate_id=id):
                        s, t, o, _ = self.predicate(id)
                        pred_node = SpanningNode(id, t, node_type)
                    else:
                        pred_node = SpanningNode(id, None, node_type)
                    parent.children[label_type].append(pred_node)
        return root

    def print_spanning_tree(self, root=None, tab=1):
        s = ""
        if root is None:
            root = self.to_spanning_tree().children['link'][0]
            string = root.pred_type if root.pred_type is not None else root.node_id
            expression = self._get_expr(string)
            s += expression + '\n'
        for label, nodes in root.children.items():
            if label in {'arg0', 'arg1'}:
                node = nodes[0]
                string = node.pred_type if node.pred_type is not None else node.node_id
                prefix = node.type + ' ' if node.type is not None else ''
                expression = self._get_expr(string)
                s += '%s%s%s: %s\n'%('\t'*tab, prefix, label, expression)
                s += self.print_spanning_tree(node, tab+1)
            elif label == 'link':
                for node in nodes:
                    string = node.pred_type if node.pred_type is not None else node.node_id
                    prefix = node.type + ' ' if node.type is not None else ''
                    expression = self._get_expr(string)
                    if len(node.children) > 0:
                        s += '%s%s%s:\n'%('\t'*tab, prefix, expression)
                        s += self.print_spanning_tree(node, tab+1)
                    else:
                        s += '%s%s%s\n' % ('\t' * tab, prefix, expression)
        return s

    def _get_expr(self, concept):
        # Return label of concept as one of the following, in priority order:
        #   (1) Definitions
        #   (2) Expressions
        #   (3) Types
        #   (4) Concept
        # SPECIAL CASES: return `user` or `bot` as label of those concepts
        label = ''
        if concept in {'user','emora'}:
            label += concept
        else:
            definitions = self.subjects(concept, 'def')
            if len(definitions) > 0:
                for def_expression in definitions:
                    expression = self.features[def_expression]['span_data'].expression
                    label += expression + ' '
            else:
                for expression in self.subjects(concept, 'expr'):
                    label += expression.replace('"', '') + ' '
                    break
            if len(label) == 0:
                for _, _, supertype, predinst in self.predicates(concept, 'type'):
                    label += self._get_expr(supertype) + ' '
            if len(label) == 0:
                return concept.strip()
        return label.strip()

    def __str__(self):
        return 'CG<%s>' % (str(id(self))[-5:])

    def __repr__(self):
        return str(self)

if __name__ == '__main__':
    print(ConceptGraphSpec.verify(ConceptGraph))




