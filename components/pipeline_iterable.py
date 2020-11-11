from components.pipeline import Pipeline

class IterablePipeline(Pipeline):

    def __init__(self, name, iteration_function):
        super().__init__(name)
        self.type = 'Iterable Pipeline'
        self.iteration_func = iteration_function
        self.iteration_vars = {}

    def add_iteration_function(self, iteration_function):
        self.iteration_func = iteration_function

    def run(self, input, graph):
        self.iteration_vars = {}
        while self.iteration_func(self, input):
            for model in self.models:
                input = model.run(input, graph)
        return input