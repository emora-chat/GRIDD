from knowledge_base.knowledge_graph import KnowledgeGraph
from knowledge_base.concept_graph import ConceptGraph
from os.path import join

class WorkingMemory:

    def __init__(self, wm, kb):
        self.knowledge_base = kb
        self.graph = wm
        self.wm_id = 0
        self.wm_tag = 'convo0_'

    def get_next_id(self):
        id = self.wm_tag + str(self.wm_id)
        self.wm_id += 1
        return id


if __name__ == '__main__':
    kb = KnowledgeGraph(join('knowledge_base', 'kg_files', 'framework_test.kg'))
    wm = ConceptGraph(nodes=['is_type'])
    working_memory = WorkingMemory(wm=wm, kb=kb)
    wm.add_node('i')
    working_memory.pull(nodes={'i'}, max_depth=2)
    test = 1