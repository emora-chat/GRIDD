from abc import ABC, abstractmethod

class Module(ABC):

    def __init__(self, name):
        self.name = name
        self.framework = None
        super().__init__()

    @abstractmethod
    def run(self, input, graph):
        pass