
from structpy import specification


@specification
class PipelineSpec:
    """

    """

    @specification.init
    def PIPELINE(Pipeline, components, tags=None):
        """

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

        """
        assert pipeline(2, 3) == '# 5 -- hello #'

    def getitem(pipeline):
        """

        """
        subpipeline = pipeline['stage1', 'second_stage']
        assert subpipeline(2, 3) == ['hello', '5']

        assert pipeline['nlu'](2, 3) == ['hello', '5']
