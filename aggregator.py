from abc import ABC, abstractmethod

class Aggregator(ABC):
    """
    Aggregation of Branch outputs
    """

    def __init__(self, name, branch):
        self.type = 'Aggregator'
        self.name = name
        self.branch = branch

    @abstractmethod
    def run(self, input):
        """
        Runs the branch and aggregates the outputs
            outputs = self.branch.run(input)
            return <aggregation of outputs>
        :param input:
        :return:
        """
        pass

    def to_display(self):
        return '%s -> %s'%(self.branch.to_display(), self.aggregator.name)