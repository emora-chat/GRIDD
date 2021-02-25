from GRIDD.data_structures.knowledge_base import KnowledgeBase
from GRIDD.data_structures.working_memory import WorkingMemory
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.pipeline import Pipeline
c = Pipeline.component

from GRIDD.data_structures.span import Span

from os.path import join
import json

kb = join('GRIDD', 'resources', 'kg_files', 'kb')
KB = KnowledgeBase(kb)

class ChatbotServer:
    """
    Implementation of full chatbot pipeline in server architecture.
    """
    def initialize_full_pipeline(self, rules, device='cpu'):
        self.nlp_processing = init_nlp_preprocessing()
        self.utter_conversion = init_utter_conversion(device)
        self.utter_integration = init_utter_integration()
        self.dialogue_inference = init_dialogue_inference(rules)
        self.response_selection = init_response_selection()
        self.response_generation = init_response_generation()

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

    def chat(self, static_utter=None):
        current_state = {'utter': [None,None], 'wm': [None,None], 'aux_state': [None,None]}

        while True:
            if static_utter is None:
                utter = input('User: ')
            else:
                utter = static_utter
            if utter == 'stop':
                break

            current_state["utter"][0] = utter
            msg = nlp_preprocessing_handler(self.nlp_processing, self.convert_state(current_state))
            self.update_current_turn_state(current_state, msg)

            msg = utter_conversion_handler(self.utter_conversion, self.convert_state(current_state))
            self.update_current_turn_state(current_state, msg)

            msg = utter_integration_handler(self.utter_integration, self.convert_state(current_state))
            self.update_current_turn_state(current_state, msg)

            msg = dialogue_inference_handler(self.dialogue_inference, self.convert_state(current_state))
            self.update_current_turn_state(current_state, msg)

            msg = response_selection_handler(self.response_selection, self.convert_state(current_state))
            self.update_current_turn_state(current_state, msg)

            msg = response_generation_handler(self.response_generation, self.convert_state(current_state))
            self.update_current_turn_state(current_state, msg)

            print(msg)
            print()

            self.add_new_turn_state(current_state)

            if static_utter is not None:
                break

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
        ('cased_utter', 'aux_state') > elit_models > ('tok', 'pos', 'dp', 'cr'),
        outputs=['tok', 'pos', 'dp', 'cr']
    )

def init_utter_conversion(device):
    from GRIDD.modules.elit_dp_to_logic_model import ElitDPToLogic
    template_file = join('GRIDD', 'resources', 'kg_files', 'elit_dp_templates.kg')
    elit_dp = c(ElitDPToLogic(KB, template_file, device=device))
    return Pipeline(
        ('tok', 'pos', 'dp') > elit_dp > ('dp_mentions', 'dp_merges'),
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
        ('cr', 'wm_after_mentions') > merge_coref > ('coref_merges'),
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
        ('wm_after_prop') > response_selection > ('response_predicate'),
        ('response_predicate', 'wm_after_prop') > response_expansion > ('main_response', 'supporting_predicates', 'wm_after_exp'),
        outputs=['main_response', 'supporting_predicates', 'wm_after_exp']
    )

def init_response_generation():
    from GRIDD.modules.response_generation import ResponseGeneration
    response_generation = c(ResponseGeneration())
    return Pipeline(
        ('main_response', 'supporting_predicates', 'aux_state') > response_generation > ('response'),
        outputs=['response']
    )

##############################
# Serialization handlers of subpiplines
##############################

def nlp_preprocessing_handler(pipeline, input_dict):
    input = {"utter": input_dict["utter"][0], "aux_state": input_dict["aux_state"][1]}
    input = load(input)
    if input["aux_state"] is None:
        input["aux_state"] = {'turn_index': -1}
    input["aux_state"]["turn_index"] += 1
    tok, pos, dp, cr = pipeline(utter=input["utter"], aux_state=input["aux_state"])
    return save(tok=tok, pos=pos, dp=dp, cr=cr, aux_state=input["aux_state"])

