from structpy import specification
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.concept_compiler import ConceptCompiler
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.utilities.utilities import collect
from GRIDD.globals import *
from os.path import join

@specification
class ResponseTemplatesSpec:

    @specification.init
    def ResponseTemplateFiller(ResponseTemplateFiller):
        response_template_filler = ResponseTemplateFiller()
        return response_template_filler

    def __call__(response_template_filler, matches, wm):
        """
         Fills the corresponding template for each match found

        `matches` is the output of the inference engine after running the template rules, which takes the form:
         dict< rule_name: (pre, post, solutions_list) >

         Each solution in the `solutions_list` is a `match_dict` which maps variables from the rule to matches in the
         concept_graph.

        `post` is the `string_spec_ls` which is a list of string elements that contain surface form realization parameters
         and form the full response when properly handled and concatenated.

         Grammatical markers used in the template sentence specifications:
            t - discrete tense category (string past, present, future)
                Used for verbs in order to set the appropriate tense
            s - subject dependency for agreement between subjects and verbs (string subject)
                Used to ensure the verb form agrees with the plurality and person (1st, 2nd, etc) of the subject
            p - possessive indicator (binary true, false) - defaults to false
                Used for nouns in order to transform the string into its possessive form if `p` is set to `true`.
            d - needs determiner indicator (binary true, false) - defaults to false
                An appropriate determiner and its agreement with its object can be derived from logical form, which is
                executed if `d` is set to `true`. Otherwise, the determiner is assumed to be provided explicitly in the
                template sentence.

            NOTE: If the value of a grammatical marker is a variable in the logical form, it must be preceded by a `#`.
        """

        aux_state = {}

        ###############################################################################################################
        # Example 1
        #  The tense of the `hike` verb is determined by the `datetime` object `Y` of the `hike` predicate. Since the
        #  `datetime` object is a variable, the value of the `t` marker is `#Y`.
        #  Similarly, the subject of the `hike` verb is a variable `person` `X`, so to produce a subject-verb sentence
        #  structure, we write `X hike`.
        #  In order to ensure agreement between the verb and its subject, we set the `s` marker to be `#X`.
        ###############################################################################################################

        compiler = ConceptCompiler(predicates=None, types=None, namespace='c_')
        predicates, metalinks, metadatas = compiler.compile('''
        time(hike(X/person()), Y/datetime())
        expr(Z/expression(), Y)
        -> person_hiked ->
        $ X hike{"t":"#Y", "s":"#X"} . $
        ;
        ''')
        template_cg = ConceptGraph(predicates, metalinks=metalinks, metadata=metadatas,
                                   namespace='t_')
        template_rules = template_cg.nlg_templates()
        inference_engine = InferenceEngine()

        # A test CG to match the template to
        cg = ConceptGraph(predicates='''
        time(hike(emora=person()), past=datetime())
        expr("I", emora)
        expr("hike", hike)
        expr("past", past)
        type("past", expression)
        ''', namespace="wm_")
        matches = inference_engine.infer(cg, template_rules)
        response = response_template_filler(matches, cg, aux_state)[0]
        assert response.lower() == 'i hiked .'

        ###############################################################################################################
        # Example 1
        #  This example is similar to the one above, with an extension that adds a clause to the subject-verb sentence
        #  for the `hike` predicate indicating who the subject performed the hike event with.
        #  In order to indicate this possessive nature between the subject and the friend in the clause, we set the
        #  `p` indicator to be `true`.
        ###############################################################################################################

        compiler = ConceptCompiler(predicates=None, types=None, namespace='c_')
        predicates, metalinks, metadatas = compiler.compile('''
        time(h/hike(X/person()), Y/datetime())
        expr(Z/expression(), Y)
        with(h, A/friend())
        possess(X, A)
        -> person_hiked_with_friend ->
        $ X hike{"t":"#Y", "s":"#X"} with X{"p": true} friend . $
        ;
        ''')
        template_cg = ConceptGraph(predicates, metalinks=metalinks, metadata=metadatas,
                                   namespace='t_')
        template_rules = template_cg.nlg_templates()

        # A test CG to match the template to
        cg = ConceptGraph(predicates='''
        t/time(h/hike(emora=person()), past=datetime())
        with(h, f/friend())
        possess(emora, f)
        user_aware(h)
        user_aware(t)
        expr("I", emora)
        expr("hike", hike)
        expr("past", past)
        type("past", expression)
        ''', namespace="wm_")
        matches = inference_engine.infer(cg, template_rules)
        response = response_template_filler(matches, cg, aux_state)[0]
        assert response.lower() == 'i hiked with my friend .'


    def fill_string(response_template_filler, match_dict, expr_dict, string_spec_ls, wm):
        """
        Replace variables in string_spec_ls with expressions of matches found in match_dict and
        surface forms with grammatical realizations.
        """
        cg = ConceptGraph()
        ConceptGraph.construct(cg, 'time(hike(emora), now)')
        match_dict = {
            'X': 'emora'
        }
        expr_dict = {
            'emora': 'I'
        }
        string_spec_ls = ['X.var', ('hike',{'t': 'present', 's': 'X'}), '.']
        filled = response_template_filler.fill_string(match_dict, expr_dict, string_spec_ls, cg)
        assert filled == 'I hike .'

        cg = ConceptGraph()
        ConceptGraph.construct(cg, 'time(hike(Mary), now)')
        match_dict = {
            'X': 'Mary',
            'Y': 'now'
        }
        expr_dict = {
            'Mary': 'Mary',
            'now': 'now'
        }
        string_spec_ls = ['X.var', ('hike',{'t': 'Y', 's': 'X'}), '.']
        filled = response_template_filler.fill_string(match_dict, expr_dict, string_spec_ls, cg)
        assert filled == 'Mary hikes .'

        cg = ConceptGraph()
        ConceptGraph.construct(cg, 'time(cute(c=cat()), now)')
        match_dict = {
            'X': 'c'
        }
        string_spec_ls = [('X.var',{'d': True}), ('be',{'t': 'present', 's': 'X'}), 'cute', '.']
        filled = response_template_filler.fill_string(match_dict, expr_dict, string_spec_ls, cg)
        assert filled == 'A cat is cute .'

        cg = ConceptGraph()
        ConceptGraph.construct(cg, f'time(cute(c=cat()), now) {USER_AWARE}(c)')
        ((s,t,o,i),) = cg.predicates('c', 'type', 'cat')
        cg.add(i, USER_AWARE)
        match_dict = {
            'X': 'c'
        }
        string_spec_ls = [('X.var',{'d': True}), ('be',{'t': 'present', 's': 'X'}), 'cute', '.']
        filled = response_template_filler.fill_string(match_dict, expr_dict, string_spec_ls, cg)
        assert filled == 'The cat is cute .'

        cg = ConceptGraph()
        ConceptGraph.construct(cg, 'time(cute(c=cat()), now) type(c, group)')
        match_dict = {
            'X': 'c'
        }
        string_spec_ls = ['X.var', ('be',{'t': 'present', 's': 'X'}), 'cute', '.']
        filled = response_template_filler.fill_string(match_dict, expr_dict, string_spec_ls, cg)
        assert filled == 'Cats are cute .'

        cg = ConceptGraph()
        ConceptGraph.construct(cg, 'time(cute(c=cat()), now) type(c, group)')
        match_dict = {
            'X': 'c'
        }
        string_spec_ls = [('X.var',{'d': True}), ('be',{'t': 'present', 's': 'X'}), 'cute', '.']
        filled = response_template_filler.fill_string(match_dict, expr_dict, string_spec_ls, cg)
        assert filled == 'Some cats are cute .'

        cg = ConceptGraph()
        ConceptGraph.construct(cg, f'time(cute(c=cat()), now) t=type(c, group) {USER_AWARE}(c) {USER_AWARE}(t)')
        ((s,t,o,i),) = cg.predicates('c', 'type', 'cat')
        cg.add(i, USER_AWARE)
        match_dict = {
            'X': 'c',
            'Y': 'past'
        }
        expr_dict = {
            'past': 'past'
        }
        string_spec_ls = [('X.var',{'d': True}), ('be',{'t': 'Y', 's': 'X'}), 'cute', '.']
        filled = response_template_filler.fill_string(match_dict, expr_dict, string_spec_ls, cg)
        assert filled == 'The cats were cute .'