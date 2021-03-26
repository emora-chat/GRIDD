from GRIDD.modules.response_selection_salience_spec import ResponseSelectionSalienceSpec

class SalienceResponseSelection:

    def __call__(self, working_memory):
        responses = [self.select_acknowledgment(working_memory), self.select_followup(working_memory)]
        return responses

    def select_acknowledgment(self, working_memory):
        options = [(ack[3], working_memory.features.get(ack[3], {}).get('salience', 0.0))
                   for ack in working_memory.predicates(predicate_type='ack_conf')
                   if working_memory.features.get(ack[3], {}).get('cover', 0.0) != 1.0]
        salience_order = sorted(options, key=lambda x: x[1], reverse=True)
        if len(salience_order) > 0:
            return working_memory.predicate(salience_order[0][0]), 'ack_conf'
        else:
            print('[WARNING] No predicate responses found.')
            return None, None

    def select_followup(self, working_memory):
        options = [(node,features['salience']) for node,features in working_memory.features.items()
                   if working_memory.has(predicate_id=node)
                   and working_memory.type(node) not in {'type', 'possess', 'referential', 'instantiative'}
                   and working_memory.features[node].get('cover', 0.0) != 1.0]
        salience_order = sorted(options, key=lambda x: x[1], reverse=True)
        if len(salience_order) > 0:
            return working_memory.predicate(salience_order[0][0]), 'nlg'
        else:
            print('[WARNING] No predicate responses found.')
            return None, None

if __name__ == '__main__':
    print(ResponseSelectionSalienceSpec.verify(SalienceResponseSelection))