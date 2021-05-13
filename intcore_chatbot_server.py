import time, json, requests
from os.path import join
from itertools import chain

from GRIDD.utilities.utilities import collect
from GRIDD.data_structures.span import Span
from GRIDD.globals import *
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.intelligence_core import IntelligenceCore
from GRIDD.modules.elit_dp_to_logic_model import ElitDPToLogic
from GRIDD.modules.responsegen_by_templates import ResponseTemplateFiller
from GRIDD.modules.response_selection_salience import ResponseSelectionSalience
from GRIDD.modules.response_expansion import ResponseExpansion
from GRIDD.modules.responsegen_by_rules import ResponseRules
from GRIDD.modules.responsegen_by_model import ResponseGeneration
from GRIDD.modules.response_assembler import ResponseAssembler

from GRIDD.utilities.server import save, load
from inspect import signature

LOCAL = True
IS_SERIALIZING = True

def serialized(*returns):
    def dectorator(f):
        if not IS_SERIALIZING:
            return f
        params = signature(f).parameters
        def f_with_serialization(cls, json):
            kwargs = {}
            # s = time.time()
            for k, serialized in json.items():
                if k in params:
                    obj = load(k, serialized)
                    kwargs[k] = obj
            # print('load - %.2f' % (time.time() - s))
            result = f(cls, **kwargs)
            results = {}
            # s = time.time()
            if isinstance(result, tuple):
                for i, r in enumerate(result):
                    results[returns[i]] = save(returns[i], r)
            elif result is not None:
                results[returns[0]] = save(returns[0], result)
            # print('save - %.2f' % (time.time() - s))
            return results
        return f_with_serialization
    return dectorator

