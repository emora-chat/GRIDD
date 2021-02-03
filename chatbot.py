from GRIDD.chatbot_spec import ChatbotSpec

QUICK_LOCAL_TESTING = True

import warnings
warnings.filterwarnings('ignore')
import time
from os.path import join
import json

from GRIDD.data_structures.knowledge_base import KnowledgeBase
from GRIDD.data_structures.working_memory import WorkingMemory
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.span import Span

from GRIDD.data_structures.pipeline import Pipeline

from GRIDD.modules.elit_models import ElitModels
from GRIDD.modules.elit_dp_to_logic_model import ElitDPToLogic, NODES, DP_LABELS
from GRIDD.modules.merge_span_to_merge_concept import MergeSpanToMergeConcept
from GRIDD.modules.inference_rule_based import InferenceRuleBased
from GRIDD.modules.mention_bridge import MentionBridge
from GRIDD.modules.merge_bridge import MergeBridge
from GRIDD.modules.inference_bridge import InferenceBridge
from GRIDD.modules.merge_coreference import MergeCoreference

if QUICK_LOCAL_TESTING is False:
    from GRIDD.modules.sentence_casing import SentenceCaser
else:
    SentenceCaser = (lambda: (lambda x, y: x))

class Chatbot:
    """
    Implementation of full chatbot pipeline. Instantiate and chat!
    """

    def __init__(self, *knowledge_base):
        self.knowledge_base = KnowledgeBase(*knowledge_base)
        self.working_memory = WorkingMemory(self.knowledge_base)
        self.auxiliary_state = {'turn_index': 0}

        c = Pipeline.component
        elit_models = c(ElitModels())
        template_starter_predicates = [(n, 'is_type') for n in NODES+DP_LABELS]
        template_file = join('GRIDD', 'resources', 'kg_files', 'elit_dp_templates.kg')
        elit_dp = c(ElitDPToLogic(self.knowledge_base, template_starter_predicates, template_file))
        mention_bridge = c(MentionBridge())
        merge_dp = c(MergeSpanToMergeConcept())
        merge_bridge = c(MergeBridge(threshold_score=0.2))
        inference_rulebased = c(
            InferenceRuleBased([join('GRIDD', 'resources', 'kg_files', 'test_inferences.kg')]))
        inference_bridge = c(InferenceBridge())
        sentence_caser = c(SentenceCaser())
        merge_coref = c(MergeCoreference())

        self.pipeline = Pipeline(
            ('utter', 'wm') > sentence_caser > ('cased_utter'),
            ('cased_utter', 'aux_state') > elit_models > ('tok', 'pos', 'dp', 'cr'),
            ('tok', 'pos', 'dp') > elit_dp > ('dp_mentions', 'dp_merges'),
            ('dp_mentions', 'wm') > mention_bridge > ('wm_after_mentions'),
            ('dp_merges', 'wm_after_mentions') > merge_dp > ('dp_node_merges'),
            ('cr', 'wm_after_mentions') > merge_coref > ('coref_merges'),
            ('wm_after_mentions', 'dp_node_merges', 'coref_merges') > merge_bridge > ('wm_after_merges'),
            ('wm_after_merges') > inference_rulebased > ('implications'),
            ('implications', 'wm_after_merges') > inference_bridge > ('wm_after_inference'),
            tags ={
                sentence_caser: ['sentence_caser'],
                elit_models: ['elit_models'],
                elit_dp: ['elit_dp'],
                mention_bridge: ['mention_bridge'],
                merge_dp: ['merge_dp'],
                merge_bridge: ['merge_bridge']
            },
            outputs=['wm_after_inference', 'cr']
        )

    def respond(self, user_utterance=None, dialogue_state=None):
        if dialogue_state is not None:
            self.load(dialogue_state)
        output, coref_context = self.pipeline(
            user_utterance,
            self.working_memory,
            self.auxiliary_state
        )
        self.auxiliary_state['coref_context'] = coref_context
        self.auxiliary_state['system_utterane'] = output
        self.auxiliary_state['turn_index'] += 1

        return output

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

if __name__ == '__main__':
    import GRIDD.globals as globals
    globals.DEBUG = True

    interactive = True

    if interactive:
        chatbot = Chatbot(join('GRIDD', 'resources', 'kg_files', 'framework_test.kg'))
        chatbot.respond('I bought a new house and I love it')
        chatbot.respond('It is pretty big and it has a pool in the back')
    else:
        print(ChatbotSpec.verify(Chatbot))

