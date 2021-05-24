
from structpy import specification


@specification
class PipelineSpec:
    """
    Data structure to organize complex modular pipelines.

    Pipeline is a directed acyclic graph (DAG) of _components_ and _datas_,
    where each component is a function with one or more inputs and one or
    more outputs and each data defines a container for storing those inputs
    and outputs.
    """

    @specification.init
    def PIPELINE(Pipeline, components, tags=None, inputs=None, outputs=None):
        """
        Construct a pipeline by tagging (or wrapping with a call) each callable
        component with `Pipeline.component`.

        Components are compsed together by defining what inputs and outputs they
        produce. Inputs and output _data_s are id'd by a string.

        _Data_s that are inputs to some component but not outputs are considered
        inputs to the pipeline as a whole by default.

        _Data_s that are outputs of some component but are not inputs are considered
        outputs of the pipeline as a whole by default.

        Components can be given _tags_, just as a way to organize them for creating
        subpipelines (see `.__getitem__` below).

        Specifying `inputs` and/or `outputs` explicitly by passing in a `list` of `str`
        will force the pipeline to expect the provided inputs in order of appearance
        and/or output the specified results in order.
        """

        @Pipeline.component
        def first_stage(x, y):
            return x + y, 'hello'

        @Pipeline.component
        def second_stage(z):
            return str(z)

        @Pipeline.component
        def third_stage(i, h):
            return i + ' -- ' + h

        @Pipeline.component
        def fourth_stage(f):
            return '# %s #' % f

        pipeline = Pipeline(
            ('x', 'y') > first_stage > ('z', 'h'),
            ('z') > second_stage > ('i'),
            ('i', 'h') > third_stage > fourth_stage > ('r'),
            tags={
                first_stage: ['stage1', 'nlu'],
                second_stage: ['nlu'],
                fourth_stage: ['final']
            },
            outputs=['r', 'h']
        )
        return pipeline

    def call(pipeline):
        """
        Make a call to invoke the entire pipeline.

        Enough args must be given to cover each _data_ that is not
        an output of some pipeline component. Args are matched to
        input _data_s in the order the _data_s were defined.
        """
        result = pipeline(2, 3)
        assert result == ('# 5 -- hello #', 'hello')

    def sub(pipeline, tags_or_stages, inputs=None, outputs=None):
        """
        Create a subpipeline. This filters out components in the
        pipeline. As long as the filtering process does not cause
        the pipeline to split into separate components, the resulting
        pipeline after filtering can be called like normal and is
        independent from the full, original pipeline.
        """
        subpipeline = pipeline.sub('stage1', 'second_stage')
        result = subpipeline(2, 3)
        assert result == ('hello', '5')
