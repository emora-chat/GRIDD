from structpy import specification
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.knowledge_base import KnowledgeBase

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
        However, in this case, if any of the provided rules are not named, then an assertion error is thrown.

        `inference_rules` is a variable number of rules where the rule can be:
            logic string of SINGLE rule
            rule concept id in concept graph
            tuple of concept graphs (precondition, postcondition)

        The tuples can have an optional third element which provides a string name for the rule.

        If no inference rules are provided, then all rules present in the concept graph will be applied.

        Returns a dictionary <rule id: list of assignments>.

        """

        cg = ConceptGraph(predicates=[
            ('fido', 'type', 'dog'),
            ('princess', 'type', 'cat')
        ])

        # Logic string
        rule = '''
            x/dog() => bark(x);
        '''
        rule2 = '''
            x/cat() => meow(x);
        '''
        assignments = inference_engine.run(cg, rule, rule2)
        for rule, solutions in assignments.items():
            if rule[0].has('dog'):
                assert len(solutions) == 1
                assert 'fido' in solutions[0].values()
            elif rule[0].has('cat'):
                assert len(solutions) == 1
                assert 'princess' in solutions[0].values()

        # Tuples
        rules_str = '''
            x/dog() => bark(x);
            x/cat() => meow(x);
        '''
        rule_base = KnowledgeBase(rules_str, ensure_kb_compatible=False)._concept_graph
        rules = inference_engine.generate_rules_from_graph(rule_base)
        assignments = inference_engine.run(cg, *rules)
        for rule in rules:
            assert len(assignments[rule]) == 1
            if rule[0].has('dog'):
                dog_var = rule[0].predicates(predicate_type='type', object='dog')[0][0]
                assert assignments[rule][0][dog_var] == 'fido'
            elif rule[0].has('cat'):
                cat_var = rule[0].predicates(predicate_type='type', object='cat')[0][0]
                assert assignments[rule][0][cat_var] == 'princess'
            else:
                assert False

        # No inference rules
        rules_str = '''
            x/dog() -> dogs_bark -> bark(x);
            x/cat() -> cats_meow -> meow(x);
        '''
        cg = KnowledgeBase(rules_str, ensure_kb_compatible=False)._concept_graph
        cg.add('fido', 'type', 'dog')
        cg.add('princess', 'type', 'cat')
        assignments = inference_engine.run(cg)
        for rule, solutions in assignments.items():
            if rule[0].has('dog'):
                assert len(solutions) == 1
                assert 'fido' in solutions[0].values()
            elif rule[0].has('cat'):
                assert len(solutions) == 1
                assert 'princess' in solutions[0].values()

        # Order is specified
        assignments = inference_engine.run(cg, ordered_rule_ids=['cats_meow', 'dogs_bark'])
        assert len(assignments) == 2
        rules = list(assignments.keys())
        cat_rule = rules[0]
        dog_rule = rules[1]
        assert cat_rule[0].has('cat')
        assert len(assignments[cat_rule]) == 1
        assert 'princess' in assignments[cat_rule][0].values()
        assert dog_rule[0].has('dog')
        assert len(assignments[dog_rule]) == 1
        assert 'fido' in assignments[dog_rule][0].values()

        # Rule concept id
        assignments = inference_engine.run(cg, 'cats_meow')
        assert len(assignments) == 1
        rules = list(assignments.keys())
        cat_rule = rules[0]
        assert cat_rule[0].has('cat')
        assert len(assignments[cat_rule]) == 1
        assert 'princess' in assignments[cat_rule][0].values()

    def generate_rules_from_graph(inference_engine, concept_graph, with_names=False):
        """
        Extracts the inference rules and their corresponding implications from `concept graph` as
        tuples of concept_graphs.

        if with_names is True
            :returns list[(precondition_cg, postcondition_cg, rule_name)]
        otherwise
            :returns list[(precondition_cg, postcondition_cg)]
        """

        rule = '''
            x/dog() => bark(x);
        '''
        rule_base = KnowledgeBase(rule, ensure_kb_compatible=False)._concept_graph
        rules = inference_engine.generate_rules_from_graph(rule_base)
        assert len(rules) == 1
        assert len(rules[0]) == 2
        assert len(rules[0][0].predicates(predicate_type='type', object='dog')) == 1
        dog_var = rules[0][0].predicates(predicate_type='type', object='dog')[0][0]
        assert rules[0][1].has(dog_var, 'bark')

        dog_rule = '''
            x/dog() -> dogs_bark -> bark(x);
        '''
        cat_rule = '''
            x/cat() -> cats_meow -> meow(x);
        '''
        rule_base = KnowledgeBase(dog_rule, cat_rule, ensure_kb_compatible=False)._concept_graph
        rules = inference_engine.generate_rules_from_graph(rule_base, with_names=True)
        assert len(rules) == 2
        for rule in rules:
            assert len(rule) == 3
            if rule[2] == 'cats_meow':
                assert len(rule[0].predicates(predicate_type='type', object='cat')) == 1
                cat_var = rule[0].predicates(predicate_type='type', object='cat')[0][0]
                assert rule[1].has(cat_var, 'meow')
            elif rule[2] == 'dogs_bark':
                assert len(rule[0].predicates(predicate_type='type', object='dog')) == 1
                dog_var = rule[0].predicates(predicate_type='type', object='dog')[0][0]
                assert rule[1].has(dog_var, 'bark')
            else:
                assert False