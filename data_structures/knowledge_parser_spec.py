
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

    def to_concept_graph(knowledge_parser, logic_strings):
        """
        Get list of concept_graphs corresponding to the provided logic_strings.

        `logic_strings` is a variable number of logic strings.
        """
        ls1 = '''
            fluffy=cat()
            meow(fluffy)
            ;
            
            fido=dog()
            bark(fido)
            ;
        '''
        concept_graphs = knowledge_parser.to_concept_graph(ls1)
        assert len(concept_graphs) == 2
        assert concept_graphs[0].has('fluffy', 'type', 'cat')
        assert concept_graphs[0].has('fluffy', 'meow')
        assert concept_graphs[1].has('fido', 'type', 'dog')
        assert concept_graphs[1].has('fido', 'bark')

    def to_rules(knowledge_parser, logic_strings, with_names=False):
        """
        Get list of rule tuples from logic strings.

        `logic_strings` is a variable number of logic strings.

        if with_names is True
            :returns list[(precondition_cg, postcondition_cg, rule_name)]
        otherwise
            :returns list[(precondition_cg, postcondition_cg)]
        """

        ls1 = '''
            X=cat()
            =>
            meow(X)
            ;

            X=dog()
            =>
            bark(X)
            ;
        '''
        rules = knowledge_parser.to_rules(ls1)
        assert len(rules) == 2
        cat_pre, cat_post = rules[0]
        assert cat_pre.has('X', 'type', 'cat')
        assert cat_post.has('X', 'meow')
        dog_pre, dog_post = rules[1]
        assert dog_pre.has('X', 'type', 'dog')
        assert dog_post.has('X', 'bark')