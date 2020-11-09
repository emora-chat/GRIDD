from components.pipeline import Pipeline
from components.branch import Branch

class Framework(Pipeline):

    def __init__(self, name):
        super().__init__(name)
        self.type = "Framework"
        self.mention_models = Branch('mention models')
        self.merge_models = Branch('merge models')
        self.inference_models = Branch('inference models')
        self.selection_models = Branch('selection models')
        self.expansion_models = Branch('expansion models')
        self.generation_models = Branch('generation models')

    def add_mention_model(self, model):
        self.mention_models.add_model(model)

    def add_mention_models(self, models):
        self.mention_models.add_models(models)

    def add_mention_aggregation(self, aggregator_cls):
        self.mention_models = aggregator_cls('mention aggreg', self.mention_models)

    def add_merge_model(self, model):
        self.merge_models.add_model(model)

    def add_merge_models(self, models):
        self.merge_models.add_models(models)

    def add_merge_aggregation(self, aggregator_cls):
        self.merge_models = aggregator_cls('merge aggreg', self.merge_models)

    def add_inference_model(self, model):
        self.inference_models.add_model(model)

    def add_inference_models(self, models):
        self.inference_models.add_models(models)

    def add_inference_aggregation(self, aggregator_cls):
        self.inference_models = aggregator_cls('inference aggreg', self.inference_models)

    def add_selection_model(self, model):
        self.selection_models.add_model(model)

    def add_selection_models(self, models):
        self.selection_models.add_models(models)

    def add_selection_aggregation(self, aggregator_cls):
        self.selection_models = aggregator_cls('selection aggreg', self.selection_models)

    def add_expansion_model(self, model):
        self.expansion_models.add_model(model)

    def add_expansion_models(self, models):
        self.expansion_models.add_models(models)

    def add_expansion_aggregation(self, aggregator_cls):
        self.expansion_models = aggregator_cls('expansion aggreg', self.expansion_models)

    def add_generation_model(self, model):
        self.generation_models.add_model(model)

    def add_generation_models(self, models):
        self.generation_models.add_models(models)

    def add_generation_aggregation(self, aggregator_cls):
        self.generation_models = aggregator_cls('generation aggreg', self.generation_models)

    def build_framework(self):
        self.add_models([self.mention_models, self.merge_models, self.inference_models,
                         self.selection_models, self.expansion_models, self.generation_models])