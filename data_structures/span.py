
from GRIDD.data_structures.span_spec import SpanSpec
import re


class Span:

    def __init__(self, string, start, end, sentence, turn, speaker, expression):
        self.string = string
        self.expression = expression if expression not in ['#crd#', '#ord#'] else string
        self.start = int(start)
        self.end = int(end)
        self.sentence = int(sentence)
        self.turn = int(turn)
        self.speaker = speaker

    def __repr__(self):
        return str(self)

    def __str__(self):
        return '%s(%s,%s,%s,%s,%s)[%s]'%(self.string,str(self.start),str(self.end),
                                     str(self.sentence),str(self.turn),str(self.speaker),self.expression)

    def to_string(self):
        return '<span>'+str(self)

    @classmethod
    def from_string(cls, string):
        return Span(*re.match(r'<span>([^(]*)\(([0-9]+), ?([0-9])+, ?([0-9]+), ?([0-9])+, ?([0-9])+\)\[([^]]*)\]', string).groups())


if __name__ == '__main__':
    print(SpanSpec.verify(Span))



# def build_span_data_dict(string, start, end, sentence=None, turn=None, speaker=None):
#     d = {
#         'string': string,
#         'start': start,
#         'end': end
#     }
#     if sentence:
#         d['sentence'] = sentence
#     if turn:
#         d['turn'] = turn
#     if speaker:
#         d['speaker'] = speaker
#     return d