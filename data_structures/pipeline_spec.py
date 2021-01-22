
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
    def PIPELINE(Pipeline, components, tags=None):
        """
        Construct a pipeline by tagging (or wrapping with a call) each callable
        component with `Pipeline.component`.

        Components are compsed together by defining what inputs and outputs they
        produce. Inputs and output _data_s are id'd by a string.

        _Data_s that are inputs to some component but not outputs are considered
        inputs to the pipeline as a whole.

        _Data_s that are outputs of some component but are not inputs are considered
        outputs of the pipeline as a whole.

        Components can be given _tags_, just as a way to organize them for creating
        subpipelines (see `.__getitem__` below).
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
            }
        )
        return pipeline

    def call(pipeline):
        """
        Make a call to invoke the entire pipeline.

        Enough args must be given to cover each _data_ that is not
        an output of some pipeline component. Args are matched to
        input _data_s in the order the _data_s were defined.
        """
        assert pipeline(2, 3) == '# 5 -- hello #'

    def getitem(pipeline):
        """
        Create a subpipeline. This filters out components in the
        pipeline. As long as the filtering process does not cause
        the pipeline to split into separate components, the resulting
        pipeline after filtering can be called like normal and is
        independent from the full, original pipeline.
        """
        subpipeline = pipeline['stage1', 'second_stage']
        assert subpipeline(2, 3) == ['hello', '5']

        assert pipeline['nlu'](2, 3) == ['hello', '5']
