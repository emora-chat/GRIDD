
class SalienceResponseSelection:

    def __call__(self, working_memory):
        """
        Select the main predicate for the response s.t. it has max salience and no cover
        """
        options = [(node,salience) for node,salience in working_memory.features['salience'].items()
                   if working_memory.has(predicate_id=node)
                   and working_memory.type(node) not in {'type'}
                   and not working_memory.features['cover'].get(node, 0.0)]
        salience_order = sorted(options, key=lambda x: x[1], reverse=True)
        return working_memory.predicate(salience_order[0][0])