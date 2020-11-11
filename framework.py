from components.pipeline import Pipeline
from components.pipeline_iterable import IterablePipeline
from components.branch import Branch

class Framework(Pipeline):

    def __init__(self, name):
        super().__init__(name)
        self.type = "Framework"

        self.mention_models = Branch('mention models')
        self.mention_bridge = None

        self.merge_models = Branch('merge models')
        self.merge_bridge = None
        self.merge_iteration = None

        self.inference_models = Branch('inference models')
        self.inference_bridge = None
        self.merge_inference_iteration = None

        self.selection_model = None
        self.expansion_model = None
        self.generation_model = None


    def add_mention_model(self, model_dict):
        self.mention_models.add_model(model_dict)

    def add_mention_models(self, models):
        self.mention_models.add_models(models)

    def add_mention_aggregation(self, aggregator_cls):
        self.mention_models = aggregator_cls('mention aggreg', self.mention_models)

    def add_merge_model(self, model_dict):
        self.merge_models.add_model(model_dict)

    def add_merge_models(self, models):
        self.merge_models.add_models(models)

    def add_merge_aggregation(self, aggregator_cls):
        self.merge_models = aggregator_cls('merge aggreg', self.merge_models)

    def add_merge_iteration(self, iter_func):
        self.merge_iteration = iter_func

    def add_inference_model(self, model_dict):
        self.inference_models.add_model(model_dict)

    def add_inference_models(self, models):
        self.inference_models.add_models(models)

    def add_inference_aggregation(self, aggregator_cls):
        self.inference_models = aggregator_cls('inference aggreg', self.inference_models)

    def add_merge_inference_iteration(self, iter_func):
        self.merge_inference_iteration = iter_func

    def add_selection_model(self, model_dict):
        self.selection_model = model_dict['model']

    def add_expansion_model(self, model_dict):
        self.expansion_model = model_dict['model']

    def add_generation_model(self, model_dict):
        self.generation_model = model_dict['model']

    def add_mention_bridge(self, mention_bridge_model):
        self.mention_bridge = mention_bridge_model

    def add_merge_bridge(self, merge_bridge_model):
        self.merge_bridge = merge_bridge_model

    def add_inference_bridge(self, inference_bridge_model):
        self.inference_bridge = inference_bridge_model

    def build_framework(self):
        merge_pipeline = IterablePipeline('merge pipeline', self.merge_iteration)
        merge_pipeline.add_models([self.merge_models, self.merge_bridge])
        merge_and_infer_pipeline = IterablePipeline('merge and infer pipeline', self.merge_inference_iteration)
        merge_and_infer_pipeline.add_models([merge_pipeline, self.inference_models, self.inference_bridge])
        self.add_models([self.mention_models, self.mention_bridge,
                         merge_and_infer_pipeline,
                         self.selection_model,
                         self.expansion_model,
                         self.generation_model])