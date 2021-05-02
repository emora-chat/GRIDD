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
        Each solution in the `solutions_list` is a `match_dict` which maps
        variables from the rule to matches in the concept_graph.
        `post` is the `string_spec_ls` which is a list of string elements that contain surface form realization parameters
        and form the full response when properly handled and concatenated.
        """
        compiler = ConceptCompiler(predicates=None, types=None, namespace='c_')
        predicates, metalinks, metadatas = compiler.compile(collect(join('GRIDD', 'resources', 'kg_files', 'nlg_templates')))
        template_cg = ConceptGraph(predicates, metalinks=metalinks, metadata=metadatas,
                                   namespace='t_')
        template_rules = template_cg.nlg_templates()
        inference_engine = InferenceEngine()
        cg = ConceptGraph(predicates='''
        time(hike(user=person()), past=datetime())
        expr("I", user)
        expr("hike", hike)
        expr("past", past)
        type("past", expression)
        ''', namespace="wm_")
        matches = inference_engine.infer(cg, template_rules)
        response = response_template_filler(matches, cg)[0]
        assert response.lower() == 'i hiked .'

        cg = ConceptGraph(predicates='''
        t/time(h/hike(user=person()), past=datetime())
        with(user, f/friend())
        possess(user, f)
        user_aware(h)
        user_aware(t)
        expr("I", user)
        expr("hike", hike)
        expr("past", past)
        type("past", expression)
        ''', namespace="wm_")
        matches = inference_engine.infer(cg, template_rules)
        response = response_template_filler(matches, cg)[0]
        assert response.lower() == 'i hiked with my friend .'

    def fill_string(response_template_filler, match_dict, expr_dict, string_spec_ls, wm):
        """
        Replace variables in string_spec_ls with expressions of matches found in match_dict and
        surface forms with grammatical realizations.

        Grammatical markers are:
            t - discrete tense category (past, present, future)
            s - subject dependency for agreement between subjects and verbs
            p - possessive indicator (true, false)

        An appropriate determiner and its agreement with its object is derived from logical form
        and as such is not specified in the template.
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
        string_spec_ls = ['X.var', ('be',{'t': 'present', 's': 'X'}), 'cute', '.']
        filled = response_template_filler.fill_string(match_dict, expr_dict, string_spec_ls, cg)
        assert filled == 'A cat is cute .'

        cg = ConceptGraph()
        ConceptGraph.construct(cg, f'time(cute(c=cat()), now) {USER_AWARE}(c)')
        ((s,t,o,i),) = cg.predicates('c', 'type', 'cat')
        cg.add(i, USER_AWARE)
        match_dict = {
            'X': 'c'
        }
        string_spec_ls = ['X.var', ('be',{'t': 'present', 's': 'X'}), 'cute', '.']
        filled = response_template_filler.fill_string(match_dict, expr_dict, string_spec_ls, cg)
        assert filled == 'The cat is cute .'

        cg = ConceptGraph()
        ConceptGraph.construct(cg, 'time(cute(c=cat()), now) type(c, group)')
        match_dict = {
            'X': 'c'
        }
        string_spec_ls = ['X.var', ('be',{'t': 'present', 's': 'X'}), 'cute', '.']
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
        string_spec_ls = ['X.var', ('be',{'t': 'Y', 's': 'X'}), 'cute', '.']
        filled = response_template_filler.fill_string(match_dict, expr_dict, string_spec_ls, cg)
        assert filled == 'The cats were cute .'