
class MentionBridge:

    def __call__(self, *args, **kwargs):
        """
        Merge mention graphs into working_memory and generate span node with span object where span node is connected to focus of mention graph.
        Map span object to span node from text_to_logic_model
        args[0] - mentions
        args[1] - span dict
        args[2] - working memory
        """
        mentions, span_dict, working_memory = args
        new_concepts = set()
        for span_obj, mention_graph in mentions.items():
            ((focus,t,o,i,),) = mention_graph.predicates(predicate_type='focus')
            mapped_ids = working_memory.concatenate(mention_graph, predicate_exclusions={'focus','center'})
            new_concepts.update(mapped_ids.values())
            span_node = working_memory._get_next_id()
            working_memory.add(span_node, 'exprof', mapped_ids.get(focus,focus))
            working_memory.add(span_node, 'type', 'span')
            span_dict[span_obj] = span_node
            span_dict[span_node] = span_obj
        working_memory.pull_ontology(new_concepts)
        working_memory.update_spans(span_dict)
        return span_dict, working_memory
