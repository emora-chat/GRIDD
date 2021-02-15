from GRIDD.data_structures.score_graph import ScoreGraph

class SalienceResponseSelection:

    def __call__(self, working_memory):
        """
        Select the main predicate for the response based on max salience
        """
        salience_order = sorted(working_memory.features['salience'], key=lambda x: x[1], reverse=True)
        for node in salience_order:
            if working_memory.has(predicate_id=node) and not working_memory.features['cover'].get(node, 0.0):
                return working_memory.predicate(node)