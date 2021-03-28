
from GRIDD.data_structures.intelligence_core_spec import IntelligenceCoreSpec


from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.data_structures.concept_compiler import ConceptCompiler
from GRIDD.utilities.utilities import uniquify, operators

import GRIDD.data_structures.intelligence_core_operators as intcoreops

SENSORY_SALIENCE = 1
ASSOCIATION_DECAY = 0.1
TIME_DECAY = 0.1
NONASSERT = 'nonassert'
SALIENCE = 'salience'
CONFIDENCE = 'confidence'


class IntelligenceCore:

    def __init__(self, knowledge_base=None, working_memory=None, inference_engine=None):
        self.compiler = ConceptCompiler(namespace='__c__')
        if isinstance(knowledge_base, ConceptGraph):
            self.knowledge_base = knowledge_base
        else:
            self.knowledge_base = ConceptGraph(namespace='kb')
            self.know(knowledge_base)
        if isinstance(working_memory, ConceptGraph):
            self.working_memory = working_memory
        else:
            self.working_memory = ConceptGraph(namespace='wm')
            self.consider(working_memory)
        if inference_engine is None:
            inference_engine = InferenceEngine()
        self.inference_engine = inference_engine
        self.operators = operators(intcoreops)

    def know(self, knowledge):
        cg = ConceptGraph(namespace='_tmp_')
        ConceptGraph.construct(cg, knowledge, compiler=self.compiler)
        self.knowledge_base.concatenate(cg)

    def consider(self, concepts, associations=None, salience=None):
        considered = ConceptGraph(concepts, namespace='_tmp_')
        if associations is None:
            considered.features.update({c: {'salience': salience*SENSORY_SALIENCE}
                                                  for c in considered.concepts()})
        else:
            s = min([self.working_memory.features.get(c, {}).get('salience', 0)
                            for c in associations]) - ASSOCIATION_DECAY
            considered.features.update({c: {'salience': s*salience}
                                        for c in considered.concepts()})
        self.working_memory.concatenate(considered)

    def infer(self, rules=None):
        if rules is None:
            solutions = self.inference_engine.infer(self.working_memory)
        else:
            solutions = self.inference_engine.infer(self.working_memory, rules=rules)
        return solutions

    def apply_inferences(self, inferences=None):
        cg = self.inference_engine.apply(inferences)
        # do something

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
        pass

    def pull_knowledge(self):
        pass

    def pull_expressions(self):
        pass

    def update_confidence(self):
        wm = self.working_memory
        for c in wm:
            if 'c' not in wm.features.get(c, {}):
                # get types (IMPLEMENT IN ConceptGraph)
                if wm.has(predicate_id=c):
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


if __name__ == '__main__':
    print(IntelligenceCoreSpec.verify(IntelligenceCore))



