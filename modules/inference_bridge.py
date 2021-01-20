
class InferenceBridge:

    def __call__(self, *args, **kwargs):
        """
        Add implications to working memory
        args[0] - list of implication cgs
        args[1] - working memory
        """
        print('You have reached the end of the implemented Pipeline. It currently only performs NLU and inferences.')
        return '__EXIT__'