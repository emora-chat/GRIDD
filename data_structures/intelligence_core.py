
from GRIDD.data_structures.intelligence_core_spec import IntelligenceCoreSpec


from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.data_structures.concept_compiler import ConceptCompiler
from GRIDD.utilities.utilities import uniquify


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
        self.operators = {}

    def know(self, knowledge):
        cg = ConceptGraph(namespace='_tmp_')
        ConceptGraph.construct(cg, knowledge, compiler=self.compiler)
        self.knowledge_base.concatenate(cg)

    def consider(self, knowledge):
        considered = ConceptGraph(knowledge, namespace='_tmp_')
        self.working_memory.concatenate(considered)

    def infer(self, rules=None):
        if rules is None:
            solutions = self.inference_engine.infer(self.working_memory)
        else:
            solutions = self.inference_engine.infer(self.working_memory, rules=rules)
        return solutions

    def apply_inferences(self, inferences=None):
        self.inference_engine.apply(inferences)

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

    def apply_resolutions(self, resolutions=None):
        for reference, referents in resolutions: # Todo: standardize resolution result format
            if len(referents) == 1:
                self.merge([[reference, referents[0]]])
        # Done?

    def logical_merge(self):
        # Todo: logical merge
        return

    def update_salience(self):
        return

    # Todo: integrate pull from WorkingMemory

if __name__ == '__main__':
    print(IntelligenceCoreSpec.verify(IntelligenceCore))



