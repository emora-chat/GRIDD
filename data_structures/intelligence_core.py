

from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.utilities.utilities import uniquify


class IntelligenceCore:

    def __init__(self, knowledge_base=None, working_memory=None, inference_engine=None):
        self.knowledge_base = ConceptGraph(knowledge_base)  # Todo: concept graph loading
        self.working_memory = ConceptGraph(working_memory)  # Todo: concept graph loading
        self.inference_engine = inference_engine if inference_engine is not None else InferenceEngine()
        self.operators = {}

    def know(self, knowledge):
        self.knowledge_base.concatenate(ConceptGraph(knowledge))

    def consider(self, knowledge):
        considered = ConceptGraph(knowledge)
        # Todo: update salience of considered
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



