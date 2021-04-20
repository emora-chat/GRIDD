from GRIDD.modules.responsegen_by_templates_spec import ResponseTemplatesSpec

class ResponseTemplates:

    def __call__(self, match_dict, string_spec_ls, wm):
        expr_dict = {}
        for s, t, o, i in wm.predicates(predicate_type='expr'):
            if o not in expr_dict:
                expr_dict[o] = s.replace('"', '')
        s = self.fill_string(match_dict, expr_dict, string_spec_ls)
        return s

    def fill_string(self, match_dict, expr_dict, string_spec_ls):
        fillers = {}
        for e in string_spec_ls:
            if not isinstance(e, tuple) and e not in fillers and e.isupper():
                fillers[e] = expr_dict[match_dict[e]]

        for e in string_spec_ls:
            if isinstance(e, tuple) and str(e) not in fillers:
                surface_form, spec = e
                if 't' in spec:
                    surface_form += '.' + spec['t']
                if 'p' in spec:
                    surface_form += '.' + spec['p']
                if 'f' in spec:
                    surface_form += '.' + spec['f']
                if 's' in spec:
                    surface_form += '.' + fillers.get(spec['s'], spec['s'])
                if 'o' in spec:
                    surface_form += '.' + fillers.get(spec['o'], spec['o'])
                fillers[str(e)] = surface_form

        final_str = [fillers.get(str(e), str(e)) for e in string_spec_ls]
        return ' '.join(final_str)



"""
spec = re.match(r"(.*)\([tpfso]=.*\)", e)
if spec:
    surface_form = spec.groups()[0]
    fillers[e] = surface_form
    t = re.match(r"t=([^,)]*)", e)
    if t:
        t = t.groups()[0]
        fillers[e] += '.' + t
    p = re.match(r"p=([^,)]*)", e)
    if p:
        p = p.groups()[0]
    f = re.match(r"f=([^,)]*)", e)
    if f:
        f = f.groups()[0]
    s = re.match(r"s=([^,)]*)", e)
    if s:
        s = s.groups()[0]
    o = re.match(r"o=([^,)]*)", e)
    if o:
        o = o.groups()[0]
"""





if __name__ == '__main__':
    print(ResponseTemplatesSpec.verify(ResponseTemplates))