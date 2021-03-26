from GRIDD.data_structures.knowledge_base import KnowledgeBase
from GRIDD.data_structures.working_memory import WorkingMemory
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.pipeline import Pipeline
c = Pipeline.component

from GRIDD.data_structures.span import Span

from os.path import join
import json, requests

##############################
# Subpipeline initializations
##############################

def init_nlp_preprocessing(local_testing=True):
    from GRIDD.modules.elit_models import ElitModels
    if not local_testing:
        from GRIDD.modules.sentence_casing import SentenceCaser
    else:
        SentenceCaser = (lambda: (lambda x: x))
    sentence_caser = c(SentenceCaser())
    elit_models = c(ElitModels())
    return Pipeline(
        ('utter') > sentence_caser > ('cased_utter'),
        ('cased_utter', 'aux_state') > elit_models > ('elit_results'),
        outputs=['elit_results']
    )

def init_utter_conversion(device, KB):
    from GRIDD.modules.elit_dp_to_logic_model import ElitDPToLogic
    template_file = join('GRIDD', 'resources', 'kg_files', 'elit_dp_templates.kg')
    elit_dp = c(ElitDPToLogic(KB, template_file, device=device))
    return Pipeline(
        ('elit_results') > elit_dp > ('dp_mentions', 'dp_merges'),
        outputs=['dp_mentions', 'dp_merges']
    )

def init_utter_integration():
    from GRIDD.modules.merge_span_to_merge_concept import MergeSpanToMergeConcept
    from GRIDD.modules.mention_bridge import MentionBridge
    from GRIDD.modules.merge_coreference import MergeCoreference
    from GRIDD.modules.merge_bridge import MergeBridge
    mention_bridge = c(MentionBridge())
    merge_dp = c(MergeSpanToMergeConcept())
    merge_coref = c(MergeCoreference())
    merge_bridge = c(MergeBridge(threshold_score=0.2))
    return Pipeline(
        ('dp_mentions', 'wm') > mention_bridge > ('wm_after_mentions'),
        ('dp_merges', 'wm_after_mentions') > merge_dp > ('dp_node_merges'),
        ('elit_results', 'wm_after_mentions') > merge_coref > ('coref_merges'),
        ('wm_after_mentions', 'dp_node_merges') > merge_bridge > ('wm_after_merges'),
        outputs=['wm_after_merges']
    )

def init_dialogue_inference(rules):
    from GRIDD.modules.inference_rule_based import InferenceRuleBased
    from GRIDD.modules.inference_bridge import InferenceBridge
    inference_rulebased = c(InferenceRuleBased(*rules))
    inference_bridge = c(InferenceBridge())
    return Pipeline(
        ('wm_after_merges', 'aux_state') > inference_rulebased > ('implications', 'aux_state_update'),
        ('implications', 'wm_after_merges') > inference_bridge > ('wm_after_inference'),
        outputs=['wm_after_inference', 'aux_state_update']
    )

def init_response_selection():
    from GRIDD.modules.feature_propogation import FeaturePropogation
    from GRIDD.modules.response_selection_salience import SalienceResponseSelection
    from GRIDD.modules.response_expansion import ResponseExpansion
    feature_propogation = c(FeaturePropogation(max_score=1.0, turn_decrement=0.1, propogation_rate=0.5, propogation_decrement=0.1))
    response_selection = c(SalienceResponseSelection())
    response_expansion = c(ResponseExpansion())
    return Pipeline(
        ('wm_after_inference', 'iterations') > feature_propogation > ('wm_after_prop'),
        ('wm_after_prop') > response_selection > ('response_predicates'),
        ('response_predicates', 'wm_after_prop') > response_expansion > ('expanded_response_predicates', 'wm_after_exp'),
        outputs=['expanded_response_predicates', 'wm_after_exp']
    )

def init_response_acknowledgment():
    from GRIDD.modules.response_acknowledgment import ResponseAcknowledgment
    response_acknowledgment = c(ResponseAcknowledgment())
    return Pipeline(
        ('expanded_response_predicates', 'aux_state') > response_acknowledgment > ('ack_responses'),
        outputs=['ack_responses']
    )

def init_response_generation(nlg_model=None, device='cpu'):
    from GRIDD.modules.response_generation import ResponseGeneration
    response_generation = c(ResponseGeneration(nlg_model, device))
    return Pipeline(
        ('expanded_response_predicates') > response_generation > ('nlg_responses'),
        outputs=['nlg_responses']
    )

def init_response_assembler():
    from GRIDD.modules.response_assembler import ResponseAssembler
    response_assembler = c(ResponseAssembler())
    return Pipeline(
        ('aux_state', 'ack_responses', 'nlg_responses') > response_assembler > ('response'),
        outputs=['response']
    )

