from GRIDD.modules.response_selection_salience_spec import ResponseSelectionSalienceSpec
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.globals import *

q_play_sports = ConceptGraph('''
p/play(user, s/sport())
time(p, now)
request(emora, s)
''', namespace='bu_')

q_school_subject = ConceptGraph('''
b/be(s/school_subject(), o/school_subject())
time(b, now)
possess(user, s)
property(s, favorite)
request(emora, o)
''', namespace='bu_')

backup_topics = {
    'sports': (list(q_play_sports.predicates(predicate_type='play'))[0], list(q_play_sports.predicates())),
    'school': (list(q_school_subject.predicates(predicate_type='be'))[0], list(q_school_subject.predicates()))
}

class ResponseSelectionSalience:

    def __call__(self, aux_state, working_memory, template_response_selection):
        if template_response_selection[0] is not None:
            # template response takes priority
            responses = [((template_response_selection[0],template_response_selection[1]),
                         template_response_selection[2])]
        else:
            # no nlg model
            # responses = [self.select_acknowledgment(working_memory), self.select_followup(working_memory, aux_state)]
            responses = []
        return aux_state, responses

    def select_acknowledgment(self, working_memory):
        options = [(ack[3], working_memory.features.get(ack[3], {}).get(SALIENCE, 0.0))
                   for ack in working_memory.predicates(predicate_type='ack_conf')
                   if not working_memory.has(ack[3], USER_AWARE)]
        salience_order = sorted(options, key=lambda x: x[1], reverse=True)
        if len(salience_order) > 0:
            return working_memory.predicate(salience_order[0][0]), 'ack_conf'
        else:
            # print('[WARNING] No acknowledgment predicate responses found.')
            return None, None

    def select_followup(self, working_memory, aux_state):
        options = [(node,features[SALIENCE]) for node,features in working_memory.features.items()
                   if features.get(SALIENCE, 0) > 0.0
                   and working_memory.has(predicate_id=node)
                   and ((working_memory.type(node) in {REQ_TRUTH, REQ_ARG} and working_memory.subject(node) == "user")
                        or not working_memory.has(node, USER_AWARE))
                   and working_memory.type(node) not in {'possess', 'referential', 'instantiative', 'ack_conf',
                                                         SPAN_DEF, SPAN_REF, ASSERT, USER_AWARE,
                                                         TIME, EXPR, TYPE, REQ_ARG, REQ_TRUTH, REQ_SAT, REQ_UNSAT}]
        salience_order = sorted(options, key=lambda x: x[1], reverse=True)
        if len(salience_order) > 0:
            return working_memory.predicate(salience_order[0][0]), 'nlg'
        else:
            # pick non-repetitive backup topic
            # print('[WARNING] No followup predicate responses found. Picking backup topic.')
            backups_used = aux_state.get('backups', [])
            options = [x for x in backup_topics if x not in backups_used]
            if len(options) > 0:
                selection = options[0]
                backups_used.append(selection)
                aux_state['backups'] = backups_used
                return backup_topics[selection], 'backup'
            else:
                # print('[WARNING] No non-repetitive backup topics found.')
                return None, 'nlg'

if __name__ == '__main__':
    print(ResponseSelectionSalienceSpec.verify(ResponseSelectionSalience))