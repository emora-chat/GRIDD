from GRIDD.modules.responsegen_by_templates_spec import ResponseTemplatesSpec
# from GRIDD.data_structures.concept_compiler import TemplateConceptCompiler
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.utilities.utilities import collect
from GRIDD.globals import *
import time

from simplenlg.framework.NLGFactory         import *
from simplenlg.realiser.english.Realiser    import *
from simplenlg.lexicon.Lexicon              import *
from simplenlg.phrasespec.VPPhraseSpec      import *

from simplenlg.features.NumberAgreement     import *
from simplenlg.features.Feature             import *
from simplenlg.features.Tense               import *
from simplenlg.features.Person              import *

"""
These two classes work in conjunction with the service-implementation of the InferenceEngine
in order to find appropriate template matches for a given concept graph and properly fill in the 
templates for each match.

Execution Sequence:
    ResponseTemplateFinder
    InferenceEngine
    ResponseTemplateFiller
"""

# class ResponseTemplateFinder:
#     """
#     Loads the template rules from template_dir upon initialization and returns them when called.
#     """
#
#     def __init__(self, template_dir):
#         compiler = TemplateConceptCompiler(predicates=None, types=None, namespace='c_')
#         predicates, metalinks, metadatas = compiler.compile(collect(template_dir))
#         template_cg = ConceptGraph(predicates, metalinks=metalinks, metadata=metadatas,
#                                       namespace='t_')
#         self.template_rules = template_cg.rules()
#
#     def __call__(self):
#         return self.template_rules

