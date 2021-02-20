import GRIDD.globals as globals
from collections import defaultdict
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.utilities import collect

class InferenceRuleBased:

    def __init__(self, *infer_files):
        # rule_logic_strings = [chunk.strip() for string in collect(*infer_files, extension='.kg')
        #                       for chunk in string.split(';') if len(chunk.strip()) > 0]
        self.inference_engine = InferenceEngine(*infer_files)

    def __call__(self, working_memory, aux_state):
        """
        Gather implications of applying inference rules to working memory.
        Ignore all implications that are derived from inferences already covered in auxiliary_state['inference_memory'].
        """
        inference_dict = self.inference_engine.infer(working_memory)
        inference_memory = aux_state.get('inference_memory', {})

        new_solutions = defaultdict(list)
        for rule_id, (pre, post, solutions) in inference_dict.items():
            new = []
            old_sols = inference_memory.get(rule_id, [])
            if len(old_sols) > 0:
                old_sols = old_sols[2]
            for solution in solutions:
                repeat = False
                for old in old_sols:
                    if solution == old:
                        repeat = True
                        break
                if not repeat:
                    new.append(solution)
            if len(new) > 0:
                new_solutions[rule_id] = (pre, post, new)
                if rule_id not in inference_memory:
                    inference_memory[rule_id] = (pre, post, new)
                else:
                    inference_memory[rule_id][2].extend(new)

        implications = self.inference_engine.apply(solutions=new_solutions)
        if globals.DEBUG:
            self.display_implications(implications)
        return implications, inference_memory

    def display_implications(self, implications):
        print("\n<< Inferences >>")
        for rule_id, cgs in implications.items():
            for cg in cgs:
                print(cg.pretty_print())
                print('*'*20 + '\n')
