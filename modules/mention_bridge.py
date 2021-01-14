from typing import List, Dict
from modules.module import Module

class BaseMentionBridge(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input: Dict, working_memory):
        """
        Merge mention graphs into working_memory and generate span node with span object where span node is connected to focus of mention graph.
        Map span object to span node from parsing_to_logic_model
        :param input: mention output (dictionary of token spans -> mention CGs)
        :return: True, if mention bridge is successful
        """
        new_concepts = set()
        span_map = self.framework.nlp_data['dependency parse'][2]
        for span_obj, mention_graph in input.items():
            ((focus,t,o,i,),) = mention_graph.predicates(predicate_type='focus')
            mapped_ids = working_memory.concatenate(mention_graph)
            new_concepts.update(mapped_ids.values())
            span_node = working_memory._get_next_id()
            working_memory.add(span_node, 'exprof', mapped_ids[focus])
            working_memory.add(span_node, 'type', 'span')
            span_map[span_obj] = span_node
        working_memory.pull_ontology(new_concepts)
        return True
