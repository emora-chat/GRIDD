import GRIDD.globals as globals

class InferenceRuleBased:

    def __init__(self, infer_files):
        self.inference_files = infer_files

    def __call__(self, *args, **kwargs):
        """
        Gather implications of applying inference rules to working memory
        args[0] - working memory
        """
        working_memory = args[0]
        implications = working_memory.infer_and_apply(*self.inference_files)
        if globals.DEBUG:
            self.display_implications(implications)
        return implications

    def display_implications(self, implications):
        print("<< Inferences >>")
        for cg in implications:
            print(cg.pretty_print())
            print('*'*20 + '\n')
