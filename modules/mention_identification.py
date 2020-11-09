from modules.module import Module

class BaseMentionIdentification(Module):

    def __init__(self, name):
        super().__init__(name)

    def run(self, input):
        return input + ' ' + 'mention'