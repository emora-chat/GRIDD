
class ResponseGeneration:

    def __call__(self, main_predicate, supporting_predicates):

        return str(main_predicate) + ' ' + str(supporting_predicates)