from abc import ABC, abstractmethod

class Stage(ABC):



    @abstractmethod
    def run(self, input):
        pass

    @abstractmethod
    def to_display(self):
        pass