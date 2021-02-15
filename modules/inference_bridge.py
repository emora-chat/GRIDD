
class InferenceBridge:

    def __call__(self, implication_cgs, working_memory):
        """
        Add implications to working memory
        """
        # todo - how to set inference salience???
        for cg in implication_cgs:
            mapped_ids = working_memory.concatenate(cg)
            for id in mapped_ids.values():
                working_memory.features['salience'][id] = \
                    max(working_memory.features['salience'].get(id, 0.0), 0.5)
        return working_memory