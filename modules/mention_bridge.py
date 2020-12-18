from typing import List, Dict
from modules.module import Module

class BaseMentionBridge(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input: Dict, working_memory):
        """
        Merge mention graphs into working_memory and generate span node with span object where span node is connected to focus of mention graph.
        Map span object to span node in WM.span_map.
        :param input: mention output (dictionary of token spans -> mention CGs)
        :return: True, if mention bridge is successful
        """
        new_nodes = set()
        for span_obj, mention_graph in input.items():
            ((sig, inst),) = mention_graph.predicate_instances('focus')
            focus = mention_graph.subject(inst)
            mapped_ids = working_memory.graph.merge(mention_graph)
            new_nodes.update(mapped_ids.values())
            span_node = working_memory.graph._get_next_id()
            working_memory.graph.add_bipredicate(span_node, mapped_ids[focus], 'exprof')
            working_memory.graph.add_bipredicate(span_node, 'span', 'type')
            working_memory.span_map[span_obj] = span_node
        working_memory.graph.pull_types(new_nodes, working_memory.knowledge_base)
        return True
