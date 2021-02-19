
class SalienceResponseSelection:

    def __call__(self, working_memory):
        """
        Select the main predicate for the response s.t. it has max salience and no cover
        """
        options = [(node,features['salience']) for node,features in working_memory.features.items()
                   if working_memory.has(predicate_id=node)
                   and working_memory.type(node) not in {'type'}
                   and not working_memory.features[node].get('cover', 0.0)]
        salience_order = sorted(options, key=lambda x: x[1], reverse=True)
        return working_memory.predicate(salience_order[0][0])