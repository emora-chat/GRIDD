from stage import Stage

class Branch(Stage):
    """
    Parallel Module Execution
    """

    def __init__(self, name):
        self.models = {}
        self.type = 'Branch'
        self.name = name

    def add_model(self, meta):
        """
        :param meta: dict<'model': model object, 'weight': weight float, etc.>
        """
        model_name = meta['model'].name
        if model_name in self.models:
            raise Warning('WARNING: Name %s already exists in %s'%(model_name,self.type))
        self.models[model_name] = meta

    def add_models(self, metas):
        existing = [meta['model'].name for meta in metas if meta['model'].name in self.models]
        if len(existing) > 0:
            raise Warning('WARNING: Names %s already exist in %s' %(str(existing),self.type))
        for meta in metas:
            self.models[meta['model'].name] = meta

    def run(self, input):
        outputs = {model_name: meta['model'].run(input) for model_name, meta in self.models.items()}
        return outputs

    def to_display(self):
        return '{%s}'%' | '.join(self.model_names)