
from GRIDD.data_structures.span_spec import SpanSpec
import re


class Span:

    def __init__(self, string, start, end):
        self.string = string
        self.start = start
        self.end = end

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '%s(%d,%d)'%(self.string, self.start, self.end)

    def to_string(self):
        return '<span>'+str(self)

    @classmethod
    def from_string(cls, string):
        return Span(*re.match(r'<span>([^(]*)\(([0-9]+), ?([0-9])+\)', string).groups())


if __name__ == '__main__':
    print(SpanSpec.verify(Span))