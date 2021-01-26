from structpy import specification
from data_structures.concept_graph import ConceptGraph
from data_structures.knowledge_base import KnowledgeBase

@specification
class InferenceEngineSpec:

    @specification.init
    def INFERENCE_ENGINE(InferenceEngine):
        inference_engine = InferenceEngine()
        return inference_engine


    def generate_rules_from_graph(inference_engine, concept_graph, with_names=False, ordered_rule_ids=None):
        """
        Extracts the inference rules and their corresponding implications from `concept graph` as individual concept_graphs.

        If the list of ordered_rule_ids is given, then the pairs are returned in the specified order.

        if with_names is True
            :returns list[(precondition_cg, postcondition_cg, rule_name)]
        otherwise
            :returns list[(precondition_cg, postcondition_cg)]
        """
        rule = '''
            x/dog() => bark(x)
        '''
        rule_base = KnowledgeBase(rule)
        rules = inference_engine.generate_rules_from_graph(rule_base)
        assert len(rules) == 1
        assert len(rules[0]) == 2
        assert rules[0][0].has(predicate_type='type', object='dog')
        dog_var = rules[0][0].predicates(predicate_type='type', object='dog')[0][0]
        assert rules[0][1].has(dog_var, 'bark')

        dog_rule = '''
            x/dog() -> dogs_bark -> bark(x)
        '''
        cat_rule = '''
            x/cat() -> cats_meow -> meow(x)
        '''
        rule_base = KnowledgeBase(dog_rule, cat_rule)
        rules = inference_engine.generate_rules_from_graph(rule_base,
                                                           with_names=True,
                                                           ordered_rule_ids=['cats_meow', 'dogs_bark'])
        assert len(rules) == 2
        assert len(rules[0]) == 3
        assert rules[0][2] == 'cats_meow'
        assert rules[0][0].has(predicate_type='type', object='cat')
        cat_var = rules[0][0].predicates(predicate_type='type', object='cat')[0][0]
        assert rules[1][1].has(cat_var, 'meow')
        assert rules[1][2] == 'dogs_bark'
        assert rules[1][0].has(predicate_type='type', object='dog')
        dog_var = rules[1][0].predicates(predicate_type='type', object='dog')[0][0]
        assert rules[1][1].has(dog_var, 'bark')


    def run(inference_engine, concept_graph, inference_rules):
        """
        Applies each rule from inference_rules to the concept_graph and identifies all valid assignments.

        `inference_rules` is a list of tuples (precondition, postcondition) where precondition and postcondition
        can be logicstrings or concept_graphs.

        The tuples can have an optional third element which provides a string name for the rule.

        Returns a dictionary <tuple: list of assignments>.
        """
        precondition = '''
            x/dog()
        '''
        postcondition = '''
            bark(x)
        '''
        # the vars are not linked if logic strings are specified???
        cg = ConceptGraph(predicates=[
            ('fido', 'type', 'dog')
        ])
        rules = [(precondition, postcondition)]
        assignments = inference_engine.run(cg, rules)
        assert len(assignments[(precondition, postcondition)]) == 1
        # how to check that the proper variable has been filled by fido???

        rule = '''
            x/dog() => bark(x)
        '''
        rule_base = KnowledgeBase(rule)
        rules = inference_engine.generate_rules_from_graph(rule_base)
        assignments = inference_engine.run(cg, rules)
        assert len(assignments[(rules[0][0],rules[0][1])]) == 1
        dog_var = rules[0][0].predicates(predicate_type='type', object='dog')[0][0]
        assert assignments[(rules[0][0],rules[0][1])][dog_var] == 'fido'
