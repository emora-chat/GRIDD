
from GRIDD.data_structures.concept_graph_spec import ConceptGraphSpec, ConceptGraphFromLogicSpec

from structpy.graph.directed.labeled.multilabeled_parallel_digraph_networkx import MultiLabeledParallelDigraphNX
from structpy.graph.directed.labeled.data.multilabeled_digraph_data import MultiLabeledDigraphDataNX as Graph
from structpy.map.map import Map
from GRIDD.data_structures.id_map import IdMap
from structpy.map.index.index import Index
from GRIDD.data_structures.span import Span
from GRIDD.data_structures.concept_compiler import compile_concepts
from GRIDD.data_structures.meta_graph import MetaGraph

CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
from collections import defaultdict, deque
import json
from GRIDD.utilities import Counter
from GRIDD.globals import *
from itertools import chain


class ConceptGraph:

    def __init__(self, predicates=None, concepts=None, namespace=None,
                 metalinks=None, metadata=None, supports=None):
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
        self.metagraph = MetaGraph(self, supports)
        if concepts is not None:
            for concept in concepts:
                self.add(concept)
        if predicates is not None:
            ConceptGraph.construct(self, predicates, metalinks, metadata)

    @classmethod
    def construct(cls, cg, predicates, metalinks=None, metadata=None, compiler=None):
        if isinstance(predicates, str) or \
                (isinstance(predicates, list) and len(predicates) > 0
                 and isinstance(predicates[0], str)):
            if compiler is None:
                p, ml, md = compile_concepts(predicates, namespace='__c__')
            else:
                p, ml, md = compiler.compile(predicates)
            pred_cg = ConceptGraph(predicates=p, namespace='__c__')
            pred_cg.features.update(md)
            for s, l, t in ml:
                pred_cg.metagraph.add(s, t, l)
            cg.concatenate(pred_cg)
        elif (isinstance(predicates, (list, tuple, set)) and len(predicates) > 0
              and (isinstance(next(iter(predicates)), (list, tuple)))):
            for predicate in predicates:
                cg.add(*predicate)
        elif isinstance(predicates, (list, tuple, set, str)) and len(predicates) == 0:
            pass # no predicates to add to cg
        else:  # ConceptGraph
            cg.concatenate(predicates)
        if metalinks is not None:
            for s, l, t in metalinks:
                cg.metagraph.add(s, t, l)
        if metadata is not None:
            cg.features.update(metadata)

    @property
    def features(self):
        return self.metagraph.features

    def add(self, concept, predicate_type=None, object=None, predicate_id=None):
        self._bipredicates_graph.add(concept)
        if predicate_type is None:  # Add concept
            return concept
        elif object is None:        # Add monopredicate
            if predicate_id is None:
                predicate_id = self._ids.get()
            elif self.has(predicate_id=predicate_id):
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
            elif self.has(predicate_id=predicate_id):
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
        if concept is not None and predicate_type is None and object is None \
                and predicate_id is None and self.has(predicate_id=concept):
            predicate_id = concept
            concept = None
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
            for s, t, o, i in list(self.predicates(concept, predicate_type, object)):
                self.remove(predicate_id=i)
        elif object is not None:            # Remove predicates between subject and object
            for s, t, o, i in list(self.predicates(subject=concept, object=object)):
                self.remove(predicate_id=i)
        else:                               # Remove concept
            for s, t, o, i in list(self.predicates(subject=concept)):
                self.remove(predicate_id=i)
            for s, t, o, i in list(self.predicates(object=concept)):
                self.remove(predicate_id=i)
            if self._bipredicates_graph.has(concept):
                self._bipredicates_graph.remove(concept)
            del self._monopredicates_map[concept]
            self.metagraph.discard(concept)


    def clear(self):
        self._ids = IdMap(namespace=self._ids.namespace, start_index=Counter(),
                         contains=lambda x: self.has(x) or self.has(predicate_id=x))
        self._bipredicates_graph = MultiLabeledParallelDigraphNX()
        self._bipredicate_instances = Index()
        self._monopredicates_map = Map()
        self._monopredicate_instances = Index()
        self.metagraph = MetaGraph(self)

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
                        for id in self._bipredicate_instances[sig]:
                            yield (*sig, id)
                else:                       # Predicates by (subject, type)
                    sig = (subject, predicate_type)
                    if sig in self._monopredicate_instances:
                        for id in self._monopredicate_instances[sig]:
                            yield (*sig, None, id)
                    if self._bipredicates_graph.has(subject, label=predicate_type):
                        for s, t, l, i in self._bipredicates_graph.out_edges(subject, predicate_type):
                            yield s, l, t, i
            else:
                if object is not None:      # Predicates by (subject, object)
                    if self._bipredicates_graph.has(subject, object):
                        for s, t, l, i in self._bipredicates_graph.edges(subject, object):
                            yield s, l, t, i
                else:                       # Predicates by (subject)
                    if self._bipredicates_graph.has(subject):
                        for s, t, l, i in self._bipredicates_graph.out_edges(subject):
                            yield s, l, t, i
                    if subject in self._monopredicates_map:
                        for m in self._monopredicates_map[subject]:
                            for i in self._monopredicate_instances[subject, m]:
                                yield (subject, m, None, i)
        else:
            if predicate_type is not None:
                if object is not None:      # Predicates by (type, object)
                    for s, t, l, i in self._bipredicates_graph.in_edges(object, predicate_type):
                        yield s, l, t, i
                else:                       # Predicates by (type)
                    for s, t, l, i in self._bipredicates_graph.edges(label=predicate_type):
                        yield s, l, t, i
                    if predicate_type in self._monopredicates_map.reverse():
                        for s in self._monopredicates_map.reverse()[predicate_type]:
                            for i in self._monopredicate_instances[s, predicate_type]:
                                yield (s, predicate_type, None, i)
            else:
                if object is not None:      # Predicates by (object)
                    if self._bipredicates_graph.has(object):
                        for s, t, l, i in self._bipredicates_graph.in_edges(object):
                            yield s, l, t, i
                else:                       # All predicates
                    for sig, id in self._bipredicate_instances.items():
                        for i in id:
                            yield (*sig, i)
                    for sig, id in self._monopredicate_instances.items():
                        for i in id:
                            yield (*sig, None, i)

    def subjects(self, concept, type=None):
        return set([predicate[0] for predicate in self.predicates(predicate_type=type,
                                                                  object=concept)])

    def objects(self, concept, type=None):
        return set([predicate[2] for predicate in self.predicates(subject=concept,predicate_type=type)
                    if predicate[2] is not None])

    def structure(self, concept, subj_emodifiers=None, obj_emodifiers=None):
        visited = {None}
        s = []
        stack = [concept]
        while stack:
            concept = stack.pop()
            if concept not in visited:
                visited.add(concept)
                if self.has(predicate_id=concept):
                    pred = self.predicate(concept)
                    s.append(pred)
                    stack.extend({pred[0], pred[2]} - visited)
                    if pred[1] in {REQ_TRUTH, REQ_ARG}:
                        # if concept is a request predicate, retrieve all ref metalinks to object for full definition
                        obj = pred[2]
                        for _, constraint, _ in self.metagraph.out_edges(obj, REF):
                            if self.has(predicate_id=constraint):
                                mp = self.predicate(constraint)
                                if mp[1] not in {'ref', 'def', 'expr'} and mp[3] not in visited:
                                    stack.append(mp[3])
                for p in self.predicates(concept, predicate_type='type'):
                    if p[3] not in visited:
                        s.append(p)
                        visited.add(p[3])
                if subj_emodifiers:
                    for em in subj_emodifiers:
                        for mp in self.predicates(concept, predicate_type=em):
                            if mp[3] not in visited:
                                stack.append(mp[3])
                if obj_emodifiers:
                    for em in obj_emodifiers:
                        for mp in self.predicates(object=concept, predicate_type=em):
                            if mp[3] not in visited:
                                stack.append(mp[3])
        return s

    def related(self, concept, types=None, exclusions=None, limit=None):
        if self.has(predicate_id=concept):
            yield from [x for x in self.predicate(concept) if x is not None and (exclusions is None or x not in exclusions)]
        num = 0
        for _, t, _, i in self.predicates(concept):
            if (types is None or t in types) and (exclusions is None or t not in exclusions):
                if limit is None or num < limit:
                    yield i
                    num += 1
                else: break
        for _, t, _, i in self.predicates(object=concept):
            if (types is None or t in types) and (exclusions is None or t not in exclusions):
                if limit is None or num < limit:
                    yield i
                    num += 1
                else: break

    def subtypes_of(self, concept, memo=None):
        if memo is None:
            memo = {}
        if concept is not None:
            if concept not in memo:
                types = {concept}
                yield concept
                for _, _, _, instance in self.predicates(predicate_type=concept):
                    for st in self.subtypes_of(instance, memo):
                        yield st
                        types.add(st)
                for predicate in self.predicates(predicate_type='type', object=concept):
                    subtype = predicate[0]
                    for st in self.subtypes_of(subtype, memo):
                        yield st
                        types.add(st)
                memo[concept] = types
            else:
                yield from memo[concept]

    def subtypes(self, memo=None):
        if memo is None:
            memo = {}
        todo = set(self.concepts())
        while todo:
            concept = todo.pop()
            todo.difference_update(self.subtypes_of(concept, memo))
        return memo

    def instances(self, concept=None, memo=None, limit=None):
        count = 0
        for subtype in self.subtypes_of(concept, memo):
            if self.metagraph.features.get(subtype, {}).get(IS_TYPE, False):
                if count < limit:
                    yield subtype
                else: break

    def types(self, concept=None, memo=None):
        if memo is None:
            memo = {}
        if concept is not None and not isinstance(concept, (list, set, tuple)):
            if concept not in memo:
                if self.has(predicate_id=concept):
                    inst = concept
                    concept = self.type(concept)
                else:
                    inst = None
                types = {concept}
                for predicate in self.predicates(subject=concept, predicate_type='type'):
                    supertype = predicate[2]
                    if concept == supertype: # todo - this should not be possible, right?
                        raise ValueError('Concept has self-loop type predicate which causes types() to crash on recursion error!')
                    types.update(self.types(supertype, memo))
                memo[concept] = types
                if inst is not None:
                    memo[inst] = types | {inst}
                    return memo[inst]
            return memo[concept]
        else:
            if isinstance(concept, (list, set, tuple)):
                todo = set(concept)
            else:
                todo = set(self.concepts())
            while todo:
                concept = todo.pop()
                self.types(concept, memo)
                todo.difference_update(set(memo.keys()))
            return memo

    def type_predicates(self, concepts=None, memo=None):
        if memo is None:
            memo = {}
        if concepts is not None and not isinstance(concepts, (list, set, tuple)):
            if concepts not in memo:
                if self.has(predicate_id=concepts):
                    inst = concepts
                    concepts = self.type(concepts)
                else:
                    inst = None
                types = {concepts}
                for predicate in self.predicates(subject=concepts, predicate_type='type'):
                    supertype = predicate[2]
                    supertypes = list(self.type_predicates(supertype, memo))
                    types.update([o for s,t,o,i in supertypes])
                    yield from supertypes
                    yield predicate
                memo[concepts] = types
                if inst is not None:
                    memo[inst] = types | {inst}
                    return
            return
        else:
            if isinstance(concepts, (list, set, tuple)):
                todo = set(concepts)
            else:
                todo = set(self.concepts())
            while todo:
                concepts = todo.pop()
                yield from self.type_predicates(concepts, memo)
                todo.difference_update(set(memo.keys()))
            return

    def rules(self, rule_instances=None):
        rules = {}
        if rule_instances is None:
            rule_instances = set(self.subtypes_of('implication')) - {'implication'}

        rule_links = {}
        instance_exclusions = set()
        for rule in rule_instances:
            pre_inst = self.metagraph.out_edges(rule, PRE)
            pre = [edge[1] for edge in pre_inst]
            post_inst = self.metagraph.out_edges(rule, POST)
            post = [edge[1] for edge in post_inst]
            vars_inst = self.metagraph.out_edges(rule, VAR)
            vars = {edge[1] for edge in vars_inst}
            if pre and post:
                instance_exclusions.update(chain(pre_inst, post_inst, vars_inst))
                rule_links[rule] = (pre, post, vars)

        for rule, (pre, post, vars) in rule_links.items():
            if pre and post:
                pre = self.subgraph(pre, meta_exclusions=instance_exclusions)
                post = self.subgraph(post, meta_exclusions=instance_exclusions)
                rules[rule] = (pre, post, vars)
        return rules

    def nlg_templates(self):
        templates = {}
        template_instances = set(self.subtypes_of('response')) - {'response'}

        template_links = {}
        instance_exclusions = set()
        for template in template_instances:
            # Get the rule that this template is the postcondition of
            (rule, ) = self.metagraph.sources(template, POST)
            # Get the precondition and vars
            pre_inst = self.metagraph.out_edges(rule, PRE)
            pre = [edge[1] for edge in pre_inst]
            vars_inst = self.metagraph.out_edges(rule, VAR)
            vars = {edge[1] for edge in vars_inst}
            # get the post and represent it as a list of string element specifications
            elements = self.objects(template, 'token_seq')
            elements = sorted(elements, key=lambda x: self.features[x]['response_index'])
            string_spec_ls = []
            for e in elements:
                string_literal = self.features[e]['response_str']
                if string_literal is None:
                    (var,) = self.metagraph.targets(e, 'response_var')
                    string_repr = f"{var}.var"
                else:
                    string_repr = string_literal
                string_data = self.features[e].get('response_data', None)
                if string_data is not None:
                    for key, value in string_data.items():
                        if isinstance(value, str) and value[0] == '#':
                            (node,) = self.metagraph.targets(e, key)
                            string_data[key] = node
                final_element = (string_repr, string_data) if string_data is not None else string_repr
                string_spec_ls.append(final_element)
            instance_exclusions.update(chain(pre_inst, vars_inst))
            template_links[template] = (pre, string_spec_ls, vars)

        for template, (pre, string_spec_ls, vars) in template_links.items():
            pre = self.subgraph(pre, meta_exclusions=instance_exclusions)
            templates[template] = (pre, string_spec_ls, vars)
        return templates


    def references(self):
        references = {}
        ref_instances = {s for s, t, l in self.metagraph.edges(label=REF)}
        for ref in ref_instances:
            pre = self.metagraph.targets(ref, REF)
            vars = set(self.metagraph.targets(ref, VAR))
            if pre:
                pre = self.subgraph(pre)
                references[ref] = (pre, vars)
        return references

    def generics(self):
        generics = {}
        group_instances = [g for g in self.subtypes_of(GROUP) if g != GROUP]
        # all groups that act as subjects of some predicate are generating generics
        for group in group_instances:
            preds = [p for p in self.predicates(group) if p[1] not in {TYPE, USER_AWARE, ASSERT, NONASSERT}]
            if preds:
                def_concepts = [e[1] for e in self.metagraph.out_edges(group, GROUP_DEF)
                                if not self.has(predicate_id=e[1]) or self.predicate(e[1]) != (e[0], TYPE, GROUP, e[1])]
                prop_concepts = [e[1] for e in self.metagraph.out_edges(group, GROUP_PROP)]
                generics[group] = (def_concepts, prop_concepts)
        # certain predicate types are generics if object is group (like, enjoy, hate, ) -> i like cats (generic) vs i bought cats (non-generic)
        return generics

    def subgraph(self, concepts=None, types=None, exclusions=None, type_exclusions=None, meta_exclusions=None):
        concepts = set(concepts) if concepts else set()
        exclusions = set(exclusions) if exclusions else set()
        meta_exclusions = set(meta_exclusions) if meta_exclusions else set()
        if types is not None or type_exclusions is not None:
            subtypes = self.subtypes()
            if types is not None:
                concepts.update(set(chain(*[subtypes[t] for t in types])))
            if type_exclusions is not None:
                exclusions.update(set(chain(*[subtypes[t] for t in type_exclusions])))
        graph = ConceptGraph(namespace=self._ids)
        to_add = set()
        for c in concepts - exclusions:
            if self.has(predicate_id=c):
                pred = self.predicate(c)
                graph.add(*pred)
                to_add.update(pred)
            else:
                graph.add(c)
                to_add.add(c)
        for e in to_add:
            fd = dict(self.features.get(e, {}))
            if fd:
                graph.features[e] = fd
            for ml in chain(self.metagraph.in_edges(e), self.metagraph.out_edges(e)):
                if ml not in meta_exclusions and graph.has(ml[0]) and graph.has(ml[1]):
                    graph.metagraph.add(*ml)
        return graph

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
        unique_preds = {USER_AWARE, TIME}
        if concept_a != concept_b:
            if not strict_order and concept_a.startswith(self._ids.namespace) and not concept_b.startswith(self._ids.namespace):
                tmp = concept_a
                concept_a = concept_b
                concept_b = tmp
            for s, t, o, i in list(self.predicates(subject=concept_b)):
                self._detach(s, t, o, i)
                if t not in unique_preds or (t in unique_preds and not self.has(concept_a, t, o)):
                    self.add(concept_a, t, o, i)
            for s, t, o, i in list(self.predicates(object=concept_b)):
                self._detach(s, t, o, i)
                self.add(s, t, concept_a, i)
            for s, t, o, i in list(self.predicates(predicate_type=concept_b)):
                self._detach(s, t, o, i)
                self.add(s, concept_a, o, i)
            if self.has(predicate_id=concept_a) and self.has(predicate_id=concept_b): # todo - inefficient if types are the same
                subj_a, type_a, obj_a, inst_a = self.predicate(concept_a)
                subj_b, type_b, obj_b, inst_b = self.predicate(concept_b)
                self._detach(subj_a, type_a, obj_a, inst_a)
                self._detach(subj_b, type_b, obj_b, inst_b)
                additional_type = None
                if type_a == type_b:
                    final_type = type_a
                elif type_b in set(self.subtypes_of(type_a)):   # type_b is a subtype of type_a
                    final_type = type_b
                elif type_a in set(self.subtypes_of(type_b)):   # type_a is a subtype of type_b
                    final_type = type_a
                else:
                    print('WARNING! Merging predicate instances but neither type (%s, %s) is a subtype of the other!'
                                     % (type_a, type_b))
                    final_type = type_a
                    additional_type = type_b
                # make new predicate, then merge args in
                if obj_a is None and obj_b is None:
                    final_subj=self.id_map().get()
                    i = self.add(final_subj, final_type, predicate_id=concept_a)
                else:
                    # promote to argument structure of higher ordered predicate (monopredicate < bipredicate)
                    final_subj=self.id_map().get()
                    final_obj=self.id_map().get()
                    i = self.add(final_subj, final_type, final_obj, predicate_id=concept_a)
                    if obj_a is not None:
                        self.merge(final_obj, obj_a)
                    if obj_b is not None:
                        self.merge(final_obj, obj_b)
                if additional_type is not None:
                    self.add(i, TYPE, additional_type)
                self.merge(final_subj, subj_a)
                self.merge(final_subj, subj_b)
            elif self.has(predicate_id=concept_b) and not self.has(predicate_id=concept_a):
                s, t, o, i = self.predicate(concept_b)
                self.add(s, t, o, concept_a)
                self._detach(s, t, o, i)
            self.metagraph.merge(concept_a, concept_b)
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

    def concatenate(self, concept_graph, predicate_exclusions=None, concepts=None, id_map=None):
        """
        :param concepts - list of predicate instance ids to be concatenated from concept_graph into self
            * only used by KnowledgeParser._extract_rules_from_graph()
        """
        if id_map is None:
            id_map = self.id_map(concept_graph)
        if concept_graph.id_map().namespace == KB: # maintain KB predicate identifiers in any CG they get added to
            id_map = concept_graph.id_map(concept_graph)
        all_added_concepts = None
        if concepts is not None:
            all_added_concepts = set()
        for s, t, o, i in concept_graph.predicates():
            if (predicate_exclusions is None or t not in predicate_exclusions) and (concepts is None or i in concepts):
                if t is not USER_AWARE or not self.has(s, t): # DO NOT ADD DUPLICATE USER_AWARE PREDS!!!
                    self.add(*(id_map.get(x) if x is not None else None for x in (s, t, o, i)))
                    if concepts is not None:
                        all_added_concepts.update({x for x in (s,t,o,i) if x is not None})
        for concept in concept_graph.concepts():
            if concept not in id_map:
                if predicate_exclusions is None:
                    if concepts is None or concept in concepts:
                        self.add(id_map.get(concept))
                        if concepts is not None:
                            all_added_concepts.add(concept)
                else:
                    if concept not in predicate_exclusions and (concepts is None or concept in concepts):
                        if not concept_graph.has(predicate_id=concept) \
                           or concept_graph.type(concept) not in predicate_exclusions:
                            self.add(id_map.get(concept))
                            if concepts is not None:
                                all_added_concepts.add(concept)
        self.id_map().index = id_map.index # todo - is this necessary?
        self.metagraph.update(concept_graph.metagraph, concept_graph.metagraph.features,
                              id_map=id_map, concepts=all_added_concepts)
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
            namespace = self._ids
        cp = ConceptGraph(namespace=namespace)
        cp.concatenate(self)
        cp.metagraph = self.metagraph.copy(cp)
        return cp

    def save(self, json_filepath=None):
        d = {
            'namespace': self._ids.namespace,
            'next_id': int(self._ids.index),
            'predicates': [],
            'concepts': [],
            'features': self.metagraph.to_json()
        }
        for item in self.predicates():
            item = [e.to_string() if hasattr(e, 'to_string') else str(e) for e in item]
            s, t, o, i = item
            d['predicates'].append([s, t, o, i])
        for item in self.concepts():
            item = item.to_string() if hasattr(item, 'to_string') else str(item)
            d['concepts'].append(item)
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
            id_map = self.id_map(d['namespace'])
            for item in d['concepts']:
                self.add(id_map.get(item))
            for item in d['predicates']:
                s, t, o, i = item
                if o == 'None':
                    o = None
                self.add(*(id_map.get(x) if x is not None else None for x in (s, t, o ,i)))
            self.metagraph.from_json(d['features'], id_map=id_map)
        else:
            for item in d['concepts']:
                self.add(item)
            for item in d['predicates']:
                s, t, o, i = item
                if o == 'None':
                    o = None
                self.add(s, t, o, i)
            self._ids.index = Counter(d['next_id'])
            self.metagraph.from_json(d['features'])

    def ugly_print(self, exclusions=None):
        strings = defaultdict(list)
        preds = ['type', 'ref', 'def', 'instantiative', 'referential', REQ_TRUTH, REQ_ARG]
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

    def __str__(self):
        return 'CG<%s>' % (str(id(self))[-5:])

    def __repr__(self):
        return str(self)

    def _was_autonamed(self, concept):
        return self._ids.namespace is not None and concept.startswith(self._ids.namespace)

    def pretty_print(self, exclusions=None, typeinfo=False):
        display = deque()
        todo = set(self.concepts())
        for e in list(todo):
            if exclusions is not None and self.has(predicate_id=e) and self.predicate(e)[1] in exclusions:
                todo.discard(e)

        class counter(dict):
            def setdefault(self, key, default):
                r = dict.setdefault(self, key, default)
                self[key] += 1
                return r

        ids = {}
        nums = counter()

        def cstr(c):
            string = ''
            todo.discard(c)
            if c in ids:
                return ids[c]
            if self.has(predicate_id=c):
                s, t, o, i = self.predicate(c)
                ids.setdefault(c, '$' + c + '$' if not self._was_autonamed(c) \
                    else '$' + t + '_' + str(nums.setdefault(t, 0)) + '$')
                string += '#' + ids[c] + ('/' if self._was_autonamed(c) else '=')
                todo.discard(t)
                string += t + '('
                string += cstr(s)
                if o is not None:
                    string += ', ' + cstr(o)
                string += ')'
            else:
                types = list(self.objects(c, 'type'))
                if len(types) > 0:
                    t = types[0]
                    ids.setdefault(c, '$' + c + '$' if not self._was_autonamed(c) \
                        else '$' + t + '_' + str(nums.setdefault(t, 0)) + '$')
                    string += '#' + ids[c] + ('/' if self._was_autonamed(c) else '=') + types[0] + '()'
                    todo.discard(types[0])
                else:
                    string += c
            return string

        roots = set(todo) - set(chain(*[(s, o) for s, _, o, _ in self.predicates()]))
        roots.difference_update(self.predicates(predicate_type='type'))
        for root in [root for root in roots if self.has(predicate_id=root) and self.type(root) != 'type']:
            display.append(cstr(root))
        preds = [self.predicate(c) for c in todo if self.has(predicate_id=c)]
        type_preds = [(s, t, o, i) for s, t, o, i in preds if t == 'type']
        todo -= set(chain(*type_preds))
        while todo:
            left = todo.pop()
            if self.has(predicate_id=left):
                display.append(cstr(left))

        if typeinfo:
            types = {}
            for s, t, o, i in type_preds:
                if exclusions is None or (s not in exclusions and o not in exclusions):
                    types.setdefault(s, set()).add(o)
            for c, v in types.items():
                c = ids.get(c, c)
                v = [ids.get(x, x) for x in v]
                display.appendleft(c + ':  ' + ', '.join(v))

        returner = '\n'.join(display)
        for i in ids.values():
            if returner.count(i) > 1:
                returner = returner.replace('#'+i, i[1:-1])
                returner = returner.replace(i, i[1:-1])
            else:
                returner = returner.replace('#'+i+'/', '')
        returner = returner.replace('#', '').replace('$', '')
        return returner

if __name__ == '__main__':
    print(ConceptGraphSpec.verify(ConceptGraph))
    # print(ConceptGraphFromLogicSpec.verify(ConceptGraph))



