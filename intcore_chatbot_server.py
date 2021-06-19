from os.path import join
import sys, os
sys.path.append(os.getcwd())

import time, json, requests
from itertools import chain

from GRIDD.utilities.utilities import collect, _process_requests, _process_answers

from GRIDD.data_structures.span import Span
from GRIDD.globals import *
from GRIDD.intcore_server_globals import *

from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.intelligence_core import IntelligenceCore
if INFERENCE:
    from GRIDD.data_structures.graph_matching.inference_engine import InferenceEngine
from GRIDD.modules.ner_mentions import get_ner_mentions

from GRIDD.utilities.server import save, load
from inspect import signature

from GRIDD.utilities.profiler import profiler as p

def serialized(*returns):
    def dectorator(f):
        if not IS_SERIALIZING:
            return f
        params = signature(f).parameters
        def f_with_serialization(cls, json):
            kwargs = {}
            s = time.time()
            for k, serialized in json.items():
                if k in params:
                    obj = load(k, serialized)
                    kwargs[k] = obj
            print(f'{f.__name__[:20]:20} serial load - {time.time() - s:.2f}', end= ' ')
            result = f(cls, **kwargs)
            results = {}
            s = time.time()
            if isinstance(result, tuple):
                for i, r in enumerate(result):
                    results[returns[i]] = save(returns[i], r)
            elif result is not None:
                results[returns[0]] = save(returns[0], result)
            print('save - %.2f' % (time.time() - s))
            return results
        return f_with_serialization
    return dectorator

