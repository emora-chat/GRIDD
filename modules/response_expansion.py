from modules.module import Module

class BaseResponseExpansion(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input, graph):
        return input + ' ' + 'expansion'