##############################
# Serialization handlers of subpiplines
##############################

def nlp_preprocessing_handler(pipeline, input_dict, local=False):
    if local:
        # print('Connecting to remote ELIT model...')
        input_dict["text"] = input_dict["utter"]
        del input_dict["utter"]
        input_dict["conversationId"] = 'local'
        response = requests.post('http://cobot-LoadB-2W3OCXJ807QG-1571077302.us-east-1.elb.amazonaws.com',
                                 data=json.dumps(input_dict),
                                 headers={'content-type': 'application/json'},
                                 timeout=3.0)
        elit_results = json.loads(response.json()["context_manager"]['elit_results'])
        print(input_dict["text"][0])
        print(elit_results['lem'])
        print(elit_results['pos'])
        print(elit_results['tok'])
        print(elit_results['dep'])
        return response.json()["context_manager"]
    else:
        input = {"utter": input_dict.get("utter",[None])[0].strip(), "aux_state": input_dict.get("aux_state",[None])[1]}
        input = load(input)
        if input["aux_state"] is None:
            input["aux_state"] = {'turn_index': -1}
        input["aux_state"]["turn_index"] += 1
        elit_results = {}
        if input["utter"] is not None and len(input["utter"]) > 0:
            elit_results = pipeline(utter=input["utter"], aux_state=input["aux_state"])
        return save(elit_results=elit_results, aux_state=input["aux_state"])

def utter_conversion_handler(pipeline, input_dict):
    input = {"elit_results": input_dict.get("elit_results",[{}])[0]}
    input = load(input)
    dp_mentions,dp_merges={},[]
    if input["elit_results"] is not None and len(input["elit_results"]) > 0:
        dp_mentions, dp_merges = pipeline(elit_results=input["elit_results"])
    return save(dp_mentions=dp_mentions, dp_merges=dp_merges)

def utter_integration_handler(pipeline, input_dict, KB, load_coldstarts=True):
    input = {"dp_mentions": input_dict.get("dp_mentions",[{}])[0], "dp_merges": input_dict.get("dp_merges",[[]])[0],
             "elit_results": input_dict.get("elit_results",[{}])[0],
             "wm": input_dict.get("wm",[None])[1]}
    input = load(input, KB)
    if input["wm"] is None:
        if load_coldstarts:
            input["wm"] = WorkingMemory(KB, join('GRIDD', 'resources', 'kg_files', 'wm'))
        else:
            input["wm"] = WorkingMemory(KB)
    wm_after_merges = pipeline(dp_mentions=input["dp_mentions"], wm=input["wm"],
                               dp_merges=input["dp_merges"], elit_results=input["elit_results"])
    return save(wm=wm_after_merges)

def dialogue_inference_handler(pipeline, input_dict, KB):
    input = {"wm": input_dict.get("wm",[None])[0], "aux_state": input_dict.get("aux_state",[{}])[0]}
    input = load(input, KB)
    wm_after_inference, aux_state_update = pipeline(wm_after_merges=input["wm"], aux_state=input["aux_state"])
    return save(wm=wm_after_inference, aux_state=aux_state_update)

def response_selection_handler(pipeline, input_dict, KB):
    input = {"wm": input_dict.get("wm",[None])[0]}
    input = load(input, KB)
    input["iterations"] = 2
    expanded_response_predicates, wm_after_exp = pipeline(wm_after_inference=input["wm"], iterations=input["iterations"])
    return save(expanded_response_predicates=expanded_response_predicates, wm=wm_after_exp)

def response_acknowledgment_handler(pipeline, input_dict):
    input = {"aux_state": input_dict.get("aux_state", [{}])[0],
            "expanded_response_predicates": input_dict.get("expanded_response_predicates", [[(None, [])]])[0]}
    input = load(input)
    ack_responses = pipeline(aux_state=input["aux_state"], expanded_response_predicates=input["expanded_response_predicates"])
    return save(ack_responses=ack_responses)

def response_generation_handler(pipeline, input_dict, local=False):
    if False: #local:
        # print('Connecting to remote NLG model...')
        input_dict["conversationId"] = 'local'
        response = requests.post('http://cobot-LoadB-1L3YPB9TGV71P-1610005595.us-east-1.elb.amazonaws.com',
                                 data=json.dumps(input_dict),
                                 headers={'content-type': 'application/json'},
                                 timeout=3.0)
        response = response.json()
        if "performance" in response:
            del response["performance"]
            del response["error"]
        return response
    else:
        input = {"expanded_response_predicates": input_dict.get("expanded_response_predicates", [[(None,[])]])[0]}
        input = load(input)
        nlg_responses = pipeline(expanded_response_predicates=input["expanded_response_predicates"])
        return save(nlg_responses=nlg_responses)

