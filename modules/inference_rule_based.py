from modules.module import Module
from data_structures.knowledge_base import KnowledgeBase

class InferenceRuleBased(Module):

    def __init__(self, name, infer_files):
        super().__init__(name)
        self.inference_files = infer_files

    def run(self, input, working_memory):
        """

        :param input: None object from merge pipeline
        :param working_memory: dialogue graph updated by merge pipeline
        :return: list of implication graphs
        """
        implications = working_memory.implications(*self.inference_files)
        self.display_implications(implications)
        return implications

    def display_implications(self, implications):
        print("\nINFERENCES::")
        for cg in implications:
            for s, t, o, i in cg.predicates():
                if t not in ['var', 'is_type']:
                    if o is not None:
                        print('%s(%s, %s) [%s]'%(t,s,o,i))
                    else:
                        print('%s(%s) [%s]' % (t, s, i))
            print()
