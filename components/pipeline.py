
class Pipeline:
    """
    Sequential Module Execution
    """

    def __init__(self, name, iteration_function=None):
        self.model_names = []
        self.models = []
        self.type = 'Pipeline'
        self.name = name
        self.iteration_func = iteration_function
        self.iteration_vars = {}

    def add_iteration_function(self, iteration_function):
        self.iteration_func = iteration_function

    def add_model(self, model):
        if model.name in self.model_names:
            raise Warning('WARNING: Name %s already exists in %s'%(model.name,self.type))
        self.model_names.append(model.name)
        self.models.append(model)

    def add_models(self, models):
        existing = [model.name for model in models if model.name in self.model_names]
        if len(existing) > 0:
            raise Warning('WARNING: Names %s already exist in %s' %(str(existing),self.type))
        self.model_names.extend([model.name for model in models])
        self.models.extend(models)

    def insert_model_by_position(self, model, position):
        self.model_names.insert(position, model.name)
        self.models.insert(position, model)

    def insert_model_after(self, source_name, target_model):
        source_idx = self.model_names.index(source_name)
        if source_idx == -1:
            raise Exception('No model named %s exists in Pipeline'%source_name)
        insertion_idx = source_idx+1
        self.model_names.insert(insertion_idx, target_model.name)
        self.models.insert(insertion_idx, target_model)

    def run(self, input):
        self.iteration_vars = {}
        if self.iteration_func is not None:
            while self.iteration_func(self, input):
                for model in self.models:
                    input = model.run(input)
        else:
            for model in self.models:
                input = model.run(input)
        return input

    def to_display(self):
        # todo - build name recursively over all atomic models
        return '%s(%s)'%(self.name, ' -> '.join(self.model_names))