def response_assembler_handler(pipeline, input_dict):
    input = {"aux_state": input_dict.get("aux_state", [{}])[0],
             "ack_responses": input_dict.get("ack_responses", [[None]])[0],
             "nlg_responses": input_dict.get("nlg_responses", [[None]])[0],}
    input = load(input)
    response = pipeline(aux_state=input["aux_state"], ack_responses=input["ack_responses"], nlg_responses=input["nlg_responses"])
    return save(response=response)

##############################
# Serialization functions
##############################

def save(**data):
    for key, value in data.items():
        if isinstance(key, str) and key.startswith('wm'):
            value = value.save()
        elif key == 'aux_state':
            coref_context = value.get('coref_context', None)
            if coref_context is not None:
                global_tokens = coref_context.get('global_tokens', [])
                global_tokens = [span.to_string() for span in global_tokens]
                coref_context['global_tokens'] = global_tokens
                value['coref_context'] = coref_context if len(coref_context) > 0 else None
        elif key == 'dp_mentions':
            new_d = {}
            for span,cg in value.items():
                new_d[span] = cg.save()
            value = new_d
        data[key] = json.dumps(value, cls=DataEncoder)
    return data

def load(json_dict, KB=None):
    for key, value in json_dict.items():
        if value is not None:
            if isinstance(key, str) and key.startswith('wm'):
                value = json.loads(value) if isinstance(value, str) else value
                working_memory = WorkingMemory(KB)
                ConceptGraph.load(working_memory, value)
                json_dict[key] = working_memory
            elif key == 'aux_state':
                value = json.loads(value) if isinstance(value, str) else value
                coref_context = value.get('coref_context', None)
                if coref_context is not None:
                    global_tokens = coref_context.get('global_tokens', [])
                    global_tokens = [Span.from_string(span) for span in global_tokens]
                    coref_context['global_tokens'] = global_tokens
                    value['coref_context'] = coref_context if len(coref_context) > 0 else None
                json_dict[key] = value
            elif key == 'elit_results':
                json_dict[key] = json.loads(value) if isinstance(value, str) else value
                if 'tok' in json_dict[key]:
                    json_dict[key]['tok'] = [Span.from_string(t) for t in json_dict[key]['tok']]
            elif key in {'expanded_response_predicates', 'ack_responses', 'nlg_responses', 'response'}:
                json_dict[key] = json.loads(value) if isinstance(value, str) else value
            elif key == 'dp_mentions':
                value = json.loads(value) if isinstance(value, str) else value
                new_d = {}
                for span_str, cg_dict in value.items():
                    cg = ConceptGraph(namespace=cg_dict["namespace"])
                    cg.id_map().index = cg_dict["next_id"]
                    cg.load(cg_dict)
                    new_d[span_str] = cg
                json_dict[key] = new_d
            elif key == 'dp_merges':
                value = json.loads(value) if isinstance(value, str) else value
                json_dict[key] = value
    return json_dict

class DataEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Span):
            return obj.to_string()
        elif isinstance(obj, ConceptGraph):
            return obj.save()
        return json.JSONEncoder.default(self, object)

##############################
# Chatbot Server Simulation
##############################

