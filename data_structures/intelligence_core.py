
from GRIDD.data_structures.intelligence_core_spec import IntelligenceCoreSpec

from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.data_structures.concept_compiler import ConceptCompiler
from GRIDD.utilities.utilities import uniquify, operators, interleave
from itertools import chain, combinations
from GRIDD.data_structures.update_graph import UpdateGraph
from GRIDD.globals import *

import GRIDD.data_structures.intelligence_core_operators as intcoreops


class IntelligenceCore:

    def __init__(self, knowledge_base=None, working_memory=None, inference_engine=None):
        self.compiler = ConceptCompiler(namespace='__c__')
        if inference_engine is None:
            inference_engine = InferenceEngine()
        self.inference_engine = inference_engine
        if isinstance(knowledge_base, ConceptGraph):
            self.knowledge_base = knowledge_base
        else:
            self.knowledge_base = ConceptGraph(namespace='kb')
            self.know(knowledge_base)
        if isinstance(working_memory, ConceptGraph):
            self.working_memory = working_memory
        else:
            self.working_memory = ConceptGraph(namespace='wm', supports={AND_LINK: False})
            self.accept(working_memory)
        self.operators = operators(intcoreops)

    def know(self, knowledge, **options):
        cg = ConceptGraph(namespace='_tmp_')
        ConceptGraph.construct(cg, knowledge, compiler=self.compiler)
        self._loading_options(cg, options)
        self._assertions(cg)
        rules = cg.rules()
        for rule, (pre, post, vars) in rules.items():
            for concept in set(chain(pre.concepts(), post.concepts())):
                cg.remove(concept)
            cg.remove(rule)
        self.inference_engine.add(rules)
        self.knowledge_base.concatenate(cg)

    def consider(self, concepts, associations=None, salience=1, **options):
        considered = ConceptGraph(concepts, namespace='_tmp_')
        if associations is None:
            considered.features.update({c: {'salience': salience*SENSORY_SALIENCE}
                                                  for c in considered.concepts()})
        else:
            s = min([self.working_memory.features.get(c, {}).get('salience', 0)
                            for c in associations]) - ASSOCIATION_DECAY
            considered.features.update({c: {'salience': s*salience}
                                        for c in considered.concepts()})
        self._loading_options(concepts, options)
        mapping = self.working_memory.concatenate(considered)
        return mapping

    def accept(self, concepts, associations=None, salience=1, **options):
        considered = ConceptGraph(concepts, namespace='_tmp_')
        if associations is None:
            considered.features.update({c: {'salience': salience*SENSORY_SALIENCE}
                                                  for c in considered.concepts()})
        else:
            s = min([self.working_memory.features.get(c, {}).get('salience', 0)
                            for c in associations]) - ASSOCIATION_DECAY
            considered.features.update({c: {'salience': s*salience}
                                        for c in considered.concepts()})
        self._loading_options(concepts, options)
        self._assertions(considered)
        mapping = self.working_memory.concatenate(considered)
        return mapping.values()

    def infer(self, rules=None):
        if rules is None:
            solutions = self.inference_engine.infer(self.working_memory)
        else:
            solutions = self.inference_engine.infer(self.working_memory, rules=rules)
        return solutions

    def apply_inferences(self, inferences=None):
        """
        :param inferences: {rule: (pre, post, [solution_dict, ...]),
                            ...}
        """
        # todo - think about type-based evidence
        #  (type predicates not found in solutions explicitly right now)
        if inferences is None:
            inferences = self.infer()
        result_dict = self.inference_engine.apply(inferences)
        for rule, results in result_dict.items():
            for evidence, implication in results:
                implication_strengths = {}
                for n in implication.concepts():
                    if implication.has(predicate_id=n):
                        implication_strengths[n] = implication.features.get(n, {}).get(CONFIDENCE, 1)
                        if n in implication.features and CONFIDENCE in implication.features[n]:
                            del implication.features[n][CONFIDENCE]
                implied_nodes = self.consider(implication, associations=evidence.values())
                and_node = self.working_memory.id_map().get()
                for pre_node, evidence_node in evidence.items():
                    if self.working_memory.has(predicate_id=evidence_node):
                        strength = inferences[rule][0].features.get(pre_node, {}).get(CONFIDENCE, 1)
                        self.working_memory.metagraph.add(evidence_node, and_node, (AND_LINK, strength))
                for imp_node, strength in implication_strengths.items():
                    self.working_memory.metagraph.add(and_node, implied_nodes[imp_node], (OR_LINK, strength))

    def update_confidence(self):
        mg = self.working_memory.metagraph
        and_links = [edge for edge in mg.edges() if isinstance(edge[2], tuple) and AND_LINK == edge[2][0]]
        or_links = [edge for edge in mg.edges() if isinstance(edge[2], tuple) and OR_LINK == edge[2][0]]
        def and_fn(node, sources):
            product = 1
            for value, (label, weight) in sources:
                product *= weight * value
            return product
        def or_fn(node, sources):
            sum = node
            product = node
            for value, (label, weight) in sources:
                sum += value * weight
                product *= value * weight
            return sum - product
        update_graph = UpdateGraph(
            edges=[*and_links, *or_links],
            nodes={c: mg.features.get(c, {}).get(CONFIDENCE, 0) if mg.features.get(c, {}).get(BASE, False) else 0
                   for c in mg.nodes()},
            updaters={
                **{n: and_fn for _,n,_ in and_links},
                **{n: or_fn for _,n,_ in or_links}},
            default=0,
            set_fn=(lambda n, v: mg.features.setdefault(n, {}).__setitem__(CONFIDENCE, v))
        )
        update_graph.update(iteration=10, push=True)

    def merge(self, concept_sets):
        sets = {}
        for cs in concept_sets:
            s = set()
            for c in cs:
                ns = sets.setdefault(c, s)
                if ns is not s:
                    ns.update(s)
                    for n in s:
                        sets[n] = ns
                ns.add(c)
        sets = uniquify(sets.values())
        for s in sets:
            if s:
                a = s[0]
                for i in range(1, len(s)):
                    b = s[i]
                    a = self.working_memory.merge(a, b)

    def resolve(self, references=None):
        if references is None:
            references = self.working_memory.references()
        inferences = self.inference_engine.infer(self.working_memory, references, cached=False)
        compatible_pairs = []
        for reference_node, (pre, matches) in inferences.items():
            for match in matches:
                pairs = [(match[node], node) for node in match] if reference_node != match[reference_node] else []
                compatible_pairs.extend(pairs)
        return compatible_pairs

    def logical_merge(self):
        # Todo: logical merge
        return

    def pull_types(self):
        type_predicates = list(self.knowledge_base.type_predicates(self.working_memory.concepts()))
        for pred in type_predicates:
            self.working_memory.add(*pred)

    def pull_knowledge(self, limit, num_pullers, assocation_limit=None, subtype_limit=None, degree=1):
        kb = self.knowledge_base
        pullers = sorted(self.working_memory.concepts(),
                         key=lambda c: self.working_memory.features.get(c, {}).get(SALIENCE, 0),
                         reverse=True)
        pullers = pullers[:num_pullers]
        neighbors = {}
        backptrs = {}
        for p in pullers:
            neighborhood = set(self.knowledge_base.related(p, limit=assocation_limit))
            arguments = set()
            for n in neighborhood:
                if self.knowledge_base.has(predicate_id=n):
                    s, _, o, _ = self.knowledge_base.predicate(n)
                    other_arg = o if s == p else s
                    if other_arg is not None:
                        arguments.add(other_arg)
                        backptrs.setdefault(other_arg, set()).add(n)
            neighborhood.update(arguments)
            neighbors[p] = neighborhood
        pulling = set()
        wmp = set(self.working_memory.predicates())
        memo = {}
        essential_types = [i for i in kb.subtypes_of(ESSENTIAL) if not kb.has(predicate_id=i)]
        for length in range(2, 0, -1): # todo - inefficient; identify combinations -> empty intersection and ignore in further processing
            combos = combinations(pullers, length)
            for combo in combos:
                related = set(neighbors[combo[0]])
                concepts = [combo[0]]
                for c in combo[1:]:
                    concepts.append(c)
                    tconcepts = tuple(concepts)
                    if tconcepts in memo:
                        related = memo[tconcepts]
                    else:
                        related.intersection_update(neighbors[c])
                        memo[tconcepts] = set(related)
                    if len(related) == 0:
                        break
                for r in related:
                    to_add = set(self.knowledge_base.structure(r, essential_types))
                    for inst in backptrs.get(r, r):
                        to_add.update(self.knowledge_base.structure(inst, essential_types))
                    to_add.difference_update(wmp)
                    to_add.difference_update(pulling)
                    if len(to_add) <= limit:
                        limit -= len(to_add)
                        pulling.update(to_add)
                    else:
                        return pulling
        return pulling

    def pull_expressions(self):
        pass

    def update_salience(self, iterations=10):
        wm = self.working_memory
        edges = wm.to_graph().edges()
        redges = [(t, s, l) for s, t, l in edges]
        def moderated_salience(salience, connectivity):
            return salience / connectivity
        def update_instance_salience(val, args):
            ms = [val[0]]
            for (sal, con), lnk in args:
                if lnk == SALIENCE_IN_LINK:
                    ms.append(moderated_salience(sal, con) - ASSOCIATION_DECAY)
                else:
                    ms.append(sal)
            return (max(ms), val[1])
        updater = UpdateGraph(
            [*[(s, t, SALIENCE_OUT_LINK) for s, t, _ in edges],
             *[(s, t, SALIENCE_IN_LINK) for s, t, _ in redges]],
            nodes={
                c: (wm.features.get(c, {}).get(SALIENCE, 0),
                    wm.features.get(c, {}).get(CONNECTIVITY, 1))
                for c in wm.concepts()},
            updaters={c: update_instance_salience for c in wm.concepts()},
            default=(0, 1)
        )
        updater.update(iterations)

    def decay_salience(self):
        pass

    def prune_attended(self):
        pass

    def operate(self, cg=None):
        if cg is None:
            cg = self.working_memory
        for opname, opfunc in self.operators.items():
            for _, _, _, i in list(cg.predicates(predicate_type=opname)):
                if cg.has(predicate_id=i): # within-loop-mutation check
                    opfunc(cg, i)

    def display(self, verbosity=1):
        s = '#'*30 + ' Working Memory ' + '#'*30
        s += self.working_memory.pretty_print()
        s += '#'*(60+len(' working memory '))
        return s

    def _assertions(self, cg):
        """
        Set confidence of predicates to 1.0 if they don't already
        have a confidence AND they are not an argument of a NONASSERT.
        """
        types = cg.types()
        predicates = set()
        not_asserted = set()
        for s, _, o, pred in cg.predicates():
            if CONFIDENCE not in cg.features.get(pred, {}):
                predicates.add(pred)
            if NONASSERT in types[pred]:
                if cg.has(predicate_id=s):
                    not_asserted.add(s)
                if cg.has(predicate_id=o):
                    not_asserted.add(o)
        for a in predicates - not_asserted:
            cg.features.setdefault(a, {})[CONFIDENCE] = 1.0
            cg.features[a][BASE] = True
        for na in predicates & not_asserted:
            cg.features.setdefault(na, {})[CONFIDENCE] = 0.0

    def _loading_options(self, cg, options):
        if 'commonsense' in options:
            pass
        elif 'attention_shift' in options:
            pass


if __name__ == '__main__':
    print(IntelligenceCoreSpec.verify(IntelligenceCore))



