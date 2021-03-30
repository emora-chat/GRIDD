
from GRIDD.data_structures.intelligence_core_spec import IntelligenceCoreSpec

from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.data_structures.concept_compiler import ConceptCompiler
from GRIDD.utilities.utilities import uniquify, operators
from itertools import chain
from functools import reduce
from GRIDD.data_structures.update_graph import UpdateGraph
from GRIDD.globals import SENSORY_SALIENCE, NECESSARY, SUFFICIENT, \
                            ASSOCIATION_DECAY, CONFIDENCE, NONASSERT

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
            self.working_memory = ConceptGraph(namespace='wm', supports={NECESSARY: False})
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
        return mapping.values()

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
        # todo - types are absolute knowledge (either you have it or you don't)
        # todo - think about type-based evidence
        #  (type predicates not found in solutions explicitly right now)
        if inferences is None:
            inferences = self.infer()
        result_dict = self.inference_engine.apply(inferences)
        for rule, results in result_dict.items():
            for evidence, implication in results:
                implied_nodes = self.consider(implication)
                and_node = self.working_memory.id_map().get()
                for e in evidence.values():
                    if self.working_memory.has(predicate_id=e):
                        self.working_memory.metagraph.add(e, and_node, NECESSARY)
                for n in implied_nodes:
                    if self.working_memory.has(predicate_id=n):
                        self.working_memory.metagraph.add(and_node, n, SUFFICIENT)

    def update_confidence(self):
        # todo - distinguish between sensory assertions and derived confidence;
        #  set self-loops on sensory assertions
        mg = self.working_memory.metagraph
        necessaries = mg.edges(label=NECESSARY)
        sufficients = mg.edges(label=SUFFICIENT)
        def and_fn(sources):
            sources, _ = list(zip(*sources))
            return reduce(lambda a, b: a*b, sources)
        def or_fn(sources):
            sources, _ = list(zip(*sources))
            return reduce(lambda a, b: a+b, sources) - reduce(lambda a, b: a*b, sources)
        update_graph = UpdateGraph(
            edges=[*necessaries, *sufficients],
            nodes={c: mg.features.get(c, {}).get(CONFIDENCE, 0) for c in mg.nodes()},
            updaters={
                **{n: and_fn for _,n,_ in necessaries},
                **{n: or_fn for _,n,_ in sufficients}},
            default=0,
            set_fn=(lambda n, v: mg.features.setdefault(n, {}).__setitem__(CONFIDENCE, v))
        )
        update_graph.update(push=True)

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
        references = []
        # Todo: collect references for IntCore resolution
        return self.inference_engine.infer(references, cached=False)

    def logical_merge(self):
        # Todo: logical merge
        return

    def pull_types(self):
        type_predicates = list(self.knowledge_base.type_predicates(self.working_memory.concepts()))
        for pred in type_predicates:
            self.working_memory.add(*pred)

    def pull_knowledge(self):
        pass

    def pull_expressions(self):
        pass

    def update_salience(self):
        return

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

    def display(self):
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
        for na in predicates & not_asserted:
            cg.features.setdefault(na, {})[CONFIDENCE] = 0.0

    def _loading_options(self, cg, options):
        if 'commonsense' in options:
            pass
        elif 'attention_shift' in options:
            pass


if __name__ == '__main__':
    print(IntelligenceCoreSpec.verify(IntelligenceCore))