class ChatbotServer:

    def __init__(self, knowledge_base, inference_rules, nlg_templates, fallbacks, starting_wm=None, device=None):
        s = time.time()
        knowledge = collect(*knowledge_base)
        inference_rules = collect(*inference_rules)
        self.starting_wm = None if starting_wm is None else collect(*starting_wm)
        nlg_templates = collect(*nlg_templates)
        fallbacks = collect(*fallbacks)
        self.dialogue_intcore = IntelligenceCore(knowledge_base=knowledge, inference_rules=inference_rules,
                                                 nlg_templates=nlg_templates, fallbacks=fallbacks, device=device)
        if INFERENCE:
            self.reference_engine = InferenceEngine(device=device)
        if self.starting_wm is not None:
            self.dialogue_intcore.consider(list(self.starting_wm.values()))
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
        words = user_utterance.split()
        user_utterance = ' '.join(words[:UTTER_TRUNC]) # safeguard out of memory exception in rest of pipeline by limiting length of user utterance
        user_utterance = self.sentence_caser(user_utterance)
        return user_utterance

    def init_elit_models(self):
        from GRIDD.modules.elit_models import ElitModels
        self.elit_models = ElitModels()

    @serialized('elit_results')
    def run_elit_models(self, user_utterance, aux_state):
        if LOCAL:
            input_dict = {"user_utterance": user_utterance,
                          "aux_state": aux_state,
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
                words = user_utterance.split()
                user_utterance = ' '.join(words[:UTTER_TRUNC])  # safeguard for if sentence caser fails
                elit_results = self.elit_models(user_utterance, aux_state)
        # span updates for errors in elit models (lemmatization, pos)
        PARSE_ERRORS = {
            'swam': ('swim', 'VBD')
        }
        for i,span in enumerate(elit_results.get("tok", [])):
            updates = PARSE_ERRORS.get(span.string, None)
            if updates is not None:
                lemma, pos = updates[0], updates[1]
                if lemma is not None:
                    span.expression = lemma
                    elit_results['lem'][i] = lemma
                if pos is not None:
                    span.pos_tag = pos.lower()
                    elit_results['pos'][i] = pos
        return elit_results

    def init_parse2logic(self, device=None):
        from GRIDD.modules.elit_dp_to_logic_model import ElitDPToLogic
        file = join('GRIDD', 'resources', 'kg_files', 'elit_dp_templates.kg')
        if USECACHE:
            if not os.path.exists(NLUCACHE):
                os.mkdir(NLUCACHE)
            cached = {f for f in os.listdir(NLUCACHE) if os.path.isfile(os.path.join(NLUCACHE, f))}
            cache_version = (file + '.json').replace(os.sep, CACHESEP)
            cached = {c for c in cached if os.path.getmtime(os.path.join(NLUCACHE, c)) > os.path.getmtime(c.replace(CACHESEP, os.sep).replace('.json',''))}
            if cache_version in cached:
                with open(os.path.join(NLUCACHE, cache_version), 'r') as f:
                    d = json.load(f)
                rules = {}
                for rule, (pre, post, vars) in d.items():
                    pre_cg = ConceptGraph(namespace=pre['namespace'])
                    pre_cg.load(pre)
                    post_cg = ConceptGraph(namespace=post['namespace'])
                    post_cg.load(post)
                    vars = set(vars)
                    rules[rule] = (pre_cg, post_cg, vars)
                self.elit_dp = ElitDPToLogic(self.dialogue_intcore.knowledge_base,
                                             rules, device=device)
            else:
                savefile = os.path.join(NLUCACHE, (file + '.json').replace(os.sep, CACHESEP))
                self.elit_dp = ElitDPToLogic(self.dialogue_intcore.knowledge_base,
                                             None, device=device)
                rules = self.elit_dp.parse_rules_from_file(file)
                d = {rule: (pre.save(), post.save(), list(vars)) for rule, (pre, post, vars) in rules.items()}
                with open(savefile, 'w') as f:
                    json.dump(d, f, indent=2)
                self.elit_dp.intcore.inference_engine.add(rules, NLU_NAMESPACE)
                self.elit_dp.intcore.inference_engine.matcher.process_queries()
        else:
            self.elit_dp = ElitDPToLogic(self.dialogue_intcore.knowledge_base,
                                         file, device=device)

    @serialized('mentions', 'merges')
    def run_parse2logic(self, elit_results):
        mentions, merges = self.elit_dp(elit_results)
        return mentions, merges

    def init_multiword_matcher(self):
        from GRIDD.modules.multiword_expression_mentions import MultiwordExpressionMatcher
        self.multiword_matcher = MultiwordExpressionMatcher(self.dialogue_intcore.knowledge_base)

    @serialized('multiword_mentions')
    def run_multiword_matcher(self, elit_results):
        multiword_mentions = self.multiword_matcher(elit_results)
        return multiword_mentions

    @serialized('ner_mentions')
    def run_ner_mentions(self, elit_results):
        ner_mentions = get_ner_mentions(elit_results)
        return ner_mentions

    @serialized('subspans', 'working_memory')
    def run_mention_bridge(self, mentions, multiword_mentions, ner_mentions, working_memory, aux_state):
        self.load_working_memory(working_memory)
        if mentions is None: mentions = {}
        if multiword_mentions is None: multiword_mentions = {}
        namespace = list(mentions.items())[0][1].id_map() if len(mentions) > 0 else "ment_"
        mega_mention_graph = ConceptGraph(namespace=namespace)

        # multiword mentions supersede single word mentions
        covered_idx = {}
        for span, mention_graph in multiword_mentions.items():
            ((focus, t, o, i,),) = list(mention_graph.predicates(predicate_type='focus'))
            center_pred = list(mention_graph.predicates(predicate_type='center'))
            ((center, t, o, i,),) = center_pred
            mapped_ids = mega_mention_graph.concatenate(mention_graph, predicate_exclusions={'focus', 'center'})
            mega_mention_graph.add(span, SPAN_REF, mapped_ids.get(focus))
            mega_mention_graph.add(span, TYPE, 'span')
            # mega_mention_graph.add(span, 'def', mapped_ids.get(center))
            span_obj = Span.from_string(span)
            covered_idx.update({i: span for i in range(span_obj.start, span_obj.end)}) # map inner indices to the multiword

        # NER mention is used as a last resort.
        # Multi-word expressions and single-word expressions supersede the identification of an NER mention.
        for span, mention_graph in ner_mentions.items():
            span_obj = Span.from_string(span)
            # If NER mention overlaps with a multi-word expression, don't take it.
            span_range = set(range(span_obj.start, span_obj.end))
            if span_range.intersection(set(covered_idx.keys())):
                continue
            # If NER mention can be broken into recognized (non-linking) single word expressions, don't take it.
            # Only if NER captures a token that is not otherwise recognized do we take it.
            decomposable = True
            for single_span, single_mention_graph in mentions.items():
                if not single_span.startswith('__linking__'):
                    single_span_obj = Span.from_string(single_span)
                    if single_span_obj.start in span_range:
                        ((focus, t, o, i,),) = list(single_mention_graph.predicates(predicate_type='focus'))
                        if UNKNOWN_TYPES.intersection(single_mention_graph.types(focus)):
                            decomposable = False
                            break
            if not decomposable:
                ((focus, t, o, i,),) = list(mention_graph.predicates(predicate_type='focus'))
                center_pred = list(mention_graph.predicates(predicate_type='center'))
                ((center, t, o, i,),) = center_pred
                mapped_ids = mega_mention_graph.concatenate(mention_graph, predicate_exclusions={'focus', 'center'})
                mega_mention_graph.add(span, SPAN_REF, mapped_ids.get(focus))
                mega_mention_graph.add(span, TYPE, 'span')
                # mega_mention_graph.add(span, 'def', mapped_ids.get(center))
                span_obj = Span.from_string(span)
                covered_idx.update({i: span for i in range(span_obj.start, span_obj.end)})  # map inner indices to ner mention

        # only add mentions that are not subset of added multiword or ner mentions
        subspans = {}
        for span, mention_graph in mentions.items():
            if not span.startswith('__linking__'):
                # linking constructions need to be maintained even if based on subword of other mention type
                # the merge process will appropriately handle these cases
                span_obj = Span.from_string(span)
                if span_obj.start in covered_idx: # map single word spans to encapsulating other mention types
                    subspans[span] = covered_idx[span_obj.start]
                    continue
            ((focus, t, o, i,),) = list(mention_graph.predicates(predicate_type='focus'))
            center_pred = list(mention_graph.predicates(predicate_type='center'))
            if len(center_pred) > 0:
                ((center, t, o, i,),) = center_pred
            else:
                ((center, t, o, i,),) = list(mention_graph.predicates(predicate_type='link'))
            mega_mention_graph.concatenate(mention_graph, predicate_exclusions={'focus', 'center', 'cover', 'link'})
            mega_mention_graph.add(span, SPAN_REF, focus)
            mega_mention_graph.add(span, TYPE, 'span')
            if not span.startswith('__linking__'):
                # mega_mention_graph.add(span, 'def', center)
                span_obj = Span.from_string(span)
                if span_obj.pos_tag in {'prp', 'prop$'}:
                    mega_mention_graph.add(focus, TYPE, span_obj.pos_tag)
        self.assign_cover(mega_mention_graph)
        for s,t,l in mega_mention_graph.metagraph.edges():
            update = False
            if s in subspans:
                s = subspans[s]
                update = True
            if t in subspans:
                t = subspans[t]
                update = True
            if update and not mega_mention_graph.has(s,t,l):
                mega_mention_graph.metagraph.add(s,t,l)
        _process_requests(mega_mention_graph)
        # user turn tracking
        for s,t,o,i in list(mega_mention_graph.predicates()):
            if t not in {SPAN_DEF, USER_AWARE, ASSERT}:
                if t == SPAN_REF: # will get floating concepts (e.g. not involved in any other predicate)
                    elements = [o]
                elif t == TYPE:
                    if o != 'span':
                        elements = [s, o, i]
                    else: # do not include type predicates on spans
                        elements = []
                else:
                    elements = [s, o, i]
                for c in elements:
                    if c is not None:
                        mega_mention_graph.features.setdefault(c, {}).setdefault(UTURN, []).append(int(aux_state.get('turn_index', -1)))

        self.dialogue_intcore.consider(mega_mention_graph)
        return subspans, self.dialogue_intcore.working_memory

    @serialized('working_memory', 'aux_state')
    def run_merge_bridge(self, merges, subspans, working_memory, aux_state):
        self.load_working_memory(working_memory)
        if merges is None:
            merges = []
        node_merges = []
        for (span1, pos1), (span2, pos2) in merges:
            has_span1 = self.dialogue_intcore.working_memory.has(span1)
            has_span2 = self.dialogue_intcore.working_memory.has(span2)
            # if no mention for span, no merge possible
            if has_span1 and has_span2:
                node_merges.append(self._convert_span_to_node_merges(span1, pos1, span2, pos2))
            # update merge to be between multiword and nonsubword, where appropriate
            # only appropriate if relationship is non-predicate relation (i.e. not subj or obj)
            elif has_span2 and span1 in subspans and pos1 == 'self':
                node_merges.append(self._convert_span_to_node_merges(subspans[span1], pos1, span2, pos2))
            elif has_span1 and span2 in subspans and pos2 == 'self':
                node_merges.append(self._convert_span_to_node_merges(span1, pos1, subspans[span2], 'self'))
            elif span1 in subspans and span2 in subspans:
                if subspans[span1] != subspans[span2]:
                    print('[WARNING!] Found merge between 2 subspans that are not from the same '
                          'multiword span: %s -> %s, %s -> %s'
                          %(span1, subspans[span1], span2, subspans[span2]))
        self.dialogue_intcore.merge(node_merges, no_warning=True)
        self.dialogue_intcore.operate(self.dialogue_intcore.universal_operators, aux_state=aux_state)
        self.dialogue_intcore.operate(self.dialogue_intcore.wm_operators, aux_state=aux_state)
        self.dialogue_intcore.convert_metagraph_span_links(DP_SUB, [ASS_LINK])
        for so, t, l in self.dialogue_intcore.working_memory.metagraph.edges(label=ASS_LINK):
            if self.dialogue_intcore.working_memory.has(predicate_id=so) and NONASSERT in self.dialogue_intcore.working_memory.types(so):
                self.dialogue_intcore.working_memory.add(t, 'maybe')
        #p.stop()
        return self.dialogue_intcore.working_memory, aux_state

    @serialized('working_memory', 'aux_state')
    def run_knowledge_pull(self, working_memory, aux_state):
        self.load_working_memory(working_memory)
        working_memory = self.dialogue_intcore.working_memory
        knowledge_by_source = self.dialogue_intcore.pull_knowledge(limit=100, num_pullers=50, association_limit=10, subtype_limit=10)
        for pred, sources in knowledge_by_source.items():
            if not working_memory.has(*pred) and not working_memory.has(predicate_id=pred[3]):
                self.dialogue_intcore.consider([pred], namespace=self.dialogue_intcore.knowledge_base._ids, associations=sources)
                working_memory.metagraph.update(self.dialogue_intcore.knowledge_base.metagraph,
                                                                      self.dialogue_intcore.knowledge_base.metagraph.features,
                                                                      concepts=[pred[3]])
                if pred[1] in {REQ_ARG, REQ_TRUTH}: # if request pulled from KB, add req_unsat to it
                    working_memory.add(pred[3], REQ_UNSAT)
        self._update_types(working_memory)
        self.dialogue_intcore.operate(self.dialogue_intcore.universal_operators, aux_state=aux_state)
        self.dialogue_intcore.operate(self.dialogue_intcore.wm_operators, aux_state=aux_state)
        return self.dialogue_intcore.working_memory, aux_state

    @serialized('inference_results')
    def run_dialogue_inference(self, working_memory, aux_state):
        self.load_working_memory(working_memory)
        inference_results = self.dialogue_intcore.infer(aux_state)
        return inference_results

    @serialized('working_memory', 'aux_state')
    def run_apply_dialogue_inferences(self, inference_results, working_memory, aux_state):
        self.load_working_memory(working_memory)
        #p.start('apply')
        self.dialogue_intcore.apply_inferences(inference_results)
        #p.next('update types')
        self._update_types(self.dialogue_intcore.working_memory)
        #p.next('operate')
        self.dialogue_intcore.operate(self.dialogue_intcore.universal_operators, aux_state=aux_state)
        self.dialogue_intcore.operate(self.dialogue_intcore.wm_operators, aux_state=aux_state)
        #p.next('sal')
        self.dialogue_intcore.update_salience(iterations=SAL_ITER)
        #p.stop()
        return working_memory, aux_state

    @serialized('rules', 'use_cached')
    def run_reference_identification(self, working_memory):
        self.load_working_memory(working_memory)
        self.dialogue_intcore.convert_metagraph_span_links(REF_SP, [REF, VAR])
        rules = self.dialogue_intcore.working_memory.references()
        return rules

    @serialized('inference_results', 'rules')
    def run_dynamic_inference(self, rules, working_memory, aux_state):
        self.load_working_memory(working_memory)
        inference_results = self.reference_engine.infer(self.dialogue_intcore.working_memory, aux_state, rules,
                                                        cached=False, remove_rules=True)
        return inference_results, {}

    @serialized('inference_results')
    def run_template_inference(self, working_memory, aux_state):
        self.load_working_memory(working_memory)
        inference_results = self.dialogue_intcore.nlg_inference_engine.infer(self.dialogue_intcore.working_memory, aux_state)
        return inference_results

    @serialized('working_memory')
    def run_reference_resolution(self, inference_results, working_memory, aux_state):
        self.load_working_memory(working_memory)
        wm = self.dialogue_intcore.working_memory
        if inference_results is None:
            inference_results = {}
        compatible_pairs = {}
        if len(inference_results) > 0:
            for reference_node, (pre, matches) in inference_results.items():
                compatible_pairs[reference_node] = {}
                for match, virtual_preds in matches:
                    # do not want match between itself and itself
                    # also, ref node and match must either both be predicates or both be entities
                    if reference_node in match and reference_node != match[reference_node] and \
                        ((wm.has(predicate_id=match[reference_node]) and wm.has(predicate_id=reference_node)) or
                         (not wm.has(predicate_id=match[reference_node]) and not wm.has(predicate_id=reference_node))):
                        compatible_pairs[reference_node][match[reference_node]] = []
                        for node in match:
                            if node != reference_node:
                                if not node.startswith('__virt_') and not match[node].startswith('__virt_'): # nothing to merge if matched node is virtual type
                                    compatible_pairs[reference_node][match[reference_node]].append((match[node], node))
            wm_types = wm.types(set(compatible_pairs.keys()))
            pairs_to_merge = [] # todo - make into a set???
            for ref_node, compatibilities in compatible_pairs.items():
                resolution_options = []
                ref_types = wm_types[ref_node]
                for ref_match, constraint_matches in compatibilities.items():
                    if ref_match not in ref_types and (('prp' not in ref_types and 'prop$' not in ref_types) or ref_match not in {'user', 'emora'}):
                        # any type of the reference is not a candidate
                        # user and emora are not candidates for pronoun references
                        if wm.metagraph.targets(ref_match, REF):
                            # found other references that perfectly match (exact same reference constraints); merge all
                            # pairs_to_merge.extend([(ref_match, ref_node)] + constraint_matches)
                            # todo - error-prone right now, it overmatches (ex: X -type-> living_thing and Y -type-> animal would merge)
                            pass
                        else:
                            # found resolution to reference; merge only one
                            resolution_options.append(ref_match)
                if len(resolution_options) > 0:
                    salient_resol = max(resolution_options,
                                        key=lambda x: wm.features.get(x, {}).get(SALIENCE, 0))
                    pairs_to_merge.extend([(salient_resol, ref_node)] + compatibilities[salient_resol])
            if len(pairs_to_merge) > 0:
                self.merge_references(pairs_to_merge, aux_state)
        return self.dialogue_intcore.working_memory

    @serialized('working_memory', 'aux_state')
    def run_fragment_resolution(self, working_memory, aux_state):
        self.load_working_memory(working_memory)
        wm = self.dialogue_intcore.working_memory

        salient_emora_truth_request = None
        salient_emora_arg_request = None
        salient_emora_request = None
        req_type = None
        #p.start('identify previous emora questions')
        # valid requests to be resolved through fragment resolution must have been requested on previous turn (currently approximated by salience threshold)
        emora_truth_requests = [pred for pred in wm.predicates('emora', REQ_TRUTH) if
                                not wm.has(pred[3], REQ_SAT)
                                and (pred[2].startswith(KB) or pred[2].startswith(WM))
                                and aux_state.get('turn_index', -1)-1 in wm.features.get(pred[3], {}).get(ETURN, [])]
        if len(emora_truth_requests) > 0:
            salient_emora_truth_request = max(emora_truth_requests,
                                              key=lambda pred: wm.features.get(pred[3], {}).get(SALIENCE, 0))
            truth_sal = wm.features.get(salient_emora_truth_request[3], {}).get(SALIENCE, 0)
        emora_arg_requests = [pred for pred in wm.predicates('emora', REQ_ARG) if
                              not wm.has(pred[3], REQ_SAT)
                              and (pred[2].startswith(KB) or pred[2].startswith(WM)) # hotfix to avoid incorrect request predicate setups where thing being requested is not a variable
                              and aux_state.get('turn_index', -1)-1 in wm.features.get(pred[3], {}).get(ETURN, [])]
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

        if DEBUG:
            print('ARG REQUESTS: %s' % emora_arg_requests)
            print('TRUTH REQUESTS: %s' % emora_truth_requests)

        if salient_emora_request is not None:
            #p.next('find answer')
            request_focus = salient_emora_request[2]
            current_user_concepts = {c for c in wm.concepts() if aux_state["turn_index"] in wm.features.get(c, {}).get(UTURN, [])}
            if req_type == REQ_TRUTH:  # special case - y/n question requires yes/no fragment as answer (or full resolution from earlier in pipeline)
                fragment_request_merges = self.truth_fragment_resolution(request_focus, current_user_concepts, wm, aux_state)
            else:
                fragment_request_merges = self.arg_fragment_resolution(request_focus, current_user_concepts, wm)
            if len(fragment_request_merges) > 0:
                # set salience of all request predicates to salience of fragment
                fragment = fragment_request_merges[0][0]  # first fragment merge must be the origin request even for truth fragments which may include additional arg merges too!
                ref_links = [e for e in wm.metagraph.out_edges(request_focus) if e[2] == REF and wm.has(predicate_id=e[1])]
                for so, t, l in ref_links:
                    wm.features.setdefault(t, {})[SALIENCE] = wm.features.setdefault(fragment, {}).get(SALIENCE, 0)
                    # wm.features[t][BASE] = True todo - check if the BASE indication matters here
            if DEBUG:
                print('CURRENT USER CONCEPTS: %s'%current_user_concepts)
                print('FRAGMENT REQUEST MERGES: %s'%fragment_request_merges)
            self.merge_references(fragment_request_merges, aux_state)
            self.dialogue_intcore.operate(self.dialogue_intcore.universal_operators, aux_state=aux_state)
            self.dialogue_intcore.operate(self.dialogue_intcore.wm_operators, aux_state=aux_state)
        #p.next('sal')
        self.dialogue_intcore.update_salience(iterations=SAL_ITER)
        #p.stop()
        return self.dialogue_intcore.working_memory, aux_state

    def init_template_nlg(self):
        from GRIDD.modules.responsegen_by_templates import ResponseTemplateFiller
        self.template_filler = ResponseTemplateFiller()

    @serialized('working_memory', 'expr_dict')
    def run_prepare_template_nlg(self, working_memory):
        self.load_working_memory(working_memory)
        self.dialogue_intcore.decay_salience()
        expr_dict = {}
        for s,t,o,i in self.dialogue_intcore.pull_expressions(): # expressions from KB
            if o not in expr_dict:
                if o == 'user':
                    expr_dict[o] = 'you'
                elif o == 'emora':
                    expr_dict[o] = 'I'
                else:
                    expr_dict[o] = s.replace('"', '')
        for s,t,o,i in self.dialogue_intcore.working_memory.predicates(predicate_type=EXPR): # expressions from WM
            if o not in expr_dict:
                expr_dict[o] = s.replace('"', '')
        return self.dialogue_intcore.working_memory, expr_dict

    @serialized('template_response_sel', 'aux_state')
    def run_template_fillers(self, inference_results, expr_dict, working_memory, aux_state):
        if inference_results is None:
            inference_results = {}
        template_response_sel = self.template_filler(inference_results, expr_dict, working_memory, aux_state, self.dialogue_intcore.fallbacks)
        return template_response_sel, aux_state

    def init_response_selection(self):
        from GRIDD.modules.response_selection_salience import ResponseSelectionSalience
        self.response_selection = ResponseSelectionSalience()

    @serialized('aux_state', 'response_predicates')
    def run_response_selection(self, working_memory, aux_state, template_response_sel):
        self.load_working_memory(working_memory)
        if template_response_sel is None:
            template_response_sel = (None,None,None)
        aux_state, response_predicates = self.response_selection(aux_state, self.dialogue_intcore.working_memory,
                                                                 template_response_sel)
        return aux_state, response_predicates

    def init_response_expansion(self):
        from GRIDD.modules.response_expansion import ResponseExpansion
        self.response_expansion = ResponseExpansion(self.dialogue_intcore.knowledge_base)

    @serialized('expanded_response_predicates', 'working_memory')
    def run_response_expansion(self, response_predicates, working_memory, aux_state):
        self.load_working_memory(working_memory)
        if response_predicates is None:
            response_predicates = []
        expanded_response_predicates, working_memory = self.response_expansion(response_predicates,
                                                               self.dialogue_intcore.working_memory, aux_state)
        return expanded_response_predicates, working_memory

    def init_response_by_rules(self):
        from GRIDD.modules.responsegen_by_rules import ResponseRules
        self.response_by_rules = ResponseRules()

    @serialized('rule_responses')
    def run_response_by_rules(self, aux_state, expanded_response_predicates):
        if expanded_response_predicates is None:
            expanded_response_predicates = []
        rule_responses = self.response_by_rules(aux_state, expanded_response_predicates)
        return rule_responses

    def init_response_nlg_model(self, model=None, device='cpu'):
        from GRIDD.modules.responsegen_by_model import ResponseGeneration
        self.response_nlg_model = ResponseGeneration(model, device)

    @serialized('nlg_responses')
    def run_response_nlg_model(self, expanded_response_predicates):
        if LOCAL:
            input_dict = {"expanded_response_predicates": expanded_response_predicates,
                          "conversationId": 'local'}
            response = requests.post('http://cobot-LoadB-1L3YPB9TGV71P-1610005595.us-east-1.elb.amazonaws.com',
                                     data=json.dumps(input_dict),
                                     headers={'content-type': 'application/json'},
                                     timeout=3.0)
            response = response.json()
            if 'context_manager' in response:
                nlg_responses = json.loads(response['context_manager']['nlg_responses'])
            else:
                nlg_responses = [None] * len(expanded_response_predicates)
        else:
            nlg_responses = self.response_nlg_model(expanded_response_predicates)
        return nlg_responses

    def init_response_assember(self):
        from GRIDD.modules.response_assembler import ResponseAssembler
        self.response_assembler = ResponseAssembler()

    @serialized('response', 'working_memory')
    def run_response_assembler(self, working_memory, aux_state, rule_responses):
        if rule_responses is None:
            rule_responses = [None]
        #p.start('response assembly')
        response = self.response_assembler(aux_state, rule_responses)
        self.load_working_memory(working_memory)
        #p.next('update sal')
        self.dialogue_intcore.update_salience(iterations=SAL_ITER)
        #p.next('decay sal')
        self.dialogue_intcore.decay_salience()
        #p.next('prune')
        self.dialogue_intcore.prune_predicates_of_type({AFFIRM, REJECT}, {})
        self.dialogue_intcore.prune_attended(aux_state, num_keep=PRUNE_THRESHOLD)
        #p.stop()
        return response, self.dialogue_intcore.working_memory

    ###################################################
    ## Helpers
    ###################################################

    def load_working_memory(self, working_memory):
        if working_memory is not None:
            self.dialogue_intcore.working_memory = working_memory
        else:
            self.dialogue_intcore.working_memory = ConceptGraph(namespace='wm', supports={AND_LINK: False})
            self.dialogue_intcore.consider(list(self.starting_wm.values()))

    def assign_cover(self, graph, concepts=None):
        if concepts is None:
            concepts = graph.concepts()
        for concept in concepts:
            if (not graph.has(predicate_id=concept) or graph.type(concept) not in PRIM) \
                    and not graph.has(concept, USER_AWARE) and not graph.has(concept, TYPE, 'span'):
                graph.add(concept, USER_AWARE)

    def _update_types(self, working_memory):
        types = self.dialogue_intcore.pull_types()
        for c, type_preds in types.items():
            for type in type_preds:
                if not working_memory.has(*type):
                    self.dialogue_intcore.consider([type], associations=c)

    def _convert_span_to_node_merges(self, span1, pos1, span2, pos2):
        (concept1,) = self.dialogue_intcore.working_memory.objects(span1, 'ref')
        concept1 = self._follow_path(concept1, pos1, self.dialogue_intcore.working_memory)
        (concept2,) = self.dialogue_intcore.working_memory.objects(span2, 'ref')
        concept2 = self._follow_path(concept2, pos2, self.dialogue_intcore.working_memory)
        return (concept1, concept2)

    def _follow_path(self, concept, pos, working_memory):
        if pos == 'subject':
            return working_memory.subject(concept)
        elif pos == 'object':
            return working_memory.object(concept)
        elif pos == 'type':
            return working_memory.type(concept)
        return concept

    def merge_references(self, reference_pairs, aux_state):
        wm = self.dialogue_intcore.working_memory
        for match_node, ref_node in reference_pairs:
            # identify user answers to emora requests and add req_sat monopredicate on request predicate
            if not wm.metagraph.out_edges(match_node, REF):
                truths = list(wm.predicates('emora', REQ_TRUTH, ref_node))
                if truths:
                    _process_answers(wm, truths[0][3])
                    wm.features.get(truths[0][3], {}).get(UTURN, []).append(aux_state["turn_index"])
                    if not wm.has(truths[0][3], USER_AWARE):
                        wm.add(truths[0][3], USER_AWARE)
                else:
                    args = list(wm.predicates('emora', REQ_ARG, ref_node))
                    if args:
                        _process_answers(wm, args[0][3])
                        wm.features.get(args[0][3], {}).get(UTURN, []).append(aux_state["turn_index"])
                        if not wm.has(args[0][3], USER_AWARE):
                            wm.add(args[0][3], USER_AWARE)
        self.dialogue_intcore.merge(reference_pairs)

    def arg_fragment_resolution(self, request_focus, current_user_concepts, wm):
        fragment_request_merges = []
        types = wm.types()
        request_focus_types = types[request_focus] - {request_focus}
        salient_concepts = sorted(current_user_concepts, key=lambda c: wm.features.get(c, {}).get(SALIENCE, 0),
                                  reverse=True)
        for c in salient_concepts:
            if c != request_focus and request_focus_types < (types[c]): # todo - should it be types[c] - {c}?
                subtype_set = current_user_concepts.intersection(wm.subtypes_of(c)) - {c}
                # if concept is a reference or if other salient concepts are its subtypes, dont treat current concept as answer fragment
                # also, concept and request focus must either both be predicates or both be entities
                if not subtype_set and not wm.metagraph.out_edges(c, REF) and \
                    ((wm.has(predicate_id=c) and wm.has(predicate_id=request_focus)) or
                     (not wm.has(predicate_id=c) and not wm.has(predicate_id=request_focus))):
                    fragment_request_merges.append((c, request_focus))
                    break
        return fragment_request_merges

    def truth_fragment_resolution(self, request_focus, current_user_concepts, wm, aux_state):
        fragment_request_merges = []
        indicator_preds = [p[3] for p in list(wm.predicates('user', AFFIRM)) + list(wm.predicates('user', REJECT))]
        options = set(indicator_preds).intersection(current_user_concepts)
        if len(indicator_preds) > 0: # find yes or no answer to question
            max_indicator = max(options, key=lambda p: wm.features.get(p[3], {}).get(SALIENCE, 0))
            fragment_request_merges.append((wm.object(max_indicator), request_focus))
        else: # maps `i do/nt` ~ do(user), `i have/nt` ~ have(user), and `i am/not` ~ am(user) to yes/no preds
            for c in current_user_concepts:
                if wm.has(predicate_id=c) and wm.type(c) in {'have', 'do', 'am'} and wm.object(c) is None:
                    if not wm.has(c, 'not'):
                        # yes
                        affirm_obj = wm.id_map().get()
                        i = wm.add('user', AFFIRM, affirm_obj)
                        if not wm.has(i, USER_AWARE):
                            wm.add(i, USER_AWARE)
                        wm.features[affirm_obj][SALIENCE] = 1.0
                        wm.features[affirm_obj][UTURN] = [aux_state.get("turn_index", -1)]
                        wm.features[i][SALIENCE] = 1.0
                        fragment_request_merges.append((affirm_obj, request_focus))
                    else:
                        # no
                        reject_obj = wm.id_map().get()
                        i = wm.add('user', REJECT, reject_obj)
                        if not wm.has(i, USER_AWARE):
                            wm.add(i, USER_AWARE)
                        wm.features[reject_obj][SALIENCE] = 1.0
                        wm.features[reject_obj][UTURN] = [aux_state.get("turn_index", -1)]
                        wm.features[i][SALIENCE] = 1.0
                        fragment_request_merges.append((reject_obj, request_focus))
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
                        wm.add(i, USER_AWARE)
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
        s = time.time()
        self.init_parse2logic(device=device)
        print('NLU load: %.2f'%(time.time()-s))
        self.init_multiword_matcher()
        self.init_template_nlg()
        self.init_response_selection()
        self.init_response_expansion()
        self.init_response_by_rules()
        self.init_response_nlg_model()
        self.init_response_assember()

    def run_mention_merge(self, user_utterance, working_memory, aux_state):
        aux_state = self.run_next_turn(aux_state)
        user_utterance = self.run_sentence_caser(user_utterance)
        elit_results = self.run_elit_models(user_utterance, aux_state)
        mentions, merges = self.run_parse2logic(elit_results)
        multiword_mentions = self.run_multiword_matcher(elit_results)
        ner_mentions = self.run_ner_mentions(elit_results)
        subspans, working_memory = self.run_mention_bridge(mentions, multiword_mentions, ner_mentions, working_memory, aux_state)
        working_memory = self.run_merge_bridge(merges, subspans, working_memory)
        return working_memory

    def respond(self, user_utterance, working_memory, aux_state):
        #p.start('next turn')
        aux_state = self.run_next_turn(aux_state)
        #p.next('sentence caser')
        user_utterance = self.run_sentence_caser(user_utterance)
        #p.next('elit')
        elit_results = self.run_elit_models(user_utterance, aux_state)
        #p.next('parse2logic')
        mentions, merges = self.run_parse2logic(elit_results)
        #p.next('multiword mentions')
        multiword_mentions = self.run_multiword_matcher(elit_results)
        #p.next('ner mentions')
        ner_mentions = self.run_ner_mentions(elit_results)
        #p.next('mention bridge')
        subspans, working_memory = self.run_mention_bridge(mentions, multiword_mentions, ner_mentions, working_memory, aux_state)
        #p.next('merge bridge')
        working_memory, aux_state = self.run_merge_bridge(merges, subspans, working_memory, aux_state)
        #p.next('knowledge pull')
        working_memory, aux_state = self.run_knowledge_pull(working_memory, aux_state)

        #p.next('reference id')
        rules = self.run_reference_identification(working_memory)
        #p.next('reference infer')
        inference_results, rules = self.run_dynamic_inference(rules, working_memory, aux_state)
        #p.next('reference resolution')
        working_memory = self.run_reference_resolution(inference_results, working_memory, aux_state)
        #p.next('fragment resolution')
        working_memory, aux_state = self.run_fragment_resolution(working_memory, aux_state)
        #p.next('dialogue infer')
        inference_results = self.run_dialogue_inference(working_memory, aux_state)
        #p.next('apply inferences')
        working_memory, aux_state = self.run_apply_dialogue_inferences(inference_results, working_memory, aux_state)

        #p.next('reference id 2')
        rules = self.run_reference_identification(working_memory)
        #p.next('reference infer 2')
        inference_results, rules = self.run_dynamic_inference(rules, working_memory, aux_state)
        #p.next('reference resolution 2')
        working_memory = self.run_reference_resolution(inference_results, working_memory, aux_state)
        #p.next('fragment resolution 2')
        working_memory, aux_state = self.run_fragment_resolution(working_memory, aux_state)
        #p.next('dialogue infer 2')
        inference_results = self.run_dialogue_inference(working_memory, aux_state)
        #p.next('apply inferences 2')
        working_memory, aux_state = self.run_apply_dialogue_inferences(inference_results, working_memory, aux_state)

        if PRINT_WM:
            print('\n<< Working Memory After Inferences Applied >>')
            print(working_memory.pretty_print(exclusions={SPAN_DEF, SPAN_REF, USER_AWARE, ASSERT, 'imp_trigger'}))

        #p.next('prepare template nlg')
        working_memory, expr_dict = self.run_prepare_template_nlg(working_memory)
        #p.next('template infer')
        inference_results = self.run_template_inference(working_memory, aux_state)
        #p.next('template fillers')
        template_response_sel, aux_state = self.run_template_fillers(inference_results, expr_dict,
                                                                     working_memory, aux_state)
        #p.next('response sel')
        aux_state, response_predicates = self.run_response_selection(working_memory, aux_state,
                                                                     template_response_sel)
        #p.next('response exp')
        expanded_response_predicates, working_memory = self.run_response_expansion(response_predicates,
                                                                                   working_memory, aux_state)
        #p.next('response rules')
        rule_responses = self.run_response_by_rules(aux_state, expanded_response_predicates)
        #p.next('response assembler')
        response, working_memory = self.run_response_assembler(working_memory, aux_state, rule_responses)
        #p.stop()
        #p.report()
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
        state_update = self.run_multiword_matcher(state)
        state.update(state_update)
        state_update = self.run_ner_mentions(state)
        state.update(state_update)
        state_update = self.run_mention_bridge(state)
        state.update(state_update)

        state_update = self.run_merge_bridge(state)
        state.update(state_update)
        state_update = self.run_knowledge_pull(state)
        state.update(state_update)

        state_update = self.run_reference_identification(state)
        state.update(state_update)
        state_update = self.run_dynamic_inference(state)
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
        state_update = self.run_dynamic_inference(state)
        state.update(state_update)
        state_update = self.run_reference_resolution(state)
        state.update(state_update)
        state_update = self.run_fragment_resolution(state)
        state.update(state_update)
        state_update = self.run_dialogue_inference(state)
        state.update(state_update)
        state_update = self.run_apply_dialogue_inferences(state)
        state.update(state_update)

        state_update = self.run_prepare_template_nlg(state)
        state.update(state_update)
        state_update = self.run_template_inference(state)
        state.update(state_update)
        state_update = self.run_template_fillers(state)
        state.update(state_update)
        state_update = self.run_response_selection(state)
        state.update(state_update)
        state_update = self.run_response_expansion(state)
        state.update(state_update)
        state_update = self.run_response_by_rules(state)
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
                # print('\tAux State: %s\n' % aux_state)
            utter = input('User: ')

    def run_static(self):
        wm = self.dialogue_intcore.working_memory.copy()
        aux_state = {'turn_index': -1}
        utters = [
            'hi',
            'sarah',
            'i bought a house',
            'thanks',
            'it has a big backyard which we wanted',
            'yeah',
            'a dog',
            'he is very energetic',
            'yeah',
            'he chewed my shoes',
            'yeah'
        ]
        for utter in utters:
            print(utter)
            if utter.strip() != '':
                s = time.time()
                if IS_SERIALIZING:
                    response, wm, aux_state = self.respond_serialize(utter, wm, aux_state)
                else:
                    response, wm, aux_state = self.respond(utter, wm, aux_state)
                elapsed = time.time() - s
                print('[%.2f s] %s\n' % (elapsed, response))
                # print('\tAux State: %s\n'%aux_state)

def get_filepaths():
    kb = [join('GRIDD', 'resources', 'kg_files', 'kb')]
    rules = [join('GRIDD', 'resources', 'kg_files', 'rules')]
    wm = [join('GRIDD', 'resources', 'kg_files', 'wm')]
    nlg_templates = [join('GRIDD', 'resources', 'kg_files', 'nlg_templates')]
    fallbacks = [join('GRIDD', 'resources', 'kg_files', 'fallbacks.kg')]
    return kb, rules, nlg_templates, fallbacks, wm

PRINT_WM = False

if __name__ == '__main__':
    import torch

    import sys
    try:
        f = open('GRIDD/scratch/input')
        if 'off' in f.readline():
            raise FileNotFoundError
        sys.stdin = f
    except FileNotFoundError:
        pass

    kb, rules, nlg_templates, fallbacks, wm = get_filepaths()

    device = input('device (cpu/cuda:0/cuda:1/...) >>> ').strip()
    print_wm = input('debug (n/y) >>> ').strip()
    # global PRINT_WM
    PRINT_WM = True if print_wm == 'y' else False
    if not device:
        if torch.cuda.is_available():
            device = 'cuda:0'
        else:
            device = 'cpu'
    chatbot = ChatbotServer(kb, rules, nlg_templates, fallbacks, wm, device=device)
    chatbot.full_init(device=device)
    chatbot.run()