class ChatbotServer:

    def __init__(self, knowledge_base, inference_rules, nlg_templates, starting_wm=None, device=None):
        s = time.time()
        knowledge = collect(*knowledge_base)
        inference_rules = collect(*inference_rules)
        self.starting_wm = None if starting_wm is None else collect(*starting_wm)
        nlg_templates = collect(*nlg_templates)
        self.dialogue_intcore = IntelligenceCore(knowledge_base=knowledge + inference_rules + nlg_templates,
                                                 device=device)
        if self.starting_wm is not None:
            self.dialogue_intcore.consider(self.starting_wm)
        print('IntelligenceCore load: %.2f' % (time.time() - s))

    ###################################################
    ## Pipeline Modules
    ###################################################

    @serialized('aux_state')
    def run_next_turn(self, aux_state):
        aux_state["turn_index"] += 1
        return aux_state

    def init_sentence_caser(self, local_testing=True):
        if not local_testing:
            from GRIDD.modules.sentence_casing import SentenceCaser
        else:
            SentenceCaser = (lambda: (lambda x: x))
        self.sentence_caser = SentenceCaser()

    @serialized('user_utterance')
    def run_sentence_caser(self, user_utterance):
        user_utterance = self.sentence_caser(user_utterance)
        return user_utterance

    def init_elit_models(self):
        from GRIDD.modules.elit_models import ElitModels
        self.elit_models = ElitModels()

    @serialized('elit_results')
    def run_elit_models(self, user_utterance, aux_state):
        if LOCAL:
            input_dict = {"text": [user_utterance, None],
                          "aux_state": [aux_state, aux_state],
                          "conversationId": 'local'}
            response = requests.post('http://cobot-LoadB-2W3OCXJ807QG-1571077302.us-east-1.elb.amazonaws.com',
                                     data=json.dumps(input_dict),
                                     headers={'content-type': 'application/json'},
                                     timeout=3.0)
            json_results = response.json()["context_manager"]
            elit_results = load('elit_results', json_results['elit_results'])
        else:
            if len(user_utterance.strip()) == 0:
                elit_results = {}
            else:
                elit_results = self.elit_models(user_utterance, aux_state)
        return elit_results

    def init_parse2logic(self, device=None):
        nlu_templates = join('GRIDD', 'resources', 'kg_files', 'elit_dp_templates.kg')
        self.elit_dp = ElitDPToLogic(self.dialogue_intcore.knowledge_base,
                                     nlu_templates,
                                     device=device)

    @serialized('mentions', 'merges')
    def run_parse2logic(self, elit_results):
        mentions, merges = self.elit_dp(elit_results)
        return mentions, merges

    @serialized('working_memory')
    def run_mention_bridge(self, mentions, working_memory):
        self.load_working_memory(working_memory)
        namespace = list(mentions.items())[0][1].id_map() if len(mentions) > 0 else "ment_"
        mega_mention_graph = ConceptGraph(namespace=namespace)
        for span, mention_graph in mentions.items():
            ((focus, t, o, i,),) = list(mention_graph.predicates(predicate_type='focus'))
            center_pred = list(mention_graph.predicates(predicate_type='center'))
            if len(center_pred) > 0:
                ((center, t, o, i,),) = center_pred
            else:
                ((center, t, o, i,),) = list(mention_graph.predicates(predicate_type='link'))
            mega_mention_graph.concatenate(mention_graph, predicate_exclusions={'focus', 'center', 'cover'})
            mega_mention_graph.add(span, 'ref', focus)
            mega_mention_graph.add(span, 'type', 'span')
            if not span.startswith('__linking__'):
                mega_mention_graph.add(span, 'def', center)
        self.assign_cover(mega_mention_graph)
        self.dialogue_intcore.consider(mega_mention_graph)
        return self.dialogue_intcore.working_memory

    @serialized('working_memory')
    def run_merge_bridge(self, merges, working_memory):
        self.load_working_memory(working_memory)
        node_merges = []
        for (span1, pos1), (span2, pos2) in merges:
            # if no mention for span, no merge possible
            if working_memory.has(span1) and working_memory.has(span2):
                (concept1,) = working_memory.objects(span1, 'ref')
                concept1 = self._follow_path(concept1, pos1, working_memory)
                (concept2,) = working_memory.objects(span2, 'ref')
                concept2 = self._follow_path(concept2, pos2, working_memory)
                node_merges.append((concept1, concept2))
        self.dialogue_intcore.merge(node_merges)
        self.dialogue_intcore.operate()
        self.dialogue_intcore.update_confidence('user', iterations=CONF_ITER)
        self.dialogue_intcore.update_confidence('emora', iterations=CONF_ITER)
        return self.dialogue_intcore.working_memory

    @serialized('working_memory')
    def run_knowledge_pull(self, working_memory):
        self.load_working_memory(working_memory)
        knowledge_by_source = self.dialogue_intcore.pull_knowledge(limit=100, num_pullers=50, association_limit=10, subtype_limit=10)
        for pred, sources in knowledge_by_source.items():
            if not working_memory.has(*pred) and not working_memory.has(predicate_id=pred[3]):
                self.dialogue_intcore.consider([pred], namespace=self.dialogue_intcore.knowledge_base._ids, associations=sources)
                self.dialogue_intcore.working_memory.metagraph.update(self.dialogue_intcore.knowledge_base.metagraph,
                                                                      self.dialogue_intcore.knowledge_base.metagraph.features,
                                                                      concepts=[pred[3]])
        types = self.dialogue_intcore.pull_types()
        for type in types:
            if not working_memory.has(*type):
                self.dialogue_intcore.consider([type], associations=type[0])
        self.dialogue_intcore.operate()
        return self.dialogue_intcore.working_memory

    @serialized('inference_results')
    def run_dialogue_inference(self, working_memory):
        self.load_working_memory(working_memory)
        inference_results = self.dialogue_intcore.infer()
        return inference_results

    @serialized('working_memory')
    def run_apply_dialogue_inferences(self, inference_results, working_memory):
        self.load_working_memory(working_memory)
        self.dialogue_intcore.apply_inferences(inference_results)
        self.dialogue_intcore.operate()
        self.dialogue_intcore.convert_metagraph_span_links(REF_SP, [REF, VAR])
        self.dialogue_intcore.convert_metagraph_span_links(DP_SUB, [ASS_LINK])
        for so, t, l in working_memory.metagraph.edges(label=ASS_LINK):
            if BASE_UCONFIDENCE not in working_memory.features[t]:
                if working_memory.has(predicate_id=so):
                    if NONASSERT in working_memory.types(so):
                        working_memory.features[t][BASE_UCONFIDENCE] = 0.0
                    else:
                        working_memory.features[t][BASE_UCONFIDENCE] = 1.0
        self.dialogue_intcore.update_confidence('user', iterations=CONF_ITER)
        self.dialogue_intcore.update_confidence('emora', iterations=CONF_ITER)
        self.dialogue_intcore.update_salience(iterations=SAL_ITER)
        return working_memory

    @serialized('rules', 'use_cached')
    def run_reference_identification(self, working_memory):
        self.load_working_memory(working_memory)
        rules = self.dialogue_intcore.working_memory.references()
        use_cached = False
        return rules, use_cached

    @serialized('inference_results', 'rules')
    def run_multi_inference(self, rules, use_cached, working_memory):
        self.load_working_memory(working_memory)
        inference_results = self.dialogue_intcore.nlg_inference_engine.infer(self.dialogue_intcore.working_memory,
                                                                              rules,
                                                                             cached=use_cached)
        rules = {}
        return inference_results, rules

    @serialized('working_memory')
    def run_reference_resolution(self, inference_results, working_memory):
        self.load_working_memory(working_memory)
        wm = self.dialogue_intcore.working_memory
        compatible_pairs = {}
        if len(inference_results) > 0:
            for reference_node, (pre, matches) in inference_results.items():
                compatible_pairs[reference_node] = {}
                for match in matches:
                    if reference_node != match[reference_node]:
                        compatible_pairs[reference_node][match[reference_node]] = []
                        for node in match:
                            if node != reference_node:
                                compatible_pairs[reference_node][match[reference_node]].append((match[node], node))
            pairs_to_merge = []
            for ref_node, compatibilities in compatible_pairs.items():
                resolution_options = []
                span_def = None
                pos_tag = None
                span_nodes = wm.subjects(ref_node, SPAN_REF)
                if span_nodes:
                    (span_node,) = span_nodes
                    span_defs = wm.objects(span_node, SPAN_DEF)
                    if span_defs:
                        (span_def,) = span_defs
                    pos_tag = Span.from_string(span_node).pos_tag
                for ref_match, constraint_matches in compatibilities.items():
                    if (span_def is None or ref_match != span_def) and \
                            (pos_tag is None or pos_tag not in {'prp', 'prop$'} or ref_match not in {'user', 'emora'}):
                        # the `def` obj of reference's span is not candidate, if there is one
                        # user and emora are not candidates for pronoun references
                        if wm.metagraph.out_edges(ref_match, REF):
                            # found other references that match; merge all
                            pairs_to_merge.extend([(ref_match, ref_node)] + constraint_matches)
                        else:
                            # found resolution to reference; merge only one
                            resolution_options.append(ref_match)
                if len(resolution_options) > 0:
                    salient_resol = max(resolution_options,
                                        key=lambda x: wm.features.get(x, {}).get(SALIENCE, 0))
                    pairs_to_merge.extend([(salient_resol, ref_node)] + compatibilities[salient_resol])
            if len(pairs_to_merge) > 0:
                self.merge_references(pairs_to_merge)
        return self.dialogue_intcore.working_memory

    @serialized('working_memory')
    def run_fragment_resolution(self, working_memory, aux_state):
        self.load_working_memory(working_memory)
        wm = self.dialogue_intcore.working_memory

        salient_emora_truth_request = None
        salient_emora_arg_request = None
        salient_emora_request = None
        req_type = None
        emora_truth_requests = [pred for pred in wm.predicates('emora', REQ_TRUTH) if
                                wm.has(pred[3], USER_AWARE) and not wm.has(pred[3], REQ_SAT)]
        if len(emora_truth_requests) > 0:
            salient_emora_truth_request = max(emora_truth_requests,
                                              key=lambda pred: wm.features.get(pred[3], {}).get(SALIENCE, 0))
            truth_sal = wm.features.get(salient_emora_truth_request[3], {}).get(SALIENCE, 0)
        emora_arg_requests = [pred for pred in wm.predicates('emora', REQ_ARG) if
                              wm.has(pred[3], USER_AWARE) and not wm.has(pred[3], REQ_SAT)]
        if len(emora_arg_requests) > 0:
            salient_emora_arg_request = max(emora_arg_requests,
                                            key=lambda pred: wm.features.get(pred[3], {}).get(SALIENCE, 0))
            arg_sal = wm.features.get(salient_emora_arg_request[3], {}).get(SALIENCE, 0)
        if salient_emora_arg_request and salient_emora_truth_request:
            if truth_sal >= arg_sal:
                salient_emora_request = salient_emora_truth_request
                req_type = REQ_TRUTH
            else:
                salient_emora_request = salient_emora_arg_request
                req_type = REQ_ARG
        elif salient_emora_arg_request:
            salient_emora_request = salient_emora_arg_request
            req_type = REQ_ARG
        elif salient_emora_truth_request:
            salient_emora_request = salient_emora_truth_request
            req_type = REQ_TRUTH

        if salient_emora_request is not None:
            request_focus = salient_emora_request[2]
            current_user_spans = [s for s in wm.subtypes_of("span") if
                                  s != "span" and int(wm.features[s]["span_data"].turn) == aux_state["turn_index"]]
            current_user_concepts = {o for s in current_user_spans for o in
                                     chain(wm.objects(s, SPAN_REF), wm.objects(s, SPAN_DEF))}
            if req_type == REQ_TRUTH:  # special case - y/n question requires yes/no fragment as answer (or full resolution from earlier in pipeline)
                fragment_request_merges = self.truth_fragment_resolution(request_focus, current_user_concepts, wm)
            else:
                fragment_request_merges = self.arg_fragment_resolution(request_focus, current_user_concepts, wm)
            if len(fragment_request_merges) > 0:
                # set salience of all request predicates to salience of fragment
                fragment = fragment_request_merges[0][
                    0]  # first fragment merge must be the origin request even for truth fragments which may include additional arg merges too!
                ref_links = [e for e in wm.metagraph.out_edges(request_focus) if e[2] == REF and wm.has(predicate_id=e[1])]
                for so, t, l in ref_links:
                    wm.features.setdefault(t, {})[SALIENCE] = wm.features.setdefault(fragment, {}).get(SALIENCE, 0)
                    # wm.features[t][BASE] = True todo - check if the BASE indication matters here
            self.merge_references(fragment_request_merges)
            self.dialogue_intcore.operate()
        self.dialogue_intcore.update_confidence('user', iterations=CONF_ITER)
        self.dialogue_intcore.update_confidence('emora', iterations=CONF_ITER)
        self.dialogue_intcore.update_salience(iterations=SAL_ITER)
        return self.dialogue_intcore.working_memory

    def init_template_nlg(self):
        self.template_filler = ResponseTemplateFiller()

    @serialized('working_memory', 'use_cached')
    def run_prepare_template_nlg(self, working_memory):
        self.load_working_memory(working_memory)
        self.dialogue_intcore.decay_salience()
        for pred in self.dialogue_intcore.pull_expressions():
            if not working_memory.has(*pred):
                working_memory.add(*pred)
        use_cached = True
        return self.dialogue_intcore.working_memory, use_cached

    @serialized('template_response_sel', 'aux_state')
    def run_template_fillers(self, inference_results, working_memory, aux_state):
        template_response_sel = self.template_filler(inference_results, working_memory, aux_state)
        if template_response_sel[0] is not None:
            aux_state.setdefault('spoken_responses', []).append(template_response_sel[0])
        return template_response_sel, aux_state

    def init_response_selection(self):
        self.response_selection = ResponseSelectionSalience()

    @serialized('aux_state', 'response_predicates')
    def run_response_selection(self, working_memory, aux_state, template_response_sel):
        self.load_working_memory(working_memory)
        aux_state, response_predicates = self.response_selection(aux_state, self.dialogue_intcore.working_memory,
                                                                 template_response_sel)
        return aux_state, response_predicates

    def init_response_expansion(self):
        self.response_expansion = ResponseExpansion(self.dialogue_intcore.knowledge_base)

    @serialized('expanded_response_predicates', 'working_memory')
    def run_response_expansion(self, response_predicates, working_memory):
        self.load_working_memory(working_memory)
        expanded_response_predicates, working_memory = self.response_expansion(response_predicates,
                                                               self.dialogue_intcore.working_memory)
        return expanded_response_predicates, working_memory

    def init_response_by_rules(self):
        self.response_by_rules = ResponseRules()

    @serialized('rule_responses')
    def run_response_by_rules(self, aux_state, expanded_response_predicates):
        rule_responses = self.response_by_rules(aux_state, expanded_response_predicates)
        return rule_responses

    def init_response_nlg_model(self, model=None, device='cpu'):
        self.response_nlg_model = ResponseGeneration(model, device)

    @serialized('nlg_responses')
    def run_response_nlg_model(self, expanded_response_predicates):
        if LOCAL:
            input_dict = {"expanded_response_predicates": [expanded_response_predicates, None],
                          "conversationId": 'local'}
            response = requests.post('http://cobot-LoadB-1L3YPB9TGV71P-1610005595.us-east-1.elb.amazonaws.com',
                                     data=json.dumps(input_dict),
                                     headers={'content-type': 'application/json'},
                                     timeout=3.0)
            response = response.json()
            if 'context_manager' in response:
                nlg_responses = json.loads(response['context_manager']['nlg_responses'])
            else:
                nlg_responses = []
        else:
            nlg_responses = self.response_nlg_model(expanded_response_predicates)
        return nlg_responses

    def init_response_assember(self):
        self.response_assembler = ResponseAssembler()

    @serialized('response', 'working_memory')
    def run_response_assembler(self, working_memory, aux_state, rule_responses, nlg_responses):
        response = self.response_assembler(aux_state, rule_responses, nlg_responses)
        self.load_working_memory(working_memory)
        self.dialogue_intcore.update_salience(iterations=SAL_ITER)
        self.dialogue_intcore.decay_salience()
        self.dialogue_intcore.prune_predicates_of_type({AFFIRM, REJECT, EXPR}, {EXPR})
        self.dialogue_intcore.prune_attended(keep=PRUNE_THRESHOLD)
        return response, self.dialogue_intcore.working_memory

    ###################################################
    ## Helpers
    ###################################################

    def load_working_memory(self, working_memory):
        if working_memory is not None:
            self.dialogue_intcore.working_memory = working_memory
        else:
            self.dialogue_intcore.working_memory = ConceptGraph(namespace='wm', supports={AND_LINK: False})
            self.dialogue_intcore.consider(self.starting_wm)

    def assign_cover(self, graph, concepts=None):
        if concepts is None:
            concepts = graph.concepts()
        for concept in concepts:
            if not graph.has(predicate_id=concept) or graph.type(concept) not in PRIM and not graph.has(concept, USER_AWARE):
                i2 = graph.add(concept, USER_AWARE)
                graph.features[i2][BASE_UCONFIDENCE] = 1.0

    def _follow_path(self, concept, pos, working_memory):
        if pos == 'subject':
            return working_memory.subject(concept)
        elif pos == 'object':
            return working_memory.object(concept)
        elif pos == 'type':
            return working_memory.type(concept)
        return concept

    def merge_references(self, reference_pairs):
        wm = self.dialogue_intcore.working_memory
        for match_node, ref_node in reference_pairs:
            # identify user answers to emora requests and add req_sat monopredicate on request predicate
            if not wm.metagraph.out_edges(match_node, REF):
                truths = list(wm.predicates('emora', REQ_TRUTH, ref_node))
                if truths:
                    wm.add(truths[0][3], REQ_SAT)
                    if not wm.has(truths[0][3], USER_AWARE):
                        i2 = wm.add(truths[0][3], USER_AWARE)
                        wm.features[i2][BASE_UCONFIDENCE] = 1.0
                else:
                    args = list(wm.predicates('emora', REQ_ARG, ref_node))
                    if args:
                        wm.add(args[0][3], REQ_SAT)
                        if not wm.has(args[0][3], USER_AWARE):
                            i2 = wm.add(args[0][3], USER_AWARE)
                            wm.features[i2][BASE_UCONFIDENCE] = 1.0
            # ref_node takes confidence of match_node
            buc = wm.features.get(match_node, {}).get(BASE_UCONFIDENCE, None)
            if buc is not None:
                wm.features.setdefault(ref_node, {})[BASE_UCONFIDENCE] = buc
            bc = wm.features.get(match_node, {}).get(BASE_CONFIDENCE, None)
            if bc is not None:
                wm.features.setdefault(ref_node, {})[BASE_CONFIDENCE] = bc
        self.dialogue_intcore.merge(reference_pairs)

    def arg_fragment_resolution(self, request_focus, current_user_concepts, wm):
        fragment_request_merges = []
        types = wm.types()
        request_focus_types = types[request_focus] - {request_focus}
        salient_concepts = sorted(current_user_concepts, key=lambda c: wm.features.get(c, {}).get(SALIENCE, 0),
                                  reverse=True)
        for c in salient_concepts:
            if c != request_focus and request_focus_types < (types[c] - {c}):
                subtype_set = current_user_concepts.intersection(wm.subtypes_of(c)) - {c}
                # if concept is a reference or if other salient concepts are its subtypes, dont treat current concept as answer fragment
                if not subtype_set and not wm.metagraph.out_edges(c, REF):
                    fragment_request_merges.append((c, request_focus))
                    break
        return fragment_request_merges

    def truth_fragment_resolution(self, request_focus, current_user_concepts, wm):
        fragment_request_merges = []
        indicator_preds = [p[3] for p in list(wm.predicates('user', AFFIRM)) + list(wm.predicates('user', REJECT))]
        options = set(indicator_preds).intersection(current_user_concepts)
        if len(indicator_preds) > 0: # find yes or no answer to question
            max_indicator = max(options, key=lambda p: wm.features.get(p[3], {}).get(SALIENCE, 0))
            fragment_request_merges.append((wm.object(max_indicator), request_focus))
        else:
            # todo - map `i do/nt` ~ do(user), `i have/nt` ~ have(user), and `i am/not` ~ am(user) to yes/no preds
            pass
        # find type-compatible argument match for non-predicates, if there is one
        # todo - expand to match predicate arguments too
        within_request_vars = {x for x in wm.metagraph.targets(request_focus, VAR) if not wm.has(predicate_id=x)}
        for v in within_request_vars:
            arg_merges = self.arg_fragment_resolution(v, current_user_concepts, wm)
            if len(arg_merges) > 0:
                if len(fragment_request_merges) == 0:
                    affirm_obj = wm.id_map().get()
                    i = wm.add('user', AFFIRM, affirm_obj)
                    if not wm.has(i, USER_AWARE):
                        i2 = wm.add(i, USER_AWARE)
                        wm.features[i2][BASE_UCONFIDENCE] = 1.0
                    wm.features[affirm_obj][SALIENCE] = 1.0
                    wm.features[i][SALIENCE] = 1.0
                    fragment_request_merges.append((affirm_obj, request_focus))
                fragment_request_merges.extend(arg_merges)
                break
        return fragment_request_merges

    ###################################################
    ## Run Full Pipeline
    ###################################################

    def full_init(self, device=None):
        self.init_sentence_caser()
        if not LOCAL:
            self.init_elit_models()
        self.init_parse2logic(device=device)
        self.init_template_nlg()
        self.init_response_selection()
        self.init_response_expansion()
        self.init_response_by_rules()
        self.init_response_nlg_model()
        self.init_response_assember()

    def respond(self, user_utterance, working_memory, aux_state):
        aux_state = self.run_next_turn(aux_state)
        user_utterance = self.run_sentence_caser(user_utterance)
        elit_results = self.run_elit_models(user_utterance, aux_state)
        mentions, merges = self.run_parse2logic(elit_results)
        working_memory = self.run_mention_bridge(mentions, working_memory)
        working_memory = self.run_merge_bridge(merges, working_memory)
        working_memory = self.run_knowledge_pull(working_memory)

        inference_results = self.run_dialogue_inference(working_memory)
        working_memory = self.run_apply_dialogue_inferences(inference_results, working_memory)
        rules, use_cached = self.run_reference_identification(working_memory)
        inference_results, rules = self.run_multi_inference(rules, use_cached, working_memory)
        working_memory = self.run_reference_resolution(inference_results, working_memory)
        working_memory = self.run_fragment_resolution(working_memory, aux_state)

        inference_results = self.run_dialogue_inference(working_memory)
        working_memory = self.run_apply_dialogue_inferences(inference_results, working_memory)
        rules, use_cached = self.run_reference_identification(working_memory)
        inference_results, rules = self.run_multi_inference(rules, use_cached, working_memory)
        working_memory = self.run_reference_resolution(inference_results, working_memory)
        working_memory = self.run_fragment_resolution(working_memory, aux_state)

        rules, use_cached = self.run_prepare_template_nlg(working_memory)
        inference_results, rules = self.run_multi_inference(rules, use_cached, working_memory)
        template_response_sel, aux_state = self.run_template_fillers(inference_results, working_memory,
                                                                        aux_state)
        aux_state, response_predicates = self.run_response_selection(working_memory, aux_state,
                                                                     template_response_sel)
        expanded_response_predicates, working_memory = self.run_response_expansion(response_predicates,
                                                                                   working_memory)
        rule_responses = self.run_response_by_rules(aux_state, expanded_response_predicates)
        nlg_responses = self.run_response_nlg_model(expanded_response_predicates)
        response, working_memory = self.run_response_assembler(working_memory, aux_state, rule_responses, nlg_responses)
        return response, working_memory, aux_state

    def respond_serialize(self, user_utterance, working_memory, aux_state):
        state = {'user_utterance': save('user_utterance', user_utterance),
                 'working_memory': save('working_memory', working_memory),
                 'aux_state': save('aux_state', aux_state)
                }

        state_update = self.run_next_turn(state)
        state.update(state_update)
        state_update = self.run_sentence_caser(state)
        state.update(state_update)
        state_update = self.run_elit_models(state)
        state.update(state_update)
        state_update = self.run_parse2logic(state)
        state.update(state_update)
        state_update = self.run_mention_bridge(state)
        state.update(state_update)

        state_update = self.run_merge_bridge(state)
        state.update(state_update)
        state_update = self.run_knowledge_pull(state)
        state.update(state_update)

        state_update = self.run_dialogue_inference(state)
        state.update(state_update)
        state_update = self.run_apply_dialogue_inferences(state)
        state.update(state_update)
        state_update = self.run_reference_identification(state)
        state.update(state_update)
        state_update = self.run_multi_inference(state)
        state.update(state_update)
        state_update = self.run_reference_resolution(state)
        state.update(state_update)
        state_update = self.run_fragment_resolution(state)
        state.update(state_update)

        state_update = self.run_dialogue_inference(state)
        state.update(state_update)
        state_update = self.run_apply_dialogue_inferences(state)
        state.update(state_update)
        state_update = self.run_reference_identification(state)
        state.update(state_update)
        state_update = self.run_multi_inference(state)
        state.update(state_update)
        state_update = self.run_reference_resolution(state)
        state.update(state_update)
        state_update = self.run_fragment_resolution(state)
        state.update(state_update)

        state_update = self.run_prepare_template_nlg(state)
        state.update(state_update)
        state_update = self.run_multi_inference(state)
        state.update(state_update)
        state_update = self.run_template_fillers(state)
        state.update(state_update)
        state_update = self.run_response_selection(state)
        state.update(state_update)
        state_update = self.run_response_expansion(state)
        state.update(state_update)
        state_update = self.run_response_by_rules(state)
        state.update(state_update)
        state_update = self.run_response_nlg_model(state)
        state.update(state_update)
        state_update = self.run_response_assembler(state)
        state.update(state_update)

        return load("response", state["response"]), \
               load("working_memory", state["working_memory"]), \
               load("aux_state", state["aux_state"])

    def run(self):
        wm = self.dialogue_intcore.working_memory.copy()
        aux_state = {'turn_index': -1}
        utter = input('User: ')
        while utter != 'q':
            if utter.strip() != '':
                s = time.time()
                if IS_SERIALIZING:
                    response, wm, aux_state = self.respond_serialize(utter, wm, aux_state)
                else:
                    response, wm, aux_state = self.respond(utter, wm, aux_state)
                elapsed = time.time() - s
                print('[%.2f s] %s\n' % (elapsed, response))
            utter = input('User: ')

def get_filepaths():
    kb_dir = join('GRIDD', 'resources', 'kg_files', 'kb')
    kb = [kb_dir]
    rules_dir = join('GRIDD', 'resources', 'kg_files', 'rules')
    rules = [rules_dir]
    wm = [join('GRIDD', 'resources', 'kg_files', 'wm')]
    nlg_templates = [join('GRIDD', 'resources', 'kg_files', 'nlg_templates')]
    return kb, rules, nlg_templates, wm

if __name__ == '__main__':
    kb, rules, nlg_templates, wm = get_filepaths()

    chatbot = ChatbotServer(kb, rules, nlg_templates, wm, device='cuda:1')

    chatbot.full_init(device='cuda:1')
    chatbot.run()