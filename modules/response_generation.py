
from GRIDD.data_structures.concept_graph import ConceptGraph
from collections import defaultdict
import re

prefix = 'translate Graph to English: '
exclusions={'var', 'is_type', 'ref', 'def', 'span', 'datetime', 'predicate', 'unknown_verb', 'unknown_noun',
            'unknown_pron', 'unknown_adj', 'unknown_adv', 'unknown_other'}

class conversiondict:
    ''' Strip out word senses of values in dict'''
    def __init__(self, d):
        self.dict = d

    def get(self, key):
        output = self.dict.get(key, key)
        matches = re.findall('(.+).[a-z]+.[0-9]', output)
        if len(matches) == 1:
            concept = matches[0]
            self.dict[key] = concept
            output = concept
        return output

    def has(self, item):
        return item in self.dict

    def put(self, key, value):
        self.dict[key] = value

class ResponseGeneration:

    def __init__(self, nlg_model=None, device='cpu'):
        self.nlg_model = nlg_model
        self.device = device

    def convert(self, main_predicate, supporting_predicates):
        mx = conversiondict({
            'emora': 'bot'
        })
        cg = ConceptGraph(predicates=[main_predicate]+list(supporting_predicates))
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
                        strings[pred] += '%s / %s ( %s , %s ) ' % (i, mx.get(t), mx.get(s), mx.get(o))
                else:
                    raise Exception('Type predicates must have an object!')
        for pred in preds[1:]:
            if exclusions is None or pred not in exclusions:
                for s, t, o, i in cg.predicates(predicate_type=pred):
                    if s not in exclusions and o not in exclusions:
                        if o is not None:
                            strings[pred] += '%s / %s ( %s , %s ) ' % (i, mx.get(t), mx.get(s), mx.get(o))
                        else:
                            strings[pred] += '%s / %s ( %s ) ' % (i, mx.get(t), mx.get(s))
        strings['mono'] = ''
        strings['bi'] = ''
        for s, t, o, i in cg.predicates():
            if (exclusions is None or (
                    t not in exclusions and s not in exclusions and o not in exclusions)) and t not in preds:
                if o is not None:
                    strings['bi'] += '%s / %s ( %s , %s ) ' % (i, mx.get(t), mx.get(s), mx.get(o))
                else:
                    strings['mono'] += '%s / %s ( %s ) ' % (i, mx.get(t), mx.get(s))
        full_string = ' '.join(strings.values())
        return full_string.strip()

    def __call__(self, main_predicate, supporting_predicates, aux_state):
        response = ""
        turn_idx = aux_state.get('turn_index', None)
        if turn_idx is not None and int(turn_idx) == 0:
            response += 'Hi, this is an Alexa Prize Socialbot. '
        if main_predicate is not None:
            output = self.convert(main_predicate, supporting_predicates)
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
        else:
            return "Well, I am not sure what to say to that. What else do you want to talk about?"