from knowledge_base.knowledge_graph import KnowledgeGraph
from knowledge_base.concept_graph import ConceptGraph
from os.path import join
from collections import defaultdict

class WorkingMemory:

    def __init__(self, wm, kb):
        self.knowledge_base = kb
        self.graph = wm
        self.span_map = {}


if __name__ == '__main__':
    kb = KnowledgeGraph(join('knowledge_base', 'kg_files', 'framework_test.kg'))
    wm = ConceptGraph('wm_', nodes=['is_type'])
    working_memory = WorkingMemory(wm=wm, kb=kb)
    wm.add_node('i')
    wm.pull(nodes={'i'}, max_depth=2, kb=kb)
    test = 1