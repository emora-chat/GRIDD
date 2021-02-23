import GRIDD.globals as globals

class MentionBridge:

    def __call__(self, *args, **kwargs):
        """
        Merge mention graphs into working_memory and connect its span to the focus of mention graph.
        args[0] - mentions
        args[1] - working memory
        """
        mentions, working_memory = args
        if globals.DEBUG:
            print()
            print('<< Mentions Identified >>')
            for span in mentions:
                print('%s(%d,%d)'%(span.string, span.start, span.end))
            print()
        new_concepts = set()
        for span, mention_graph in mentions.items():
            ((focus,t,o,i,),) = mention_graph.predicates(predicate_type='focus')
            ((center, t, o, i,),) = mention_graph.predicates(predicate_type='center')
            mapped_ids = working_memory.concatenate(mention_graph, predicate_exclusions={'focus','center','cover'})
            working_memory.features.update_from_mentions(mapped_ids.values(), working_memory)
            new_concepts.update(mapped_ids.values())
            mapped_focus = mapped_ids.get(focus)
            mapped_center = mapped_ids.get(center)
            working_memory.add(span, 'ref', mapped_focus)
            working_memory.add(span, 'def', mapped_center)
            working_memory.add(span, 'type', 'span')
        working_memory.pull_ontology(new_concepts)
        return working_memory
