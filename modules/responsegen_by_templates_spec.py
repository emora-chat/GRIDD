from structpy import specification
from GRIDD.data_structures.concept_graph import ConceptGraph


@specification
class ResponseTemplatesSpec:

    @specification.init
    def ResponseTemplateFiller(ResponseTemplateFiller):
        response_templates = ResponseTemplateFiller()
        return response_templates

    def fill_string(response_templates, match_dict, expr_dict, string_spec_ls):
        """
        Replace variables in string_spec_ls with expressions of matches found in match_dict and
        surface forms with grammatical realizations.

        Grammatical markers are:
            t - discrete tense category (past, present)
            p - binary plurality        (True, False)
            f - discrete form category  (gerund, infinitive)
            s - subject dependency for agreement between subjects and verbs
            o - object dependency for agreement between determiners and objects
        """
        match_dict = {
            'X': 'emora'
        }
        expr_dict = {
            'emora': 'i'
        }
        string_spec_ls = ['X', ('hike',{'t': 'present', 's': 'X'}), '.']
        filled = response_templates.fill_string(match_dict, expr_dict, string_spec_ls)
        assert filled == 'I hike.'

        match_dict = {
            'X': 'Mary'
        }
        expr_dict = {
            'Mary': 'Mary'
        }
        string_spec_ls = ['X', ('hike',{'t': 'present', 's': 'X'}), '.']
        filled = response_templates.fill_string(match_dict, expr_dict, string_spec_ls)
        assert filled == 'Mary hikes.'