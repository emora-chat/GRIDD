from GRIDD.modules.responsegen_by_templates_spec import ResponseTemplatesSpec
from GRIDD.data_structures.concept_compiler import ConceptCompiler
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.utilities.utilities import collect
from GRIDD.globals import *
import time, re

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

class ResponseTemplateFinder:
    """
    Loads the template rules from template_dir upon initialization and returns them when called.
    """

    def __init__(self, template_dir):
        compiler = ConceptCompiler(predicates=None, types=None, namespace='c_')
        predicates, metalinks, metadatas = compiler.compile(collect(template_dir))
        template_cg = ConceptGraph(predicates, metalinks=metalinks, metadata=metadatas,
                                      namespace='t_')
        self.template_rules = template_cg.nlg_templates()

    def templates(self):
        return self.template_rules

class ResponseTemplateFiller:
    """
    Fills out a template based on the provided variable matches and concept expressions.
    """

    def __init__(self):
        self.lexicon = Lexicon.getDefaultLexicon()
        self.nlgFactory = NLGFactory(self.lexicon)
        self.realiser = Realiser(self.lexicon)

    def __call__(self, matches, cg, aux_state):
        expr_dict = {}
        for s, t, o, i in cg.predicates(predicate_type='expr'):
            if o not in expr_dict:
                if o == 'user':
                    expr_dict[o] = 'you'
                elif o == 'emora':
                    expr_dict[o] = 'I'
                else:
                    expr_dict[o] = s.replace('"', '')
        candidates = []
        for rule, (pre_graph, post, solutions_list) in matches.items():
            string_spec_ls = list(post) # need to create copy so as to not mutate the postcondition in the rule
            for match_dict in solutions_list:
                response_str = self.fill_string(match_dict, expr_dict, string_spec_ls, cg)
                if response_str not in aux_state.get('spoken_responses', []):
                    candidates.append((match_dict, response_str))
        predicates, string, avg_sal = self.select_best_candidate(candidates, cg)
        return (string, predicates, 'template')

    def select_best_candidate(self, candidates, cg):
        # get highest salience candidate with at least one uncovered predicate
        with_sal = []
        for match_dict, string in candidates:
            preds = [cg.predicate(x) for x in match_dict.values() if cg.has(predicate_id=x)
                     and cg.type(x) not in {EXPR, TYPE, TIME}]
            req_pred = [cg.predicate(x) for x in match_dict.values() if cg.has(predicate_id=x)
                        and cg.type(x) in {REQ_ARG, REQ_TRUTH}]
            user_awareness = [cg.has(x[3], USER_AWARE) for x in preds]
            user_req_awareness = [cg.has(x[3], USER_AWARE) for x in req_pred]
            # print()
            # for i, pred in enumerate(preds):
            #     print(pred, user_awareness[i])
            if False in user_awareness and (not user_req_awareness or True not in user_req_awareness):
                sals = [cg.features.get(x, {}).get(SALIENCE, 0) for x in match_dict.values()]
                avg = sum(sals) / len(sals)
                with_sal.append((preds, string, avg))
        if len(with_sal) > 0:
            return max(with_sal, key=lambda x: x[2])
        else:
            return None, None, None

    def fill_string(self, match_dict, expr_dict, string_spec_ls, cg):
        realizations = {}
        specifications = {}

        # Replacement of parameter-less variables
        for i, e in enumerate(string_spec_ls):
            is_tuple = False
            if isinstance(e, tuple):
                is_tuple = True
                e = e[0]
            if e not in realizations and '.var' in e:
                e = e[:-4]
                string_spec_ls[i] = e if not is_tuple else (e, string_spec_ls[i][1])
                match = match_dict[e]
                if match in expr_dict: # the matched concept for the variable is a named concept
                    realizations[e] = expr_dict[match_dict[e]]
                else: # not a named concept
                    np = self.nlgFactory.createNounPhrase()
                    # need to get main type
                    match_types = cg.types(match)
                    main_type = self._concrete_type(cg, match)
                    noun = self.nlgFactory.createNLGElement(main_type, LexicalCategory.NOUN)
                    if is_tuple and string_spec_ls[i][1].get("d", False) == True:
                        # determine whether reference or instance
                        if cg.metagraph.out_edges(match, REF) or list(cg.predicates(match, USER_AWARE)):
                            np.setDeterminer('the')
                        else:
                            np.setDeterminer('a')
                    # whether group
                    if GROUP in match_types:
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
                    tense = match_dict.get(spec['t'], spec['t'])
                    tense = expr_dict.get(tense, tense)
                    if tense == 'past':
                        clause.setFeature(Feature.TENSE, Tense.PAST)
                    elif tense in {'present', 'now'}:
                        clause.setFeature(Feature.TENSE, Tense.PRESENT)
                    elif tense == 'future':
                        clause.setFeature(Feature.TENSE, Tense.FUTURE)
                    else:
                        print('WARNING! You specified an nlg `tense` parameter that is not handled (%s).'%spec['t'])
                if 's' in spec:
                    subject = realizations.get(spec['s'], spec['s'])
                    clause.setSubject(subject)
                    if spec['s'] in specifications:
                        clause.setFeature(Feature.NUMBER, specifications[spec['s']].features['number'])
                    to_remove.add(subject)
                if 'p' in spec:
                    noun = match_dict.get(surface_form, surface_form)
                    noun = expr_dict.get(noun, noun)
                    np = self.nlgFactory.createNounPhrase(noun)
                    if spec['p'] == True:
                        np.setFeature(Feature.POSSESSIVE, True)
                        np.setFeature(Feature.PRONOMINAL, True)
                    clause = np
                sentence = self.realiser.realiseSentence(clause).lower()
                for r in to_remove:
                    pattern = r'\b' + r.lower() + r'\b'
                    sentence = re.sub(pattern, '', sentence)
                realizations[str(e)] = sentence[:-1].strip()

        final_str = [realizations.get(str(e), str(e)) for e in string_spec_ls]
        return ' '.join(final_str)

    def _concrete_type(self, cg, concept):
        """
        Identify which immediate type of a concept is the most concrete (e.g. is lowest in
        the ontology hierarchy)
        """
        immediate_types = cg.objects(concept, TYPE)
        candidates = set()
        for t in immediate_types:
            subs = set(cg.subtypes_of(t)) - {t}
            intersection = immediate_types.intersection(subs)
            if len(intersection) == 0:
                # there are no lower types in the immediate types that are subtypes of the current one
                candidates.add(t)
        return next(iter(candidates))



if __name__ == '__main__':
    print(ResponseTemplatesSpec.verify(ResponseTemplateFiller))

    # from os.path import join
    # from GRIDD.data_structures.inference_engine import InferenceEngine
    #
    # tfind = ResponseTemplateFinder(join('GRIDD', 'resources', 'kg_files', 'nlg_templates'))
    # infer = InferenceEngine()
    #
    # logic = '''
    # '''
    # cg = ConceptGraph(namespace='wm')
    # ConceptGraph.construct(cg, logic)

    # tfill = ResponseTemplateFiller()
    # tfill.test()


