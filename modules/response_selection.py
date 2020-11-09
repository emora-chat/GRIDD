from modules.module import Module

class BaseResponseSelection(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input):
        return input + ' ' + 'generation'