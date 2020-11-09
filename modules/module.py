from abc import ABC, abstractmethod

class Module(ABC):

    def __init__(self, name):
        self.name = name
        super().__init__()

    @abstractmethod
    def run(self, input):
        pass