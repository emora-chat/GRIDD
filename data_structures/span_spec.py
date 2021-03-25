
from structpy import specification


@specification
class SpanSpec:
    """
    Span gives the string data, and start (inclusive) and end (exclusive)
    token indices of the span within its larger text.

    Span also requires turn and sentence indices, as well as speaker id.
    Sentence indices are global.
    """

    @specification.init
    def SPAN(Span):
        full_string = 'I love my dog Fido'
        return Span('my dog', 2, 4, 0, 0, 1, 'my dog')


