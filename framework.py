from stage import Stage
from pipeline import Pipeline
from branch import Branch

class Framework(Stage):
    """
    Container Class for Pipelines and Branches
    """

    def __init__(self, name):
        self.type = 'Framework'
        super().__init__(name)