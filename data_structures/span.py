
from GRIDD.data_structures.span_spec import SpanSpec
import re


class Span:

    def __init__(self, string, start, end, sentence=None, turn=None, speaker=None):
        self.string = string
        self.start = start
        self.end = end
        self.sentence = sentence
        self.turn = turn
        self.speaker = speaker

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '%s(%s,%s)'%(self.string, str(self.start), str(self.end))

    def to_string(self):
        return '<span>'+str(self)

    @classmethod
    def from_string(cls, string):
        return Span(*re.match(r'<span>([^(]*)\(([0-9]+), ?([0-9])+\)', string).groups())


if __name__ == '__main__':
    print(SpanSpec.verify(Span))