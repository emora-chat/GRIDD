
from data_structures.span_spec import SpanSpec


class Span:

    def __init__(self, string, start, end):
        self.string = string
        self.start = start
        self.end = end

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '%s(%d,%d)'%(self.string, self.start, self.end)


if __name__ == '__main__':
    print(SpanSpec.verify(Span))