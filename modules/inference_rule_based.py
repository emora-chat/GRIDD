import GRIDD.globals as globals
from collections import defaultdict
from GRIDD.data_structures.inference_engine import InferenceEngine

class InferenceRuleBased:

    def __init__(self, infer_files):
        self.inference_engine = InferenceEngine()
        self.rules = infer_files

    def __call__(self, working_memory, aux_state):
        """
        Gather implications of applying inference rules to working memory.
        Ignore all implications that are derived from inferences already covered in auxiliary_state['inference_memory'].
        """

        # todo - maintain solutions that have been used before to prevent reapplying the same inference (rules are generated each turn, rather than loaded ahead of time!)

        inference_dict = working_memory.inferences(*self.rules)
        inference_memory = aux_state.get('inference_memory', defaultdict(list))

        new_solutions = defaultdict(list)
        for rule, solutions in inference_dict.items():
            for solution in solutions:
                repeat = False
                for old in inference_memory[rule]:
                    if solution == old:
                        repeat = True
                        break
                if not repeat:
                    new_solutions[rule].append(solution)
                    inference_memory[rule].append(solution)

        implications = working_memory.apply_implications(new_solutions)
        if globals.DEBUG:
            self.display_implications(implications)
        return implications, inference_memory

    def display_implications(self, implications):
        print("<< Inferences >>")
        for cg in implications:
            print(cg.pretty_print())
            print('*'*20 + '\n')
