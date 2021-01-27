QUICK_LOCAL_TESTING = True

import warnings
warnings.filterwarnings('ignore')
import time
from os.path import join

from data_structures.knowledge_base import KnowledgeBase
from data_structures.working_memory import WorkingMemory

from data_structures.pipeline import Pipeline
from modules.elit_models import ElitModels
from modules.elit_dp_to_logic_model import ElitDPToLogic, NODES, DP_LABELS
from modules.merge_syntax import MergeSyntax
from modules.inference_rule_based import InferenceRuleBased
from modules.mention_bridge import MentionBridge
from modules.merge_bridge import MergeBridge
from modules.inference_bridge import InferenceBridge

if QUICK_LOCAL_TESTING is False:
    from modules.sentence_casing import SentenceCaser
else:
    SentenceCaser = (lambda: (lambda x, y: x))


class Chatbot:
    """
    Implementation of full chatbot pipeline. Instantiate and chat!
    """

    def __init__(self, *knowledge_base):
        self.knowledge_base = KnowledgeBase(*knowledge_base)
        self.working_memory = WorkingMemory(self.knowledge_base)

        elit_models = Pipeline.component(ElitModels())
        template_starter_predicates = [(n, 'is_type') for n in NODES+DP_LABELS]
        template_file = join('GRIDD', 'resources', 'kg_files', 'elit_dp_templates.kg')
        elit_dp = Pipeline.component(ElitDPToLogic(self.knowledge_base, template_starter_predicates, template_file))
        mention_bridge = Pipeline.component(MentionBridge())
        merge_dp = Pipeline.component(MergeSyntax())
        merge_bridge = Pipeline.component(MergeBridge(threshold_score=0.2))
        inference_rulebased = Pipeline.component(
            InferenceRuleBased([join('GRIDD', 'resources', 'kg_files', 'test_inferences.kg')]))
        inference_bridge = Pipeline.component(InferenceBridge())
        sentence_caser = Pipeline.component(SentenceCaser())

        self.pipeline = Pipeline(
            ('utter', 'wm') > sentence_caser > ('cased_utter'),
            ('cased_utter') > elit_models > ('tok', 'pos', 'dp'),
            ('tok', 'pos', 'dp') > elit_dp > ('dp_mentions', 'dp_merges', 'span_dict'),
            ('dp_mentions', 'span_dict', 'wm') > mention_bridge > ('wm_span_dict', 'wm_after_mentions'),
            ('dp_merges', 'wm_span_dict', 'wm_after_mentions') > merge_dp > ('node_merges'),
            ('node_merges', 'wm_after_mentions') > merge_bridge > ('wm_after_merges'),
            ('wm_after_merges') > inference_rulebased > ('implications'),
            ('implications', 'wm_after_merges') > inference_bridge > ('wm_after_inference'),
            tags ={
                sentence_caser: ['sentence_caser'],
                elit_models: ['elit_models'],
                elit_dp: ['elit_dp'],
                mention_bridge: ['mention_bridge'],
                merge_dp: ['merge_dp'],
                merge_bridge: ['merge_bridge']
            }
        )

    def chat(self):
        utterance = input('User: ')
        while utterance != 'q':
            s = time.time()
            output = self.pipeline(utterance, self.working_memory)
            elapsed = time.time() - s
            print('[%.6f s] %s' % (elapsed, output))
            utterance = input('User: ')


if __name__ == '__main__':
    chatbot = Chatbot(join('GRIDD', 'resources', 'kg_files', 'framework_test.kg'))
    chatbot.chat()