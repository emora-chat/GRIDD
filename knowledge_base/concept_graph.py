from structpy.graph.directed.labeled.multilabeled_parallel_digraph_networkx import MultiLabeledParallelDigraphNX
from structpy.map.map import Map
from structpy.map.index.index import Index
from knowledge_base.concept_graph_spec import ConceptGraphSpec
from pyswip import Prolog, Variable
from structpy.map.bijective.bimap import Bimap
CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
from collections import defaultdict
import json, time, copy

class ConceptGraph:

    def __init__(self, predicates=None, concepts=None, namespace=None):
        self._namespace = namespace
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
            elif self.has(predicate_id=predicate_id):
                raise ValueError("Predicate id '%s' already exists!" % str(predicate_id))
            self._monopredicates_map[concept].add(predicate_type)
            self._monopredicate_instances[(concept, predicate_type)].add(predicate_id)
            return predicate_id
        else:                       # Add bipredicate
            if predicate_id is None:
                predicate_id = self._get_next_id()
            elif self.has(predicate_id=predicate_id):
                raise ValueError("Predicate id '%s' already exists!" % str(predicate_id))
            self._bipredicates_graph.add(concept, object, predicate_type, edge_id=predicate_id)
            self._bipredicate_instances[(concept, predicate_type, object)].add(predicate_id)
            return predicate_id

    def remove(self, concept=None, predicate_type=None, object=None, predicate_id=None):
        if predicate_id is not None:        # Remove predicate by id
            pass
        elif predicate_type is not None:    # Remove predicates by type and signature
            pass
        elif object is not None:            # Remove predicates between subject and object
            pass
        else:                               # Remove concept
            pass

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
                        monos = [(*sig, id) for id in self._monopredicate_instances[sig]]
                    else:
                        monos = []
                    if self._bipredicates_graph.has(subject, label=predicate_type):
                        es = self._bipredicates_graph.out_edges(subject, predicate_type)
                        bis = [(s, l, t, self._bipredicate_instances[s, l, t]) for s, t, l in es]
                    else:
                        bis = []
                    return monos + bis
            else:
                if object is not None:      # Predicates by (subject, object)
                    if self._bipredicates_graph.has(subject, object):
                        es = self._bipredicates_graph.edges(subject, object)
                        return [(s, l, t, self._bipredicate_instances[s, l, t]) for s, t, l in es]
                else:                       # Predicates by (subject)
                    if self._bipredicates_graph.has(subject):
                        es = self._bipredicates_graph.out_edges(subject)
                        bis = [(s, l, t, self._bipredicate_instances[s, l, t]) for s, t, l in es]
                    else:
                        bis = []
                    if subject in self._monopredicates_map:
                        ms = self._monopredicates_map[subject]
                        monos = [(subject, m, None, self._monopredicate_instances[subject, m]) for m in ms]
                    else:
                        monos = []
                    return monos + bis
        else:
            if predicate_type is not None:
                if object is not None:      # Predicates by (type, object)
                    if self._bipredicates_graph.has(label=predicate_type, target=object):
                        es = self._bipredicates_graph.in_edges(object, predicate_type)
                        return [(s, l, t, self._bipredicate_instances[s, l, t]) for s, t, l in es]
                else:                       # Predicates by (type)
                    es = self._bipredicates_graph.edges(label=predicate_type)
                    bis = [(s, l, t, self._bipredicate_instances[s, l, t]) for s, t, l in es]
                    if predicate_type in self._monopredicates_map.reverse():
                        ss = self._monopredicates_map.reverse()[predicate_type]
                        monos = [(s, predicate_type, None, self._monopredicate_instances[s, predicate_type]) for s in ss]
                        return monos + bis
                    else:
                        return bis
            else:
                if object is not None:      # Predicates by (object)
                    if self._bipredicates_graph.has(object):
                        es = self._bipredicates_graph.in_edges(object)
                        return [(s, l, t, self._bipredicate_instances[s, l, t]) for s, t, l in es]
                else:                       # All predicates
                    bis = [(*sig, id) for sig, id in self._bipredicate_instances.items()]
                    monos = [(*sig, None, id) for sig, id in self._monopredicate_instances.items()]
                    return monos + bis
        return []

    def subjects(self, concept):
        pass

    def objects(self, concept):
        pass

    def related(self, concept):
        pass

    def merge(self, concept_a, concept_b):
        pass

    def concatenate(self, concept_graph):
        pass

    def copy(self):
        pass

    def copy(self):
        """     FOR REFERENCE   """
        cp = ConceptGraph()
        cp.next_id = self.next_id
        cp.bipredicate_graph = copy.deepcopy(self.bipredicate_graph)
        cp.bipredicate_instance_index = copy.deepcopy(self.bipredicate_instance_index)
        cp.monopredicate_instance_index = copy.deepcopy(self.monopredicate_instance_index)
        cp.monopredicate_map = Map(self.monopredicate_map.items())
        return cp


if __name__ == '__main__':
    print(ConceptGraphSpec.verify(ConceptGraph))