class ChatbotServer:
    """
    Implementation of full chatbot pipeline in server architecture.
    """
    def initialize_full_pipeline(self, kb_files, rules, device='cpu', local=False, debug=False):
        self.local = local
        self.debug = debug
        self.kb = KnowledgeBase(*kb_files)
        self.nlp_processing = None
        if not self.local:
            self.nlp_processing = init_nlp_preprocessing()
        self.utter_conversion = init_utter_conversion(device, self.kb)
        self.utter_integration = init_utter_integration()
        self.dialogue_inference = init_dialogue_inference(rules)
        self.response_selection = init_response_selection()
        self.response_acknowledgment = init_response_acknowledgment()
        self.response_generation = init_response_generation()
        self.response_assembler = init_response_assembler()

    def initialize_nlu(self, kb_files, device='cpu', local=False):
        self.local = local
        self.kb = KnowledgeBase(*kb_files)
        self.nlp_processing = None
        if not self.local:
            self.nlp_processing = init_nlp_preprocessing()
        self.utter_conversion = init_utter_conversion(device, self.kb)
        self.utter_integration = init_utter_integration()

    def run_nlu(self, utterance, display=True):
        if display:
            print('-' * 20)
            print(utterance)
            print('-'*20)
        current_state = {'utter': [None, None], 'wm': [None, None], 'aux_state': [None, None]}
        current_state["utter"][0] = utterance
        msg = nlp_preprocessing_handler(self.nlp_processing, self.convert_state(current_state), local=self.local)
        self.update_current_turn_state(current_state, msg)

        msg = utter_conversion_handler(self.utter_conversion, self.convert_state(current_state))
        self.update_current_turn_state(current_state, msg)

        msg = utter_integration_handler(self.utter_integration, self.convert_state(current_state),
                                        self.kb, load_coldstarts=False)
        self.update_current_turn_state(current_state, msg)

        saved_wm = json.loads(msg["wm"])
        working_memory = WorkingMemory(self.kb)
        ConceptGraph.load(working_memory, saved_wm)
        if display:
            print(working_memory.ugly_print(exclusions={'is_type', 'object', 'predicate', 'entity', 'post', 'pre',
                                                        'def', 'span', 'datetime'}))
            print()
        return working_memory

    def add_new_turn_state(self, current_state):
        for key in current_state:
            current_state[key].insert(0, None)

    def update_current_turn_state(self, current_state, new_vals):
        for key, value in new_vals.items():
            if key not in current_state:
                current_state[key] = [value, None]
            else:
                current_state[key][0] = value

    def convert_state(self, current_state, history_turns=1):
        converted = {key: values[0:history_turns+1] for key, values in current_state.items()}
        return converted

    def chat(self, static_utter=None, load_coldstarts=True):
        current_state = {'utter': [None,None], 'wm': [None,None], 'aux_state': [None,None]}

        while True:
            print('-' * 10)
            if static_utter is None:
                utter = input('User: ')
            else:
                utter = static_utter
            if utter == 'stop':
                break

            current_state["utter"][0] = utter
            msg = nlp_preprocessing_handler(self.nlp_processing, self.convert_state(current_state), local=self.local)
            self.update_current_turn_state(current_state, msg)

            msg = utter_conversion_handler(self.utter_conversion, self.convert_state(current_state))
            self.update_current_turn_state(current_state, msg)

            msg = utter_integration_handler(self.utter_integration, self.convert_state(current_state),
                                            self.kb, load_coldstarts=load_coldstarts)
            self.update_current_turn_state(current_state, msg)

            if self.debug:
                print('\nWorking Memory after Utterance Integration:')
                saved_wm = json.loads(msg["wm"])
                working_memory = WorkingMemory(self.kb)
                ConceptGraph.load(working_memory, saved_wm)
                print(working_memory.ugly_print(exclusions={'is_type', 'object', 'predicate', 'entity', 'post', 'pre',
                                                            'def', 'span', 'datetime'}))
                print()

            msg = dialogue_inference_handler(self.dialogue_inference, self.convert_state(current_state), self.kb)
            self.update_current_turn_state(current_state, msg)

            if self.debug:
                print('\nWorking Memory after Inference:')
                saved_wm = json.loads(msg["wm"])
                working_memory = WorkingMemory(self.kb)
                ConceptGraph.load(working_memory, saved_wm)
                print(working_memory.ugly_print(exclusions={'is_type', 'object', 'predicate', 'entity', 'post', 'pre',
                                                            'def', 'span', 'datetime'}))
                print()

            msg = response_selection_handler(self.response_selection, self.convert_state(current_state), self.kb)
            self.update_current_turn_state(current_state, msg)
            print('Selections:')
            for selection in json.loads(msg["expanded_response_predicates"]):
                print('\t', selection[0])
                for support in selection[1]:
                    print('\t', support)
                print()

            msg = response_acknowledgment_handler(self.response_acknowledgment, self.convert_state(current_state))
            self.update_current_turn_state(current_state, msg)

            msg = response_generation_handler(self.response_generation, self.convert_state(current_state), local=self.local)
            self.update_current_turn_state(current_state, msg)

            msg = response_assembler_handler(self.response_assembler, self.convert_state(current_state))
            self.update_current_turn_state(current_state, msg)

            print('Response:')
            if "response" in msg:
                print('\t', msg["response"])
            else:
                print('\t', msg["message"])
            print()

            self.add_new_turn_state(current_state)

            if static_utter is not None:
                break

if __name__ == '__main__':
    kb_dir = join('GRIDD', 'resources', 'kg_files', 'kb')
    kb = [kb_dir]
    rules_dir = join('GRIDD', 'resources', 'kg_files', 'rules')
    rules = [rules_dir]

    chatbot = ChatbotServer()
    chatbot.initialize_full_pipeline(kb_files=kb, rules=rules, device='cpu',
                                     local=True, debug=True)
    chatbot.chat(load_coldstarts=True)