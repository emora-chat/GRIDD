import GRIDD.globals as globals

class InferenceBridge:

    def __call__(self, *args, **kwargs):
        """
        Add implications to working memory
        args[0] - list of implication cgs
        args[1] - working memory
        """
        if globals.DEBUG:
            print('You have reached the end of the implemented Pipeline.')
        return '__EXIT__\n'