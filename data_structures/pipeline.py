
from data_structures.pipeline_spec import PipelineSpec

from structpy.graph.directed.labeled.data.multilabeled_digraph_data import MultiLabeledDigraphDataNX as Graph
from utilities import identification_string

class Pipeline:

    class component:

        def __init__(self, fn):
            self.fn = fn
            self.tags = set()
            self.transitions = []

        def __call__(self, *args, **kwargs):
            return self.fn(*args, **kwargs)

        def __lt__(self, other):
            if isinstance(other, Pipeline.component):
                self.transitions = other.transitions + self.transitions + [(other, self)]
                self.tags = other.tags | self.tags
                return self
            elif isinstance(other, tuple):
                self.transitions.append((other, self))
                return self
            else:
                other = (other,)
                self.transitions.append((other, self))
                return self

        def __gt__(self, other):
            if isinstance(other, Pipeline.component):
                return NotImplemented
            elif isinstance(other, tuple):
                self.transitions.append((self, other))
                return self
            else:
                other = (other,)
                self.transitions.append((self, other))
                return self

        def __str__(self):
            if hasattr(self.fn, __name__):
                name = {self.fn.__name__}
            else:
                name = {type(self.fn).__name__}
            return 'Comp<{}>'.format(name)

        def __repr__(self):
            return str(self)

    def __init__(self, *components, tags=None):
        self._graph = Graph()
        self._stages = set()
        self._datas = set()
        self._order = {}
        next_id = 0
        anon_outs = {}
        for component in components:
            for source, target in component.transitions:
                if isinstance(source, Pipeline.component) and isinstance(target, Pipeline.component):
                    self._order[source] = len(self._order)
                    if source in anon_outs:
                        output = anon_outs[source]
                    else:
                        output = '__data__{}'.format(identification_string(next_id))
                        anon_outs[source] = output
                        next_id += 1
                    if output not in self._order: self._order[output] = len(self._order)
                    if target not in self._order: self._order[target] = len(self._order)
                    self._datas.add(output)
                    self._graph.add(source, output, 0)
                    self._graph.add(target)
                    self._graph.add(output, target, len(self._graph.in_edges(target)))
                    self._stages.add(source)
                    self._stages.add(target)
                elif isinstance(source, Pipeline.component) and isinstance(target, tuple):
                    for i, result in enumerate(target):
                        self._graph.add(source, result, i)
                        if source not in self._order: self._order[source] = len(self._order)
                        if result not in self._order: self._order[result] = len(self._order)
                        self._datas.add(result)
                    self._stages.add(source)
                elif isinstance(source, tuple) and isinstance(target, Pipeline.component):
                    for arg in source:
                        self._graph.add(target)
                        self._graph.add(arg, target, len(self._graph.in_edges(target)))
                        if arg not in self._order: self._order[arg] = len(self._order)
                        self._datas.add(arg)
                    if target not in self._order: self._order[target] = len(self._order)
                    self._stages.add(target)
        self._tags = {} if tags is None else \
            {k: (set(v) if hasattr(v, '__iter__') else {v}) for k, v in tags.items()}
        for stage in self._stages:
            if stage in self._tags:
                if hasattr(stage.fn, __name__):
                    self._tags[stage].add(stage.fn.__name__)
                else:
                    self._tags[stage].add(type(stage.fn).__name__)
            else:
                if hasattr(stage.fn, __name__):
                    self._tags[stage] = {stage.fn.__name__}
                else:
                    self._tags[stage] = {type(stage.fn).__name__}

    def __call__(self, *args, **kwargs):
        inputs = {n for n in self._graph.nodes() if len(self._graph.in_edges(n)) == 0}
        outputs = {n for n in self._graph.nodes() if len(self._graph.out_edges(n)) == 0}
        inputs = sorted(inputs, key=self._order.__getitem__)
        outputs = sorted(outputs, key=self._order.__getitem__)
        stages = sorted(self._stages, key=self._order.__getitem__)
        datas = {}
        invalidated = set(stages)

        for i, arg in enumerate(args):
            datas[inputs[i]] = arg
        for kw, arg in kwargs.items():
            datas[kw] = arg

        while invalidated:
            for stage in stages:
                arg_ids = [x[0] for x in sorted(self._graph.in_edges(stage), key=lambda y: y[2])]
                if stage not in invalidated:
                    continue
                args = [datas[arg_id] for arg_id in arg_ids]
                result = stage(*args)   # STAGE CALL
                if len(self._graph.out_edges(stage)) == 1:
                    ((s, t, l),) = self._graph.out_edges(stage)
                    datas[t] = result
                else:
                    outs = sorted(self._graph.out_edges(stage), key=lambda x: x[2])
                    for (s, t, l) in outs:
                        datas[t] = result[l]
                for s, t, l in self._graph.out_edges(stage):
                    for s, t, l in self._graph.out_edges(t):
                        invalidated.add(t)
                invalidated.remove(stage)

        return [datas[o] for o in outputs] if len(outputs) > 1 else datas[outputs[0]]

    def __getitem__(self, item):
        subpipeline = self.copy()
        if not isinstance(item, str):
            tags = set(item)
        else:
            tags = {item}
        for stage in subpipeline._stages:
            if not subpipeline._tags[stage] & tags:
                subpipeline._graph.remove(stage)
        for data in subpipeline._datas:
            if len(subpipeline._graph.neighbors(data)) == 0:
                subpipeline._graph.remove(data)
        nodes = set(subpipeline._graph.nodes())
        subpipeline._stages &= nodes
        subpipeline._datas &= nodes
        return subpipeline

    def copy(self):
        cp = Pipeline()
        cp._graph = Graph(edges=self._graph.edges())
        cp._tags = dict(self._tags)
        cp._stages = set(self._stages)
        cp._datas = set(self._datas)
        cp._order = dict(self._order)
        return cp


if __name__ == '__main__':
    print(PipelineSpec.verify(Pipeline))