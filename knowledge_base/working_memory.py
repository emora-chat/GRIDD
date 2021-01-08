from knowledge_base.knowledge_graph import KnowledgeBase
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

    def pull(self, nodes, max_depth):
        """
        Pull KB predicates into WM for specified nodes

        :param nodes: iterable of nodes to retrieve neighbors for
        :param depth: integer value of retrieved neighborhood depth
        """
        visited = set()
        frontier = [(x, 0) for x in nodes]
        while len(frontier) > 0:
            item = frontier.pop(0)
            if item[0] not in visited:
                if len(item) == 2:
                    node, depth = item
                    visited.add(node)
                    self._update_frontier(frontier, [node], depth, max_depth)
                elif len(item) == 3:
                    node, tuple, depth = item
                    visited.add(node)
                    self._add_tuple_nodes(tuple)
                    if len(tuple) == 3 and tuple[2] == 'type':
                        # for type bipredicate, do not pull connections
                        # only pull type ancestry
                        ancestry = self.knowledge_base._concept_graph.get_all_types(tuple[0], get_predicates=True)
                        for tuple, pred_id in ancestry:
                            self._add_tuple_nodes(tuple)
                            if not self.graph.has(pred_id):
                                self.graph.add_bipredicate(*tuple, predicate_id=pred_id)
                                is_type_inst = list(self.knowledge_base._concept_graph.monopredicate(tuple[1], 'is_type'))[0]
                                if not self.graph.has(is_type_inst):
                                    self.graph.add_monopredicate(tuple[1], 'is_type', predicate_id=is_type_inst)
                    else:
                        if len(tuple) == 3:
                            self.graph.add_bipredicate(*tuple, predicate_id=node)
                        elif len(tuple) == 2:
                            self.graph.add_monopredicate(*tuple, predicate_id=node)
                        self._update_frontier(frontier, list(tuple)+[node], depth, max_depth)
                else:
                    raise Exception('Unexpected element %s in frontier of pull()'%str(item))

    def _update_frontier(self, frontier, nodes, depth, max_depth):
        if depth < max_depth:
            for n in nodes:
                connections = self.knowledge_base._concept_graph.predicate_instances(n)
                frontier.extend([(connection[1], connection[0], depth + 1)
                                 for connection in connections])

    def _add_tuple_nodes(self, tuple):
        for t in tuple:
            if not self.graph.has(t):
                self.graph.add_node(t)

if __name__ == '__main__':
    kb = KnowledgeBase(join('knowledge_base', 'kg_files', 'framework_test.kg'))
    wm = ConceptGraph(nodes=['is_type'])
    working_memory = WorkingMemory(wm=wm, kb=kb)
    wm.add_node('i')
    working_memory.pull(nodes={'i'}, max_depth=2)
    test = 1