class ResponseTemplateFiller:
    """
    Fills out a template based on the provided variable matches and concept expressions.
    """

    def __init__(self):
        self.lexicon = Lexicon.getDefaultLexicon()
        self.nlgFactory = NLGFactory(self.lexicon)
        self.realiser = Realiser(self.lexicon)

    def __call__(self, matches, cg):
        expr_dict = {}
        for s, t, o, i in cg.predicates(predicate_type='expr'):
            if o not in expr_dict:
                expr_dict[o] = s.replace('"', '')
        candidates = []
        for match_dict, string_spec_ls in matches:
            candidates.append((match_dict, self.fill_string(match_dict, expr_dict, string_spec_ls, cg)))
        return candidates

    def fill_string(self, match_dict, expr_dict, string_spec_ls, cg):
        realizations = {}
        specifications = {}

        # Replacement of parameter-less variables
        for e in string_spec_ls:
            if not isinstance(e, tuple) and e not in realizations and e.isupper():
                match = match_dict[e]
                if match in expr_dict: # the matched concept for the variable is a named concept
                    realizations[e] = expr_dict[match_dict[e]]
                else: # not a named concept
                    np = self.nlgFactory.createNounPhrase()
                    # need to get main type
                    types = cg.types(match)
                    noun = self.nlgFactory.createNLGElement(list(types - {match, GROUP})[0], LexicalCategory.NOUN)
                    # determine whether reference or instance
                    if cg.metagraph.out_edges(match, REF) or list(cg.predicates(match, USER_AWARE)):
                        np.setDeterminer('the')
                    else:
                        np.setDeterminer('a')
                    # whether group
                    if GROUP in types:
                        noun.setFeature(Feature.NUMBER, NumberAgreement.PLURAL)
                    else:
                        noun.setFeature(Feature.NUMBER, NumberAgreement.SINGULAR)
                    np.setNoun(noun)
                    realizations[e] = self.realiser.realiseSentence(np)[:-1]
                    specifications[e] = np

        # Replacement of parameterized variables
        for e in string_spec_ls:
            if isinstance(e, tuple) and str(e) not in realizations:
                surface_form, spec = e
                clause = self.nlgFactory.createClause()
                to_remove = set()
                if 't' in spec:
                    clause.setVerb(surface_form)
                    if spec['t'] == 'past':
                        clause.setFeature(Feature.TENSE, Tense.PAST)
                    elif spec['t'] == 'present':
                        clause.setFeature(Feature.TENSE, Tense.PRESENT)
                    elif spec['t'] == 'future':
                        clause.setFeature(Feature.TENSE, Tense.FUTURE)
                    else:
                        print('WARNING! You specified an nlg `tense` parameter that is not handled (%s).'%spec['t'])
                if 's' in spec:
                    subject = realizations.get(spec['s'], spec['s'])
                    clause.setSubject(subject)
                    if spec['s'] in specifications:
                        clause.setFeature(Feature.NUMBER, specifications[spec['s']].features['number'])
                    to_remove.add(subject)
                    # todo - determine if we need to use simplenlg to determine plurality/person?
                sentence = self.realiser.realiseSentence(clause)
                for r in to_remove:
                    sentence = sentence.replace(r, '')
                realizations[str(e)] = sentence[:-1].strip()

        final_str = [realizations.get(str(e), str(e)) for e in string_spec_ls]
        return ' '.join(final_str)

    def test(self):

        # Plurality & Determiner Object Agreement

        s = time.time()
        np = self.nlgFactory.createNounPhrase()
        np.setDeterminer('the')
        noun = self.nlgFactory.createNLGElement('cat', LexicalCategory.NOUN)
        noun.setFeature(Feature.NUMBER, NumberAgreement.SINGULAR)
        np.setNoun(noun)
        print('[%.2f] %s'%(time.time() - s, self.realiser.realiseSentence(np)))

        s = time.time()
        np = self.nlgFactory.createNounPhrase()
        np.setDeterminer('the')
        noun = self.nlgFactory.createNLGElement('cat', LexicalCategory.NOUN)
        noun.setFeature(Feature.NUMBER, NumberAgreement.PLURAL)
        np.setNoun(noun)
        print('[%.2f] %s'%(time.time() - s, self.realiser.realiseSentence(np)))

        s = time.time()
        np = self.nlgFactory.createNounPhrase()
        np.setDeterminer('a')
        noun = self.nlgFactory.createNLGElement('cat', LexicalCategory.NOUN)
        noun.setFeature(Feature.NUMBER, NumberAgreement.SINGULAR)
        np.setNoun(noun)
        print('[%.2f] %s'%(time.time() - s, self.realiser.realiseSentence(np)))

        s = time.time()
        np = self.nlgFactory.createNounPhrase()
        np.setDeterminer('a')
        noun = self.nlgFactory.createNLGElement('cat', LexicalCategory.NOUN)
        noun.setFeature(Feature.NUMBER, NumberAgreement.PLURAL)
        np.setNoun(noun)
        print('[%.2f] %s'%(time.time() - s, self.realiser.realiseSentence(np)))

        # Verb Tense and Subject Person Agreement

        s = time.time()
        clause = self.nlgFactory.createClause()
        clause.setSubject('Mark')
        clause.setVerb('sing')
        clause.setFeature(Feature.TENSE, Tense.PRESENT)
        print('[%.2f] %s' % (time.time() - s, self.realiser.realiseSentence(clause)))

        s = time.time()
        clause = self.nlgFactory.createClause()
        clause.setSubject('Mark')
        clause.setVerb('sing')
        clause.setFeature(Feature.TENSE, Tense.PAST)
        print('[%.2f] %s' % (time.time() - s, self.realiser.realiseSentence(clause)))

        s = time.time()
        clause = self.nlgFactory.createClause()
        clause.setSubject('Mark')
        clause.setVerb('sing')
        clause.setFeature(Feature.TENSE, Tense.FUTURE)
        print('[%.2f] %s' % (time.time() - s, self.realiser.realiseSentence(clause)))

        s = time.time()
        clause = self.nlgFactory.createClause()
        clause.setSubject('I')
        clause.setVerb('sing')
        clause.setFeature(Feature.TENSE, Tense.PRESENT)
        print('[%.2f] %s' % (time.time() - s, self.realiser.realiseSentence(clause)))

        s = time.time()
        clause = self.nlgFactory.createClause()
        clause.setSubject('I')
        clause.setVerb('sing')
        clause.setFeature(Feature.TENSE, Tense.PAST)
        print('[%.2f] %s' % (time.time() - s, self.realiser.realiseSentence(clause)))

        s = time.time()
        clause = self.nlgFactory.createClause()
        clause.setSubject('I')
        clause.setVerb('sing')
        clause.setFeature(Feature.TENSE, Tense.FUTURE)
        print('[%.2f] %s' % (time.time() - s, self.realiser.realiseSentence(clause)))









if __name__ == '__main__':
    print(ResponseTemplatesSpec.verify(ResponseTemplateFiller))

    # from os.path import join
    # from GRIDD.data_structures.inference_engine import InferenceEngine
    #
    # tfind = ResponseTemplateFinder(join('GRIDD', 'resources', 'nlg_templates'))
    # infer = InferenceEngine()
    #
    # logic = '''
    # '''
    # cg = ConceptGraph(namespace='wm')
    # ConceptGraph.construct(cg, logic)

    # tfill = ResponseTemplateFiller()
    # tfill.test()


