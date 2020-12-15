from subframeworks.text_to_logic_model import TextToLogicModel

from knowledge_base.concept_graph import ConceptGraph
from knowledge_base.knowledge_graph import KnowledgeGraph
import knowledge_base.knowledge_graph as kg
from knowledge_base.working_memory import WorkingMemory

from os.path import join

class AllenAIToLogic(TextToLogicModel):

    def text_to_graph(self, turns, knowledge_base):
        pass


if __name__ == '__main__':
    kb = KnowledgeGraph(join('knowledge_base', 'kg_files', 'framework_test.kg'))
    wm = ConceptGraph(nodes=['is_type'])
    working_memory = WorkingMemory(wm=wm, kb=kb)

    asr_hypotheses = [
        {'text': 'i bought a red house',
         'text_confidence': 0.87,
         'tokens': ['i', 'bought', 'a', 'red', 'house'],
         'token_confidence': {0: 0.90, 1: 0.90, 2: 0.80, 3: 0.80, 4: 0.80}
         }
    ]

    template_file = join('knowledge_base', 'kg_files', 'allen_dp_templates.txt')
    output = AllenAIToLogic(kb, template_file).translate([hypo['text'] for hypo in asr_hypotheses])