from structpy import specification
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.globals import *

@specification
class ResponseTemplatesSpec:

    @specification.init
    def ResponseTemplateFiller(ResponseTemplateFiller):
        response_template_filler = ResponseTemplateFiller()
        return response_template_filler

    def __call__(self, matches, wm):
        """
        Fills the corresponding template for each match found

        `matches` - is a list of (match_dict, string_spec_ls) where match_dict maps
        variables from the rule to matches in the concept_graph and string_spec_ls
        is a list of string elements that contain surface form realization parameters
        and form the full response when properly handled and concatenated.
        """
        pass

    def fill_string(response_template_filler, match_dict, expr_dict, string_spec_ls, wm):
        """
        Replace variables in string_spec_ls with expressions of matches found in match_dict and
        surface forms with grammatical realizations.

        Grammatical markers are:
            t - discrete tense category (past, present, future)
            s - subject dependency for agreement between subjects and verbs

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
        string_spec_ls = ['X', ('hike',{'t': 'present', 's': 'X'}), '.']
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
        string_spec_ls = ['X', ('hike',{'t': 'Y', 's': 'X'}), '.']
        filled = response_template_filler.fill_string(match_dict, expr_dict, string_spec_ls, cg)
        assert filled == 'Mary hikes .'

        cg = ConceptGraph()
        ConceptGraph.construct(cg, 'time(cute(c=cat()), now)')
        match_dict = {
            'X': 'c'
        }
        string_spec_ls = ['X', ('be',{'t': 'present', 's': 'X'}), 'cute', '.']
        filled = response_template_filler.fill_string(match_dict, expr_dict, string_spec_ls, cg)
        assert filled == 'A cat is cute .'

        cg = ConceptGraph()
        ConceptGraph.construct(cg, f'time(cute(c=cat()), now) {USER_AWARE}(c)')
        ((s,t,o,i),) = cg.predicates('c', 'type', 'cat')
        cg.add(i, USER_AWARE)
        match_dict = {
            'X': 'c'
        }
        string_spec_ls = ['X', ('be',{'t': 'present', 's': 'X'}), 'cute', '.']
        filled = response_template_filler.fill_string(match_dict, expr_dict, string_spec_ls, cg)
        assert filled == 'The cat is cute .'

        cg = ConceptGraph()
        ConceptGraph.construct(cg, 'time(cute(c=cat()), now) type(c, group)')
        match_dict = {
            'X': 'c'
        }
        string_spec_ls = ['X', ('be',{'t': 'present', 's': 'X'}), 'cute', '.']
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
        string_spec_ls = ['X', ('be',{'t': 'Y', 's': 'X'}), 'cute', '.']
        filled = response_template_filler.fill_string(match_dict, expr_dict, string_spec_ls, cg)
        assert filled == 'The cats were cute .'