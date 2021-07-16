from GRIDD.globals import *
import random

from simplenlg.framework.NLGFactory         import *
from simplenlg.realiser.english.Realiser    import *
from simplenlg.lexicon.Lexicon              import *
from simplenlg.phrasespec.VPPhraseSpec      import *

from simplenlg.features.NumberAgreement     import *
from simplenlg.features.Feature             import *
from simplenlg.features.Tense               import *
from simplenlg.features.Person              import *

from itertools import chain


"""
This class works in conjunction with the service-implementation of the InferenceEngine
in order to find appropriate template matches for a given concept graph and properly fill in the 
templates for each match.

Execution Sequence:
    ResponseTemplateFinder
    InferenceEngine
    ResponseTemplateFiller
"""

SPECIAL_NOT_CHECK_AWARE = {'unknown_answer_to_user_q'}

class ResponseTemplateFiller:
    """
    Fills out a template based on the provided variable matches and concept expressions.
    """

    def __init__(self):
        self.lexicon = Lexicon.getDefaultLexicon()
        self.nlgFactory = NLGFactory(self.lexicon)
        self.realiser = Realiser(self.lexicon)

    def __call__(self, matches, expr_dict, cg, aux_state, fallback_options):
        react_cands = []
        present_cands = []
        rpresent_cands = []

        previous_user_requests = [p for p in chain(list(cg.predicates('user', REQ_ARG)), list(cg.predicates('user', REQ_TRUTH)))
                                  if aux_state.get('turn_index', -1) in cg.features.get(p[3], {}).get(UTURN, set())
                                  and not cg.has(p[3], USER_AWARE)]
        answer_checks = {}
        ignore = set()
        for p in previous_user_requests:
            constraints = {t for s,t,l, in cg.metagraph.out_edges(p[2], RREF)}
            for t in constraints:
                if cg.has(predicate_id=t) and cg.type(t) == TYPE:
                    ignore.update({t, cg.object(t)})
            answer_checks[p] = constraints - ignore

        for rule, (pre_graph, post, solutions_list) in matches.items():
            repetition_type = list(post.values())[0].repetition_type
            for match_dict, virtual_preds in solutions_list:
                # add constants to match
                const_matches = {n: n for n in pre_graph.concepts() if n not in match_dict}
                match_dict.update(const_matches)

                if repetition_type == '_r':
                    # (1) pick unused form, if there is more than one form, else pick used form
                    candidates = self._get_candidates(post, aux_state, rule)
                    selection = random.choice(candidates)
                elif repetition_type == '_nr':
                    # if template never used before, do (1)
                    if rule not in aux_state.get('responses', {}):
                        candidates = self._get_candidates(post, aux_state, rule)
                        selection = random.choice(candidates)
                    else:
                        continue # skip to next template
                elif repetition_type == '_ur':
                    # get current realization of previously used form
                    # if unique from previous, do (1)
                    candidates = list(post.keys())
                    prev = aux_state.get('responses', {}).get(rule, None)
                    if prev is None: # template never used before
                        selection = random.choice(candidates)
                    else: # template used before
                        prev_form, prev_string = prev
                        curr = self._fill_template(rule, post[prev_form], match_dict, expr_dict, cg)
                        if curr != prev_string: # is a unique match
                            candidates.remove(prev_form)
                        else: # is not a unique match
                            continue # skip to next template
                        selection = random.choice(candidates)

                rule_info = (rule, selection)
                selection = post[selection]
                response_str = self._fill_template(rule_info, selection, match_dict, expr_dict, cg)
                if response_str is None or (repetition_type == '_nr' and response_str in aux_state.get('all_resp', set())):
                    continue # skip to next template

                if selection.template_type == '_react':
                    react_cands.append((rule_info, match_dict, response_str, selection.priority, selection.topic_anchor))
                elif selection.template_type == '_present':
                    present_cands.append((rule_info, match_dict, response_str, selection.priority, selection.topic_anchor))
                elif selection.template_type == '_rpresent':
                    rpresent_cands.append((rule_info, match_dict, response_str, selection.priority, selection.topic_anchor))

        rp_predicates, rp_string, rp_score, rp_anchor, rp_id = None, None, None, None, None
        if len(rpresent_cands) > 0:
            print('\nReact + Present Options: ')
            rp_predicates, rp_string, rp_score, rp_anchor, rp_id = self.select_best_candidate(rpresent_cands, cg, answer_checks)

        p_predicates, p_string, p_score, p_anchor, p_id = None, None, None, None, None
        if len(present_cands) > 0:
            print('\nPresent Options: ')
            p_predicates, p_string, p_score, p_anchor, p_id = self.select_best_candidate(present_cands, cg, answer_checks)

        r_predicates, r_string, r_score, r_anchor, r_id = None, None, None, None, None
        curr_turn = aux_state.get('turn_index', 0)
        if len(react_cands) > 0:
            print('React Options: ')
            r_predicates, r_string, r_score, r_anchor, r_id = self.select_best_candidate(react_cands, cg, answer_checks, check_aware=False)

        if rp_score is not None and (p_score is None or rp_score >= p_score):
            string = rp_string
            predicates = rp_predicates
            anchor = rp_anchor
            aux_state.setdefault('responses', {})[rp_id[0]] = (rp_id[1], rp_string)
            aux_state.setdefault('all_resp', set()).add(rp_string)
        else:
            if p_string is None:
                string, predicates, anchor = (p_string, p_predicates, p_anchor)
            else:
                string = p_string
                anchor = p_anchor
                aux_state.setdefault('responses', {})[p_id[0]] = (p_id[1], p_string)
                aux_state.setdefault('all_resp', set()).add(p_string)
                predicates = p_predicates
                if curr_turn > 0:
                    s = random.choice(['Yeah .', 'Gotcha .', 'I see .', 'Okay .'])
                else:
                    s = ''
                if r_string is not None:
                    aux_state.setdefault('responses', {})[r_id[0]] = (r_id[1], r_string)
                    aux_state.setdefault('all_resp', set()).add(r_string)
                    s = r_string
                # Do not add reaction predicates to predicates list in order to avoid them being treated as spoken and getting the eturn predicate
                string = s + ' ' + string

        type = "template"
        if string is None: # PICK UNUSED FALLBACK
            # can still use reaction even with fallback
            string = ''
            candidates = list(set(fallback_options.keys()) - set(aux_state.get('fallbacks', [])))
            # candidates = ['ai', 'pet', 'sport', 'movie', 'postpandemicnlg',
            #               'art', 'reading', 'tech', 'food', 'videogame', 'travel', 'phone']
            if len(candidates) > 0:
                selected = random.choice(candidates)
                # selected = candidates[len(aux_state.get('fallbacks', []))] + '_fallback'
                if 'fallbacks' not in aux_state:
                    aux_state['fallbacks'] = []
                if selected not in aux_state['fallbacks']:
                    aux_state['fallbacks'].append(selected)
                predicates, template_d, _ = fallback_options[selected]
                template_obj = list(template_d.values())[0]
                string = template_obj.string_spec_ls
                aux_state.setdefault('all_resp', set()).add(string)
                if r_string is not None:
                    aux_state.setdefault('responses', {})[r_id[0]] = (r_id[1], r_string)
                    string = r_string + string
                type = "fallback"
                anchor = template_obj.topic_anchor
            else:
                string = None
                predicates = None
                anchor = None

        if string is not None:
            string = string.replace("’", "'")

        return (string, predicates, [(anchor, '_tanchor')], type)

    def _get_candidates(self, post, aux_state, rule):
        candidates = list(post.keys())
        if len(candidates) > 1:
            prev = aux_state.get('responses', {}).get(rule, None)
            if prev is not None:
                previous_form, previous_str = prev
                candidates.remove(previous_form)
        return candidates

    def _fill_template(self, rule, post, match_dict, expr_dict, cg):
        string_spec_ls = list(post.string_spec_ls)  # need to create copy so as to not mutate the postcondition in the rule
        try:
            return self.fill_string(match_dict, expr_dict, string_spec_ls, cg)
        except Exception as e:
            print('Error in NLG template filling of %s for rule %s => %s' % (string_spec_ls, rule, e))
            return None

    def select_best_candidate(self, responses, cg, answer_checks, check_aware=True):
        # get highest salience candidate with at least one uncovered predicate
        # prefer answers to unanswered user requests above all else
        candidates = []
        answer_candidates = []

        for rule_info, match_dict, string, priority, topic_anchor in responses:
            rule, selection = rule_info
            # check if template that gives answer to user request
            for req, req_concepts in answer_checks.items():
                if req_concepts.issubset(set(match_dict.values())):
                    answer_candidates.append(rule)
            preds = [cg.predicate(x) for x in match_dict.values() if cg.has(predicate_id=x)
                     and cg.type(x) not in {EXPR, TYPE}]
            if check_aware and rule not in SPECIAL_NOT_CHECK_AWARE:
                req_pred = [cg.predicate(x) for x in match_dict.values() if cg.has(predicate_id=x)
                            and cg.type(x) in {REQ_ARG, REQ_TRUTH} and cg.subject(x) == 'emora'] # check if emora already asked question
                user_awareness = [cg.has(x[3], USER_AWARE) for x in preds]
                user_req_awareness = [cg.has(x[3], USER_AWARE) for x in req_pred]
            if not check_aware or rule in SPECIAL_NOT_CHECK_AWARE or (False in user_awareness and (not user_req_awareness or False in user_req_awareness)):
                # at least one predicate is not known by the user
                # and all request predicates are not known by user, if there are requests in response
                # todo - stress test emora not asking a question she already has answer to or has asked before
                # this should work, but we do have req_unsat predicate as backup, if needed
                concepts = list(match_dict.values())
                sals = [cg.features.get(x, {}).get(SALIENCE, 0) for x in concepts]
                sal_avg = sum(sals) / len(sals)
                # GET COHERENCE BY TOPIC ANCHOR SALIENCE
                coh = cg.features.get(topic_anchor, {}).get(SALIENCE, 0)
                final_score = SAL_WEIGHT * sal_avg + PRIORITY_WEIGHT * priority + COH_WEIGHT * coh
                candidates.append((preds, string, final_score, topic_anchor, rule_info))
                print('\t%s (sal: %.2f, coh: %.2f, pri: %.2f)' % (string, sal_avg, coh, priority))
        print()
        if len(answer_candidates) > 0:
            with_scores = [x for x in candidates if x[4][0] in answer_candidates]
            if len(with_scores) > 0:
                return max(with_scores, key=lambda x: x[2])
        if len(candidates) > 0:
            return max(candidates, key=lambda x: x[2])
        return None, None, None, None, None

    # todo - add in profanity check
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
            if len(intersection) == 0 and t not in {GROUP, 'prp', 'propds'} and not t.startswith(namespace) and '_ner' not in t:
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

    def __init__(self, string_spec_ls, priority, template_type, repetition_type, topic_anchor):
        self.string_spec_ls = string_spec_ls
        self.priority = priority
        self.template_type = template_type
        self.repetition_type = repetition_type
        self.topic_anchor = topic_anchor

    def save(self):
        return (self.string_spec_ls, self.priority, self.template_type, self.repetition_type, self.topic_anchor)

    def load(self, d):
        self.string_spec_ls = d[0]
        self.priority = d[1]
        self.template_type = d[2]
        self.repetition_type = d[3]
        self.topic_anchor = d[4]


if __name__ == '__main__':
    from GRIDD.modules.responsegen_by_templates_spec import ResponseTemplatesSpec
    print(ResponseTemplatesSpec.verify(ResponseTemplateFiller))

    # from os.path import join
    # from GRIDD.data_structures.inference_engine import InferenceEngine
    #
    # tfind = ResponseTemplateFinder(join('GRIDD', 'resources', KB_FOLDERNAME, 'nlg_templates'))
    # infer = InferenceEngine()
    #
    # logic = '''
    # '''
    # cg = ConceptGraph(namespace='wm')
    # ConceptGraph.construct(cg, logic)
    #
    # tfill = ResponseTemplateFiller()
    # tfill.test()


