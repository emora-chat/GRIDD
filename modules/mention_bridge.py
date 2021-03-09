from GRIDD.data_structures.concept_graph import ConceptGraph
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
                print('%s'%(span[span.index('>')+1:]))
            print()
        namespace = 'ment_' # todo - link to mentions graph namespace without relying on there being a mention?
        mega_mention_graph = ConceptGraph(namespace=namespace)
        for span, mention_graph in mentions.items():
            ((focus,t,o,i,),) = mention_graph.predicates(predicate_type='focus')
            ((center, t, o, i,),) = mention_graph.predicates(predicate_type='center')
            mega_mention_graph.concatenate(mention_graph, predicate_exclusions={'focus','center','cover'})
            mega_mention_graph.add(span, 'ref', focus)
            mega_mention_graph.add(span, 'def', center)
            mega_mention_graph.add(span, 'type', 'span')
        mapped_ids = working_memory.concatenate(mega_mention_graph)
        working_memory.features.update_from_mentions(mapped_ids.values(), working_memory)
        working_memory.pull_ontology(mapped_ids.values())
        return working_memory
