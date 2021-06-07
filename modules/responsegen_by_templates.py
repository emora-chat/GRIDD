from GRIDD.globals import *

from simplenlg.framework.NLGFactory         import *
from simplenlg.realiser.english.Realiser    import *
from simplenlg.lexicon.Lexicon              import *
from simplenlg.phrasespec.VPPhraseSpec      import *

from simplenlg.features.NumberAgreement     import *
from simplenlg.features.Feature             import *
from simplenlg.features.Tense               import *
from simplenlg.features.Person              import *

"""
This class works in conjunction with the service-implementation of the InferenceEngine
in order to find appropriate template matches for a given concept graph and properly fill in the 
templates for each match.

Execution Sequence:
    ResponseTemplateFinder
    InferenceEngine
    ResponseTemplateFiller
"""

class ResponseTemplateFiller:
    """
    Fills out a template based on the provided variable matches and concept expressions.
    """

    def __init__(self):
        self.lexicon = Lexicon.getDefaultLexicon()
        self.nlgFactory = NLGFactory(self.lexicon)
        self.realiser = Realiser(self.lexicon)

    def __call__(self, matches, expr_dict, cg, aux_state):
        candidates = []
        for rule, (pre_graph, post, solutions_list) in matches.items():
            for match_dict in solutions_list:
                string_spec_ls = list(post.string_spec_ls)  # need to create copy so as to not mutate the postcondition in the rule
                try:
                    response_str = self.fill_string(match_dict, expr_dict, string_spec_ls, cg)
                except Exception as e:
                    print('Error in NLG template filler => %s'%e)
                    continue
                # print(string_spec_ls)
                if response_str not in aux_state.get('spoken_responses', []):
                    candidates.append((match_dict, response_str, post.priority))
        predicates, string, avg_sal = self.select_best_candidate(candidates, cg)
        return (string, predicates, 'template')

    def select_best_candidate(self, candidates, cg):
        # get highest salience candidate with at least one uncovered predicate
        with_sal = []
        print('\nResponse Options: ')
        for match_dict, string, priority in candidates:
            preds = [cg.predicate(x) for x in match_dict.values() if cg.has(predicate_id=x)
                     and cg.type(x) not in {EXPR, TYPE, TIME}]
            req_pred = [cg.predicate(x) for x in match_dict.values() if cg.has(predicate_id=x)
                        and cg.type(x) in {REQ_ARG, REQ_TRUTH} and cg.subject(x) == 'emora'] # check if emora already asked question
            user_awareness = [cg.has(x[3], USER_AWARE) for x in preds]
            user_req_awareness = [cg.has(x[3], USER_AWARE) for x in req_pred]
            if False in user_awareness and (not user_req_awareness or True not in user_req_awareness):
                # at least one predicate is not known by the user
                # and all request predicates are not known by user, if there are requests in response
                # todo - stress test emora not asking a question she already has answer to or has asked before
                # this should work, but we do have req_unsat predicate as backup, if needed
                sals = [cg.features.get(x, {}).get(SALIENCE, 0) for x in match_dict.values()]
                avg = sum(sals) / len(sals)
                final_score = SAL_WEIGHT * avg + PRIORITY_WEIGHT * priority
                with_sal.append((preds, string, final_score))
                print('\t%s (s: %.2f, pr: %.2f)' % (string, avg, priority))
        print()
        if len(with_sal) > 0:
            return max(with_sal, key=lambda x: x[2])
        else:
            return None, None, None


    def fill_string(self, match_dict, expr_dict, string_spec_ls, cg):
        # initialize realizations for variables used in string_spec_ls dependencies
        specifications = {}
        realizations = {}
        for e in string_spec_ls:
            if isinstance(e, (list,tuple)):
                for k,v in e[1].items():
                    if v in match_dict:
                        np, np_realized = self._process_variable_match(match_dict[v], cg, expr_dict)
                        if np is not None:
                            specifications[v] = np
                        realizations[v] = np_realized
        with_params = [(i,e) for i,e in enumerate(string_spec_ls) if isinstance(e, (list,tuple))]
        without_params = [(i,e) for i,e in enumerate(string_spec_ls) if not isinstance(e, (list,tuple))]

        # Replacement of constants and parameter-less variables
        for i, e in without_params:
            if '.var' in e:
                e = e[:-4]
                string_spec_ls[i] = e
                if e not in realizations:
                    match = match_dict[e]
                    np, np_realized = self._process_variable_match(match, cg, expr_dict)
                    if np is not None:
                        specifications[e] = np
                    realizations[e] = np_realized
            else:
                if e not in realizations:
                    realizations[e] = e

        with_params_dependent = []
        with_params_independent = []
        for i, e in with_params:
            for val in e[1].values():
                if val in match_dict:
                    with_params_dependent.append((i,e))
                    break
            else:
                with_params_independent.append((i,e))

        # Replacement of independent variables
        for i, e in with_params_independent:
            surface_form, spec = e
            e_id = str(e)
            if e_id not in realizations:
                if '.var' in surface_form:
                    surface_form = surface_form[:-4]
                    surface_form = match_dict[surface_form]
                if "p" in spec or "d" in spec: # noun
                    np = self.nlgFactory.createNounPhrase()
                    if surface_form in expr_dict:  # the matched concept for the variable is a named concept
                        noun = self.nlgFactory.createNLGElement(expr_dict[surface_form], LexicalCategory.NOUN)
                    else:  # not a named concept
                        noun = self._unnamed_noun(cg, surface_form)
                    np.setNoun(noun)
                    if spec.get("d", False) == True: # set determiner
                        if cg.metagraph.out_edges(surface_form, REF) or list(cg.predicates(surface_form, USER_AWARE)): # reference
                            np.setDeterminer('the')
                        else: # instance
                            np.setDeterminer('a')
                    if spec.get("p", False) == True: # set as possessive
                        np.setFeature(Feature.POSSESSIVE, True)
                        np.setFeature(Feature.PRONOMINAL, True) # todo - is this supposed to be here?
                    realizations[e_id] = self.realiser.realiseSentence(np)[:-1]
                    specifications[e_id] = np
                else: # verb
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
                            print(
                                'WARNING! You specified an nlg `tense` parameter that is not handled (%s).' % spec['t'])
                    if 's' in spec:
                        subject = realizations.get(spec['s'], spec['s'])
                        clause.setSubject(subject)
                        if spec['s'] in specifications:
                            clause.setFeature(Feature.NUMBER, specifications[spec['s']].features['number'])
                        to_remove.add(subject)
                    sentence = self.realiser.realiseSentence(clause).lower()
                    for r in to_remove:
                        pattern = r'\b' + r.lower() + r'\b'
                        sentence = re.sub(pattern, '', sentence)
                    realizations[e_id] = sentence[:-1].strip()

        # Replacement of dependent variables (only verbs can be dependent and `p` and `d` markers are not relevant for verbs)
        for i, e in with_params_dependent:
            surface_form, spec = e
            e_id = str(e)
            if e_id not in realizations:
                if '.var' in surface_form:
                    surface_form = surface_form[:-4]
                    surface_form = match_dict[surface_form]
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
                sentence = self.realiser.realiseSentence(clause).lower()
                for r in to_remove:
                    pattern = r'\b' + r.lower() + r'\b'
                    sentence = re.sub(pattern, '', sentence)
                realizations[e_id] = sentence[:-1].strip()

        final_str = [realizations[str(e)] for e in string_spec_ls]
        return ' '.join(final_str)

    def _concrete_type(self, cg, concept):
        """
        Identify which immediate type of a concept is the most concrete (e.g. is lowest in
        the ontology hierarchy)
        """
        namespace = cg.id_map().namespace
        immediate_types = cg.objects(concept, TYPE)
        candidates = set()
        for t in immediate_types:
            expressable_subs = {x for x in cg.subtypes_of(t) if x != t and not x.startswith(namespace)}
            intersection = immediate_types.intersection(expressable_subs)
            if len(intersection) == 0 and t not in {GROUP} and not t.startswith(namespace):
                # there are no subtypes in the immediate types and it is not an unexpressable type
                candidates.add(t)
        return next(iter(candidates))

    def _process_variable_match(self, match, cg, expr_dict):
        if match in expr_dict:  # the matched concept for the variable is a named concept
            return None, expr_dict[match]
        else:  # not a named concept
            np = self.nlgFactory.createNounPhrase()
            noun = self._unnamed_noun(cg, match, expr_dict)
            np.setNoun(noun)
            return np, self.realiser.realiseSentence(np)[:-1]


    def _unnamed_noun(self, cg, match, expr_dict):
        # need to get main type
        match_types = cg.types(match)
        main_type = self._concrete_type(cg, match)
        main_type = expr_dict.get(main_type, main_type)
        noun = self.nlgFactory.createNLGElement(main_type, LexicalCategory.NOUN)
        # whether group
        if GROUP in match_types:
            noun.setFeature(Feature.NUMBER, NumberAgreement.PLURAL)
        else:
            noun.setFeature(Feature.NUMBER, NumberAgreement.SINGULAR)
        return noun

class Template:

    def __init__(self, string_spec_ls, priority):
        self.string_spec_ls = string_spec_ls
        self.priority = priority

    def save(self):
        return (self.string_spec_ls, self.priority)


if __name__ == '__main__':
    from GRIDD.modules.responsegen_by_templates_spec import ResponseTemplatesSpec
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
    #
    # tfill = ResponseTemplateFiller()
    # tfill.test()


