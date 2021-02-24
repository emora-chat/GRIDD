from GRIDD.data_structures.knowledge_base import KnowledgeBase
from GRIDD.data_structures.working_memory import WorkingMemory
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.pipeline import Pipeline
c = Pipeline.component

from GRIDD.data_structures.span import Span

from os.path import join
import json

QUICK_LOCAL_TESTING = True

kb = join('GRIDD', 'resources', 'kg_files', 'kb')
KB = KnowledgeBase(kb)

class ChatbotServer:
    """
    Implementation of full chatbot pipeline in server architecture.
    """
    def __init__(self, rules, device='cpu'):
        self.nlp_processing = self.init_nlp_processing()
        self.utter_conversion = self.init_utter_conversion(device)
        self.utter_integration = self.init_utter_integration()
        self.dialogue_inference = self.init_dialogue_inference(rules)
        self.response_selection = self.init_response_selection()
        self.response_generation = self.init_response_generation()

    def init_nlp_processing(self):
        from GRIDD.modules.elit_models import ElitModels
        if QUICK_LOCAL_TESTING is False:
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

    def init_utter_conversion(self, device):
        from GRIDD.modules.elit_dp_to_logic_model import ElitDPToLogic
        template_file = join('GRIDD', 'resources', 'kg_files', 'elit_dp_templates.kg')
        elit_dp = c(ElitDPToLogic(KB, template_file, device=device))
        return Pipeline(
            ('tok', 'pos', 'dp') > elit_dp > ('dp_mentions', 'dp_merges'),
            outputs=['dp_mentions', 'dp_merges']
        )

    def init_utter_integration(self):
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

    def init_dialogue_inference(self, rules):
        from GRIDD.modules.inference_rule_based import InferenceRuleBased
        from GRIDD.modules.inference_bridge import InferenceBridge
        inference_rulebased = c(InferenceRuleBased(*rules))
        inference_bridge = c(InferenceBridge())
        return Pipeline(
            ('wm_after_merges', 'aux_state') > inference_rulebased > ('implications', 'aux_state_update'),
            ('implications', 'wm_after_merges') > inference_bridge > ('wm_after_inference'),
            outputs=['wm_after_inference', 'aux_state_update']
        )

    def init_response_selection(self):
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

    def init_response_generation(self):
        from GRIDD.modules.response_generation import ResponseGeneration
        response_generation = c(ResponseGeneration())
        return Pipeline(
            ('main_response', 'supporting_predicates', 'aux_state') > response_generation > ('response'),
            outputs=['response']
        )

    #####
    # Subpipeline components wrapped with serialization handlers
    #####

    def nlp_preprocessing_handler(self, input_dict):
        input = load(input_dict)
        previous_aux = input.get('aux_state', [None, None])[1]
        input["aux_state"] = previous_aux if previous_aux is not None else {'turn_index': 0}
        tok, pos, dp, cr = self.nlp_processing(utter=input["utter"],
                                               aux_state=input["aux_state"])
        return save(tok=tok, pos=pos, dp=dp, cr=cr)

    def utter_conversion_handler(self, input_dict):
        input = load(input_dict)
        dp_mentions, dp_merges = self.utter_conversion(tok=input["tok"],
                                                       pos=input["pos"],
                                                       dp=input["dp"])
        return save(dp_mentions=dp_mentions, dp_merges=dp_merges)

    def utter_integration_handler(self, input_dict):
        input = load(input_dict)
        previous_wm = input.get('wm', [None, None])[1]
        input["wm"] = previous_wm if previous_wm is not None else WorkingMemory(KB, join('GRIDD', 'resources', 'kg_files', 'wm'))
        wm_after_merges = self.utter_integration(dp_mentions=input["dp_mentions"],
                                                 wm=input["wm"],
                                                 dp_merges=input["dp_merges"])
        return save(wm=wm_after_merges)

    def dialogue_inference_handler(self, input_dict):
        input = load(input_dict)
        wm_after_inference, aux_state_update = self.dialogue_inference(wm_after_merges=input["wm"],
                                                                       aux_state=input["aux_state"])
        return save(wm=wm_after_inference, aux_state=aux_state_update)

    def response_selection_handler(self, input_dict):
        input = load(input_dict)
        main_response, supporting_predicates, wm_after_exp = self.response_selection(wm_after_inference=input["wm"],
                                                                                     iterations=input["iterations"])
        return save(main_response=main_response, supporting_predicates=supporting_predicates, wm=wm_after_exp)

    def response_generation_handler(self, input_dict):
        input = load(input_dict)
        response = self.response_generation(main_response=input["main_response"],
                                            supporting_predicates=input["supporting_predicates"],
                                            aux_state=["aux_state"])
        return save(response=response)

    #####
    # Chat
    #####

    def chat(self, utter=None):
        current_state = {}

        while True:
            if utter is None:
                utter = input('User: ')
            if utter == 'stop':
                break

            msg = {'utter': utter}
            msg = self.nlp_preprocessing_handler(msg)
            current_state.update(msg)

            msg = self.utter_conversion_handler(msg)
            current_state.update(msg)

            msg = self.utter_integration_handler(msg)
            current_state.update(msg)

            msg.update({'aux_state': current_state["aux_state"]})
            msg = self.dialogue_inference_handler(msg)
            current_state.update(msg)

            msg = self.response_selection_handler(msg)
            current_state.update(msg)

            msg.update({"aux_state": current_state["aux_state"]})
            msg = self.response_generation_handler(msg)
            current_state.update(msg)

            print(msg)
            print()


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

    chatbot = ChatbotServer(rules=rules)
    chatbot.chat("lets chat")