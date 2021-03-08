from GRIDD.chatbot_spec import ChatbotSpec

QUICK_LOCAL_TESTING = True

import warnings
warnings.filterwarnings('ignore')
import time, os, json
from os.path import join

from GRIDD.data_structures.knowledge_base import KnowledgeBase
from GRIDD.data_structures.working_memory import WorkingMemory
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.span import Span

from GRIDD.data_structures.pipeline import Pipeline

from GRIDD.modules.elit_models import ElitModels
from GRIDD.modules.elit_dp_to_logic_model import ElitDPToLogic
from GRIDD.modules.merge_span_to_merge_concept import MergeSpanToMergeConcept
from GRIDD.modules.mention_bridge import MentionBridge
from GRIDD.modules.merge_coreference import MergeCoreference
from GRIDD.modules.merge_bridge import MergeBridge
from GRIDD.modules.inference_rule_based import InferenceRuleBased
from GRIDD.modules.inference_bridge import InferenceBridge
from GRIDD.modules.feature_propogation import FeaturePropogation
from GRIDD.modules.response_selection_salience import SalienceResponseSelection
from GRIDD.modules.response_expansion import ResponseExpansion
from GRIDD.modules.response_generation import ResponseGeneration

if QUICK_LOCAL_TESTING is False:
    from GRIDD.modules.sentence_casing import SentenceCaser
else:
    SentenceCaser = (lambda: (lambda x, y: x))

class Chatbot:
    """
    Implementation of full chatbot pipeline. Instantiate and chat!
    """

    def __init__(self, *knowledge_base, rules, starting_wm=None, device='cpu'):
        self.knowledge_base = KnowledgeBase(*knowledge_base)
        if starting_wm is not None:
            self.working_memory = WorkingMemory(self.knowledge_base, starting_wm)
        else:
            self.working_memory = WorkingMemory(self.knowledge_base)
        self.auxiliary_state = {'turn_index': 0}

        c = Pipeline.component
        sentence_caser = c(SentenceCaser())
        elit_models = c(ElitModels())
        template_file = join('GRIDD', 'resources', 'kg_files', 'elit_dp_templates.kg')
        elit_dp = c(ElitDPToLogic(self.knowledge_base, template_file, device=device))
        mention_bridge = c(MentionBridge())
        merge_dp = c(MergeSpanToMergeConcept())
        merge_coref = c(MergeCoreference())
        merge_bridge = c(MergeBridge(threshold_score=0.2))
        inference_rulebased = c(InferenceRuleBased(*rules))
        inference_bridge = c(InferenceBridge())
        feature_propogation = c(FeaturePropogation(max_score=1.0, turn_decrement=0.1, propogation_rate=0.5, propogation_decrement=0.1))
        response_selection = c(SalienceResponseSelection())
        response_expansion = c(ResponseExpansion())
        response_generation = c(ResponseGeneration())

        # todo - add coref_merges back as input to merge_bridge once module is fixed
        self.pipeline = Pipeline(
            ('utter', 'wm') > sentence_caser > ('cased_utter'),
            ('cased_utter', 'aux_state') > elit_models > ('tok', 'pos', 'dp', 'cr'),
            ('tok', 'pos', 'dp') > elit_dp > ('dp_mentions', 'dp_merges'),
            ('dp_mentions', 'wm') > mention_bridge > ('wm_after_mentions'),
            ('dp_merges', 'wm_after_mentions') > merge_dp > ('dp_node_merges'),
            ('cr', 'wm_after_mentions') > merge_coref > ('coref_merges'),
            ('wm_after_mentions', 'dp_node_merges') > merge_bridge > ('wm_after_merges'),
            ('wm_after_merges', 'aux_state') > inference_rulebased > ('implications', 'aux_state_update'),
            ('implications', 'wm_after_merges') > inference_bridge > ('wm_after_inference'),
            ('wm_after_inference', 'iterations') > feature_propogation > ('wm_after_prop'),
            ('wm_after_prop') > response_selection > ('response_predicate'),
            ('response_predicate', 'wm_after_prop') > response_expansion > ('main_response', 'supporting_predicates', 'wm_after_exp'),
            ('main_response', 'supporting_predicates', 'aux_state_update') > response_generation > ('response'),
            tags ={
                sentence_caser: ['sentence_caser'],
                elit_models: ['elit_models'],
                elit_dp: ['elit_dp'],
                mention_bridge: ['mention_bridge'],
                merge_dp: ['merge_dp'],
                merge_coref: ['merge_coref'],
                merge_bridge: ['merge_bridge']
            },
            outputs=['response', 'wm_after_exp', 'aux_state_update', 'cr']
        )

    def respond(self, user_utterance=None, dialogue_state=None):
        if dialogue_state is not None:
            self.load(dialogue_state)
        response, wm, aux_state_update, coref_context = self.pipeline(
            user_utterance,
            self.working_memory,
            self.auxiliary_state,
            2
        )
        self.auxiliary_state = aux_state_update
        self.auxiliary_state['coref_context'] = coref_context
        self.auxiliary_state['system_utterance'] = response
        self.auxiliary_state['turn_index'] += 1

        self.working_memory = wm

        return response

    def chat(self):
        utterance = input('User: ')
        while utterance != 'q':
            s = time.time()
            response = self.respond(utterance)
            elapsed = time.time() - s
            print('[%.6f s] %s' % (elapsed, response))
            utterance = input('User: ')

    def save(self):
        coref_context = self.auxiliary_state.get('coref_context', {})
        global_tokens = coref_context.get('global_tokens', [])
        global_tokens = [span.to_string() for span in global_tokens]
        coref_context['global_tokens'] = global_tokens
        self.auxiliary_state['coref_context'] = coref_context
        dialogue_state = {
            'working_memory': self.working_memory.save(),
            'aux': self.auxiliary_state
        }
        return dialogue_state

    def load(self, dialogue_state):
        self.working_memory = WorkingMemory(self.knowledge_base)
        dialogue_state = json.loads(dialogue_state)
        ConceptGraph.load(self.working_memory, dialogue_state['working_memory'])
        self.auxiliary_state = dialogue_state['aux']
        coref_context = self.auxiliary_state.get('coref_context', {})
        global_tokens = coref_context.get('global_tokens', [])
        global_tokens = [Span.from_string(span) for span in global_tokens]
        coref_context['global_tokens'] = global_tokens
        self.auxiliary_state['coref_context'] = coref_context

if __name__ == '__main__':
    import GRIDD.globals as globals
    globals.DEBUG = True

    interactive = True

    kb = join('GRIDD', 'resources', 'kg_files', 'kb')
    rules_dir = join('GRIDD', 'resources', 'kg_files', 'rules')
    rules = [rules_dir]
    starting_wm = join('GRIDD', 'resources', 'kg_files', 'wm')
    # rules = [join(rules_dir, file) for file in os.listdir(rules_dir) if file.endswith('.kg')]

    if interactive:
        chatbot = Chatbot(kb, rules=rules, starting_wm=starting_wm)
        chatbot.chat()
    else:
        # print(ChatbotSpec.verify(Chatbot))
        for i in range(1):
            chatbot = Chatbot(kb, rules=rules, starting_wm=starting_wm)
            r = chatbot.respond('I bought a car')
            print('\nResponse: ', r)
            r = chatbot.respond('I bought a house')
            print('\nResponse: ', r)
            print('\n' * 2)
            print('#' * 30)
            print('\n' * 2)
