from structpy import specification
from data_structures.concept_graph import ConceptGraph
from data_structures.knowledge_base import KnowledgeBase

@specification
class InferenceEngineSpec:

    @specification.init
    def INFERENCE_ENGINE(InferenceEngine):
        inference_engine = InferenceEngine()
        return inference_engine


    def run(inference_engine, concept_graph, inference_rules, ordered_rule_ids=None):
        """
        Applies each rule from inference_rules to the concept_graph and identifies all valid assignments.
        If ordered_rule_ids is specified, the rules are applied in the order indicated by ordered_rule_ids.

        `inference_rules` is a variable number of rules where the rule can be:
            rule logicstring
            rule concept id in concept graph
            tuple of concept graphs (precondition, postcondition)

        The tuples can have an optional third element which provides a string name for the rule.

        If no inference rules are provided, then all rules present in the concept graph will be applied.

        Returns a dictionary <rule identifier: list of assignments>.
        """

        cg = ConceptGraph(predicates=[
            ('fido', 'type', 'dog'),
            ('princess', 'type', 'cat')
        ])

        # Logic string
        rule = '''
            x/dog() => bark(x)
        '''
        rule2 = '''
            x/cat() => meow(x)
        '''
        assignments = inference_engine.run(cg, rule, rule2)
        assert len(assignments[rule]) == 1
        assert 'fido' in assignments[rule][0].values()
        assert 'princess' not in assignments[rule][0].values()

        # Tuples
        rules_str = '''
            x/dog() => bark(x)
            x/cat() => meow(x)
        '''
        rule_base = KnowledgeBase(rules_str)
        rules = inference_engine.generate_rules_from_graph(rule_base)
        assignments = inference_engine.run(cg, *rules)
        assert len(assignments[(rules[0][0],rules[0][1])]) == 1
        dog_var = rules[0][0].predicates(predicate_type='type', object='dog')[0][0]
        assert assignments[(rules[0][0],rules[0][1])][0][dog_var] == 'fido'
        assert len(assignments[(rules[1][0],rules[1][1])]) == 1
        cat_var = rules[1][0].predicates(predicate_type='type', object='cat')[0][0]
        assert assignments[(rules[1][0],rules[1][1])][0][cat_var] == 'princess'

        # No inference rules
        rules_str = '''
            x/dog() -> dogs_bark -> bark(x)
            x/cat() -> cats_meow -> meow(x)
        '''
        cg = KnowledgeBase(rules_str)._concept_graph
        cg.add('fido', 'type', 'dog')
        cg.add('princess', 'type', 'cat')
        assignments = inference_engine.run(cg)
        assert len(assignments) == 2
        assert assignments.keys() == ['dogs_bark', 'cats_meow']
        assert len(assignments['dogs_bark']) == 1
        dog_instances = [x[0] for x in cg.predicates(predicate_type='type', object='dog')]
        pre_predicates = cg.predicates('dogs_bark', 'pre')
        dog_pre_var = set(pre_predicates).intersection(set(dog_instances))
        assert assignments['dogs_bark'][0][dog_pre_var] == 'fido'
        assert len(assignments['cats_meow']) == 1
        cat_instances = [x[0] for x in cg.predicates(predicate_type='type', object='cat')]
        pre_predicates = cg.predicates('cats_meow', 'pre')
        cat_pre_var = set(pre_predicates).intersection(set(cat_instances))
        assert assignments['cats_meow'][0][cat_pre_var] == 'princess'

        # Order is specified
        assignments = inference_engine.run(cg, ordered_rule_ids=['cats_meow', 'dogs_bark'])
        assert len(assignments) == 2
        assert assignments.keys() == ['cats_meow', 'dogs_bark']
        assert len(assignments['dogs_bark']) == 1
        dog_instances = [x[0] for x in cg.predicates(predicate_type='type', object='dog')]
        pre_predicates = cg.predicates('dogs_bark', 'pre')
        dog_pre_var = set(pre_predicates).intersection(set(dog_instances))
        assert assignments['dogs_bark'][0][dog_pre_var] == 'fido'
        assert len(assignments['cats_meow']) == 1
        cat_instances = [x[0] for x in cg.predicates(predicate_type='type', object='cat')]
        pre_predicates = cg.predicates('cats_meow', 'pre')
        cat_pre_var = set(pre_predicates).intersection(set(cat_instances))
        assert assignments['cats_meow'][0][cat_pre_var] == 'princess'

        # Rule concept id
        assignments = inference_engine.run(cg, 'cats_meow')
        assert len(assignments) == 1
        assert len(assignments['cats_meow']) == 1
        cat_instances = [x[0] for x in cg.predicates(predicate_type='type', object='cat')]
        pre_predicates = cg.predicates('cats_meow', 'pre')
        cat_pre_var = set(pre_predicates).intersection(set(cat_instances))
        assert assignments['cats_meow'][0][cat_pre_var] == 'princess'

    def generate_rules_from_graph(inference_engine, concept_graph, with_names=False, ordered_rule_ids=None):
        """
        Extracts the inference rules and their corresponding implications from `concept graph` as
        tuples of concept_graphs.

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