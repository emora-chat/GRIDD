
class InferenceBridge:

    def __call__(self, implication_cgs, working_memory):
        """
        Add implications to working memory
        """
        for rule_id, cgs in implication_cgs.items():
            for cg in cgs:
                mapped_ids = working_memory.concatenate(cg)
                working_memory.features.update_from_inference(mapped_ids.values(), working_memory)
        return working_memory