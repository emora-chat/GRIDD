import json
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.span import Span

##############################
# Serialization functions
##############################

class DataEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Span):
            return obj.to_string()
        elif isinstance(obj, ConceptGraph):
            return obj.save()
        return json.JSONEncoder.default(self, object)

def save(key, object):
    if key == 'aux_state':
        coref_context = object.get('coref_context', None)
        if coref_context is not None:
            global_tokens = coref_context.get('global_tokens', [])
            global_tokens = [span.to_string() for span in global_tokens]
            coref_context['global_tokens'] = global_tokens
            object['coref_context'] = coref_context if len(coref_context) > 0 else None
    elif key == 'mentions':
        new_d = {}
        for span,cg in object.items():
            new_d[span] = cg.save()
        object = new_d
    elif key == 'inference_results':
        for rule, info in object.items():
            if len(info) == 3:
                pre, post, match_dict = info
                pre_json = pre.save()
                if isinstance(post, ConceptGraph):
                    post_json = post.save()
                else:
                    post_json = post
                object[rule] = (pre_json, post_json, match_dict)
            else:
                pre, match_dict = info
                pre_json = pre.save()
                object[rule] = (pre_json, match_dict)
    elif key == 'rules':
        for rule, (pre, vars) in object.items():
            pre_json = pre.save()
            vars_json = list(vars)
            object[rule] = (pre_json, vars_json)
    object = json.dumps(object, cls=DataEncoder)
    return object

def load(key, value):
    if value is not None:
        try:
            value = json.loads(value) if isinstance(value, str) else value
        except json.JSONDecodeError as e:
            print('ERROR:', e)
            value = value
        if key == 'working_memory':
            working_memory = ConceptGraph(namespace=value["namespace"])
            ConceptGraph.load(working_memory, value)
            value = working_memory
        elif key == 'aux_state':
            coref_context = value.get('coref_context', None)
            if coref_context is not None:
                global_tokens = coref_context.get('global_tokens', [])
                global_tokens = [Span.from_string(span) for span in global_tokens]
                coref_context['global_tokens'] = global_tokens
                value['coref_context'] = coref_context if len(coref_context) > 0 else None
        elif key == 'elit_results':
            if 'tok' in value:
                value['tok'] = [Span.from_string(t) for t in value['tok']]
        elif key == 'mentions':
            new_d = {}
            for span_str, cg_dict in value.items():
                cg = ConceptGraph(namespace=cg_dict["namespace"])
                cg.id_map().index = cg_dict["next_id"]
                cg.load(cg_dict)
                new_d[span_str] = cg
            value = new_d
        elif key == 'inference_results':
            print('Value:', value)
            for rule, info in value.items():
                if len(info) == 3:
                    pre_json, post_json, match_dict = info
                    pre = ConceptGraph(namespace=pre_json["namespace"])
                    pre.load(pre_json)
                    if isinstance(post_json, dict):
                        post = ConceptGraph(namespace=post_json["namespace"])
                        post.load(post_json)
                    else:
                        post = post_json
                    value[rule] = (pre, post, match_dict)
                else:
                    pre_json, match_dict = info
                    pre = ConceptGraph(namespace=pre_json["namespace"])
                    pre.load(pre_json)
                    value[rule] = (pre, match_dict)
        elif key == 'rules':
            for rule, (pre_json, vars_json) in value.items():
                pre = ConceptGraph(namespace=pre_json["namespace"])
                pre.load(pre_json)
                vars_json = set(vars_json)
                value[rule] = (pre, vars_json)
    return value
