
from structpy import specification


@specification
class KnowledgeParserSpec:
    """
    Algorithm for parsing logic strings into list of concept graphs
    """

    @specification.init
    def KNOWLEDGE_PARSER(KnowledgeParser, kg=None, base_nodes=None, ensure_kb_compatible=False):
        """
        Create a `KnowledgeParser` object.

        If not ensure_kb_compatible,

            (1) no concept compatibility checks are performed

            (2) `kg` and `base_nodes` should not be provided.

            USE CASES: Concept Graphs, Rule Graphs

        If ensure_kb_compatible,

            (1) compatibility checks will throw Errors if the logic strings concepts
            are not properly defined either by being defined in the logic string or in the
            provided KnowledgeBase `kb`.

            (2) `kg` and `base_nodes` must also be provided.

            USE CASES: Knowledge Bases

        """
        knowledge_parser = KnowledgeParser()
        return knowledge_parser

    @specification.init
    def from_data(KnowledgeParser, data):
        """
        Get a single concept graph that contains all data provided.

        `data` is a variable number of directories, files, or logic strings.

        `data` can also be a single ConceptGraph, in which case it is just returned.
        """
        ls1 = '''
            fluffy=cat()
            meow(fluffy)
            ;
            
            /* comment */
            
            fido=dog()
            bark(fido)
            ;
            
            /* comment */
        '''
        concept_graph = KnowledgeParser.from_data(ls1, namespace='cg_')
        assert concept_graph.has('fluffy', 'type', 'cat')
        assert concept_graph.has('fluffy', 'meow')
        assert concept_graph.has('fido', 'type', 'dog')
        assert concept_graph.has('fido', 'bark')

    @specification.init
    def rules(KnowledgeParser, data):
        """
        Get dictionary of rule_id: (precondition_graph, postcondition_graph) from data.

        `data` is a variable number of concept graphs, directories, files, or logic strings
        """

        ls1 = '''
            X=cat()
            -> cat_rule ->
            meow(X)
            ;
            
            /* my comment */

            /* my comment */

            X=dog()
            -> dog_rule ->
            bark(X)
            ;
        '''
        rules = KnowledgeParser.rules(ls1)
        assert len(rules) == 2
        cat_pre, cat_post = rules['cat_rule']
        assert cat_pre.has('X', 'type', 'cat')
        assert cat_post.has('X', 'meow')
        dog_pre, dog_post = rules['dog_rule']
        assert dog_pre.has('X', 'type', 'dog')
        assert dog_post.has('X', 'bark')