
class InferenceBridge:

    def __call__(self, implication_cgs, working_memory):
        """
        Add implications to working memory
        """
        # todo - how to set inference salience???
        inference_salience = 0.5
        for rule_id, cgs in implication_cgs.items():
            for cg in cgs:
                mapped_ids = working_memory.concatenate(cg)
                for id in mapped_ids.values():
                    if working_memory.has(predicate_id=id) and working_memory.type(id) == 'question':
                        working_memory.features[id]['salience'] = inference_salience * 1.5
                    else:
                        working_memory.features[id]['salience'] = max(inference_salience,
                                                                      working_memory.features[id].get('salience', 0.0))
        return working_memory