def utter_conversion_handler(pipeline, input_dict):
    input = {"tok": input_dict["tok"][0], "pos": input_dict["pos"][0], "dp": input_dict["dp"][0]}
    input = load(input)
    dp_mentions, dp_merges = pipeline(tok=input["tok"], pos=input["pos"], dp=input["dp"])
    return save(dp_mentions=dp_mentions, dp_merges=dp_merges)

def utter_integration_handler(pipeline, input_dict):
    input = {"dp_mentions": input_dict["dp_mentions"][0], "dp_merges": input_dict["dp_merges"][0], "cr": input_dict["cr"][0],
             "wm": input_dict["wm"][1]}
    input = load(input)
    if input["wm"] is None:
        input["wm"] = WorkingMemory(KB, join('GRIDD', 'resources', 'kg_files', 'wm'))
    wm_after_merges = pipeline(dp_mentions=input["dp_mentions"], wm=input["wm"], dp_merges=input["dp_merges"], cr=input["cr"])
    return save(wm=wm_after_merges)

def dialogue_inference_handler(pipeline, input_dict):
    input = {"wm": input_dict["wm"][0], "aux_state": input_dict["aux_state"][0]}
    input = load(input)
    wm_after_inference, aux_state_update = pipeline(wm_after_merges=input["wm"], aux_state=input["aux_state"])
    return save(wm=wm_after_inference, aux_state=aux_state_update)

def response_selection_handler(pipeline, input_dict):
    input = {"wm": input_dict["wm"][0]}
    input = load(input)
    input["iterations"] = 2
    main_response, supporting_predicates, wm_after_exp = pipeline(wm_after_inference=input["wm"], iterations=input["iterations"])
    return save(main_response=main_response, supporting_predicates=list(supporting_predicates), wm=wm_after_exp)

def response_generation_handler(pipeline, input_dict):
    input = {"main_response": input_dict["main_response"][0], "supporting_predicates": input_dict["supporting_predicates"][0], "aux_state": input_dict["aux_state"][0]}
    input = load(input)
    response = pipeline(main_response=input["main_response"], supporting_predicates=input["supporting_predicates"], aux_state=input["aux_state"])
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
                new_d[span.to_string()] = cg.save()
            value = new_d
        data[key] = json.dumps(value, cls=DataEncoder)
    return data

def load(json_dict):
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
            elif key == 'tok':
                value = json.loads(value) if isinstance(value, str) else value
                json_dict[key] = [Span.from_string(obj) for obj in value]
            elif key in {'pos', 'dp', 'main_response', 'supporting_predicates', 'response'}:
                json_dict[key] = json.loads(value) if isinstance(value, str) else value
            elif key == 'cr':
                value = json.loads(value) if isinstance(value, str) else value
                if 'global_tokens' in value:
                    value['global_tokens'] = [Span.from_string(obj) for obj in value['global_tokens']]
                json_dict[key] = value
            elif key == 'dp_mentions':
                value = json.loads(value) if isinstance(value, str) else value
                new_d = {}
                for span_str, cg_dict in value.items():
                    cg = ConceptGraph(namespace=cg_dict["namespace"])
                    cg.id_map().index = cg_dict["next_id"]
                    cg.load(cg_dict)
                    new_d[Span.from_string(span_str)] = cg
                json_dict[key] = new_d
            elif key == 'dp_merges':
                value = json.loads(value) if isinstance(value, str) else value
                new_pairs = [[(Span.from_string(pair[0][0]), pair[0][1]), (Span.from_string(pair[1][0]), pair[1][1])]
                             for pair in value]
                json_dict[key] = new_pairs
    return json_dict

class DataEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Span):
            return obj.to_string()
        elif isinstance(obj, ConceptGraph):
            return obj.save()
        return json.JSONEncoder.default(self, object)




if __name__ == '__main__':
    rules_dir = join('GRIDD', 'resources', 'kg_files', 'rules')
    rules = [rules_dir]

    chatbot = ChatbotServer()
    chatbot.initialize_full_pipeline(rules=rules, device='cpu')
    chatbot.chat()