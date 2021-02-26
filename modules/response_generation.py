
from GRIDD.data_structures.concept_graph import ConceptGraph
from collections import defaultdict

prefix = 'translate Graph to English: '
exclusions={'var', 'is_type', 'ref', 'def', 'span', 'datetime', 'predicate', 'unknown_verb', 'unknown_noun',
            'unknown_pron', 'unknown_adj', 'unknown_adv', 'unknown_other'}

class ResponseGeneration:

    def __init__(self, nlg_model=None, device='cpu'):
        self.nlg_model = nlg_model
        self.device = device

    def convert(self, main_predicate, supporting_predicates):
        cg = ConceptGraph(predicates=[main_predicate]+supporting_predicates)
        strings = defaultdict(str)
        preds = ['type', 'instantiative', 'referential', 'question']
        pred = preds[0]
        for s, t, o, i in cg.predicates(predicate_type=pred):
            if s not in exclusions and o not in exclusions:
                if (s == 'user' and o == 'person') or (s == 'emora' and o == 'bot'):
                    pass
                elif o is not None:
                    type_preds = set(cg.predicates(predicate_type='type', object=s))
                    if len(cg.predicates(predicate_type=s)) == 0 and len(type_preds) == 0:
                        strings[pred] += '%s / %s ( %s , %s ) ' % (i, t, s, o)
                else:
                    raise Exception('Type predicates must have an object!')
        for pred in preds[1:]:
            if exclusions is None or pred not in exclusions:
                for s, t, o, i in cg.predicates(predicate_type=pred):
                    if s not in exclusions and o not in exclusions:
                        if o is not None:
                            strings[pred] += '%s / %s ( %s , %s ) ' % (i, t, s, o)
                        else:
                            strings[pred] += '%s / %s ( %s ) ' % (i, t, s)
        strings['mono'] = ''
        strings['bi'] = ''
        for s, t, o, i in cg.predicates():
            if (exclusions is None or (
                    t not in exclusions and s not in exclusions and o not in exclusions)) and t not in preds:
                if o is not None:
                    strings['bi'] += '%s / %s ( %s , %s ) ' % (i, t, s, o)
                else:
                    strings['mono'] += '%s / %s ( %s ) ' % (i, t, s)
        full_string = ' '.join(strings.values())
        return full_string.strip()

    def __call__(self, main_predicate, supporting_predicates, aux_state):
        response = ""
        turn_idx = aux_state.get('turn_index', None)
        if turn_idx is not None and int(turn_idx) == 0:
            response += 'Hi, this is an Alexa Prize Socialbot. '
        output = self.convert(main_predicate, supporting_predicates)
        print(type(self.nlg_model))
        if self.nlg_model is not None:
            print('Running NLG model...')
            try:
                encoding = self.nlg_model.tokenizer.prepare_seq2seq_batch([prefix + output.rstrip('\n')], max_length=512,
                                                                 max_target_length=384, return_tensors="pt").data
                encoding["input_ids"] = encoding["input_ids"].to(self.device)
                encoding["attention_mask"] = encoding["attention_mask"].to(self.device)
                output = self.nlg_model.test_step(encoding)[0]
            except Exception as e:
                print('FAILED! %s' % e)
                output = "Well, I am not sure what to say to that. What else do you want to talk about?"
        response += output
        return response