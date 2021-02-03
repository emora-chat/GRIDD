from structpy.graph.directed.labeled.multilabeled_parallel_digraph_networkx import MultiLabeledParallelDigraphNX
from structpy.map.map import Map
from structpy.map.index.index import Index
from GRIDD.data_structures.concept_graph_spec import ConceptGraphSpec
from GRIDD.data_structures.span import Span
CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
import GRIDD.utilities as util
from collections import defaultdict
import json


CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

class ConceptGraph:

    def __init__(self, predicates=None, concepts=None, namespace=None):
        if namespace is None:
            namespace = 'def'
        self._namespace = namespace.lower()
        self._next_id = 0
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

    def _get_next_id(self):
        if self._namespace is not None:
            next_id = self._namespace + '_' + str(self._next_id)
            while self.has(next_id):
                self._next_id += 1
                next_id = self._namespace + '_' + str(self._next_id)
        else:
            next_id = str(self._next_id)
            while self.has(next_id):
                self._next_id += 1
                next_id = str(self._next_id)
        self._next_id += 1
        return next_id

    def add(self, concept, predicate_type=None, object=None, predicate_id=None):
        self._bipredicates_graph.add(concept)
        if predicate_type is None:  # Add concept
            return concept
        elif object is None:        # Add monopredicate
            if predicate_id is None:
                predicate_id = self._get_next_id()
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
                predicate_id = self._get_next_id()
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

    def merge(self, concept_a, concept_b):
        if self.has(predicate_id=concept_a) and self.has(predicate_id=concept_b):
            raise ValueError("Cannot merge two predicate instances!")
        if concept_a.startswith(self._namespace) and not concept_b.startswith(self._namespace):
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
        if self.has(predicate_id=concept_b):
            s, t, o, i = self.predicate(concept_b)
            self.add(s, t, o, concept_a)
            self._detach(s, t, o, i)
        self.remove(concept_b)
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

    def concatenate(self, concept_graph, predicate_exclusions=None):
        id_map = {}
        if predicate_exclusions is not None:
            for s, t, o, i in concept_graph.predicates():
                if t not in predicate_exclusions:
                    s = util.map(self, s, concept_graph._namespace, id_map)
                    t = util.map(self, t, concept_graph._namespace, id_map)
                    o = util.map(self, o, concept_graph._namespace, id_map)
                    i = util.map(self, i, concept_graph._namespace, id_map)
                    self.add(s, t, o, i)
        else:
            for s, t, o, i in concept_graph.predicates():
                s = util.map(self, s, concept_graph._namespace, id_map)
                t = util.map(self, t, concept_graph._namespace, id_map)
                o = util.map(self, o, concept_graph._namespace, id_map)
                i = util.map(self, i, concept_graph._namespace, id_map)
                self.add(s, t, o, i)
        for concept in concept_graph.concepts():
            if concept not in id_map:
                if predicate_exclusions is None:
                    concept = util.map(self, concept, concept_graph._namespace, id_map)
                    self.add(concept)
                else:
                    if concept not in predicate_exclusions:
                        if not concept_graph.has(predicate_id=concept) or concept_graph.type(concept) not in predicate_exclusions:
                            concept = util.map(self, concept, concept_graph._namespace, id_map)
                            self.add(concept)
        return id_map

    def copy(self, namespace=None):
        if namespace is None:
            namespace = self._namespace
        cp = ConceptGraph(namespace=namespace)
        if namespace != self._namespace:
            namespace_map = {}
            for s, t, o, i in self.predicates():
                s = util.map(cp, s, self._namespace, namespace_map)
                t = util.map(cp, t, self._namespace, namespace_map)
                o = util.map(cp, o, self._namespace, namespace_map)
                i = util.map(cp, i, self._namespace, namespace_map)
                cp.add(s, t, o, i)
        else:
            for s, t, o, i in self.predicates():
                cp.add(s, t, o, i)
        cp._next_id = self._next_id
        return cp

    def save(self, json_filepath=None):
        d = {
            'namespace': self._namespace,
            'next_id': self._next_id,
            'predicates': []
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
        if d['namespace'] != self._namespace:
            namespace_map = {}
            for item in d['predicates']:
                for i, e in enumerate(item):
                    if e.startswith('<span>'):
                        item[i] = Span.from_string(e)
                s, t, o, i = item
                if o == 'None':
                    o = None
                s = util.map(self, s, d['namespace'], namespace_map)
                t = util.map(self, t, d['namespace'], namespace_map)
                o = util.map(self, o, d['namespace'], namespace_map)
                i = util.map(self, i, d['namespace'], namespace_map)
                self.add(s, t, o ,i)
        else:
            for item in d['predicates']:
                for i, e in enumerate(item):
                    if e.startswith('<span>'):
                        item[i] = Span.from_string(e)
                s, t, o, i = item
                if o == 'None':
                    o = None
                self.add(s, t, o, i)
            self._next_id = d['next_id']

    def ugly_print(self, exclusions=None):
        ont_str, inst_str, mono_str, bi_str = '', '', '', ''
        for s, t, o, i in self.predicates(predicate_type='type'):
            if exclusions is None or (t not in exclusions and s not in exclusions and o not in exclusions):
                tmp = '%s/%s(%s,%s)\n' % (i, t, s, o)
                if 'wm_' in tmp[tmp.find('/'):] or 'kb_' in tmp[tmp.find('/'):]:
                    inst_str += tmp
                else:
                    ont_str += tmp
        for s, t, o, i in self.predicates():
            if (exclusions is None or (t not in exclusions and s not in exclusions and o not in exclusions)) \
                    and t != 'type':
                if o is not None:
                    bi_str += '%s/%s(%s,%s)\n' % (i, t, s, o)
                else:
                    mono_str += '%s/%s(%s)\n' % (i, t, s)
        full_string = ont_str + '\n' + inst_str + '\n' + mono_str + '\n' + bi_str
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
                        if isinstance(concept, str) and concept.startswith(self._namespace):
                            if self.has(predicate_id=concept):
                                type_string, bi_string, mono_string = self._get_representation(self.predicate(concept),
                                                                                               id_map, name_counter, visited,
                                                                                               type_string, bi_string, mono_string,
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
                    pname = id_map[s].replace('_', '')[0] + id_map[t].replace('_', '')[0] + id_map[o].replace('_', '')[0]
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

    def __str__(self):
        return 'CG<%s>' % (str(id(self))[-5:])

    def __repr__(self):
        return str(self)



if __name__ == '__main__':
    print(ConceptGraphSpec.verify(ConceptGraph))




