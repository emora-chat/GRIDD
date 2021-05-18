# ========================================================================
# Copyright 2021 Emory University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========================================================================
from types import SimpleNamespace
from typing import Any, Optional, Tuple, List, Iterable, Set

import ahocorasick


class SpanMatcher:
    def __init__(self, data: Optional[Iterable[str]] = None):
        """
        :param data: a collection of (span, value) pairs.
        """
        self._AC = ahocorasick.Automaton(ahocorasick.STORE_ANY)
        if data: self.addall(data)

    def addall(self, data: Iterable[str]):
        """
        Adds all (span, value) pairs in the data and finalizes this matcher.
        :param data: a collection of (span, value) pairs.
        """
        for span in data:
            if span in self._AC:
                t = self._AC.get(span)
            else:
                t = SimpleNamespace(span=span, values=set())
                self._AC.add_word(span, t)
            t.values.add("A")

        self._AC.make_automaton()

    def findall(self, tokens: List[str], remove_subset=True, remove_overlap=False) -> List[Tuple[str, int, int, Set[Any]]]:
        """
        :param tokens: a list of tokens.
        :param remove_subset: if True, remove spans that are subsets of other spans.
        :param remove_overlap: if True, remove subset spans (regardless of the value of remove_subset) and also overlapped spans.
        :return: a list of tuples where each tuple consists of
                 - span: str,
                 - start token index (inclusive): int
                 - end token index (exclusive): int
                 - a set of values for the span: Set[Any]
        """
        # find mappings between character offsets and token indices
        smap, emap, idx = dict(), dict(), 0
        for i, token in enumerate(tokens):
            smap[idx] = i
            idx += len(token)
            emap[idx] = i
            idx += 1

        # find matches
        text = ' '.join(tokens)
        spans = []
        for eidx, t in self._AC.iter(text):
            eidx += 1
            sidx = eidx - len(t.span)
           # sidx = smap.get(sidx, None)
            #eidx = emap.get(eidx, None)
            if sidx is None or eidx is None: continue
            spans.append((t.span, sidx, eidx+1, t.values))

        # remove subsets
        if remove_subset or remove_overlap:
            tmp = []
            for span0 in spans:
                remove = False
                for span1 in spans:
                    if span0 == span1: continue
                    if span0[1] >= span1[1] and span0[2] <= span1[2]:
                        remove = True
                        break
                if not remove: tmp.append(span0)
            spans = tmp

        # remove overlaps
        if remove_overlap:
            def sort_key(idx, oset):
                return len(oset), -(spans[idx][2] - spans[idx][1])

            overlaps = dict()
            for i0, span0 in enumerate(spans):
                s = set()
                for i1, span1 in enumerate(spans):
                    if i0 == i1: continue
                    if span1[1] < span0[1] < span1[2] or span1[1] < span0[2] < span1[2]: s.add(i1)
                if s: overlaps[i0] = s

            remove = set()
            while overlaps:
                k, v = max(overlaps.items(), key=lambda x: sort_key(x[0], x[1]))
                del overlaps[k]
                remove.add(k)
                for i in v:
                    s = overlaps[i]
                    s.remove(k)
                    if not s: del overlaps[i]
            if remove: spans = [span for i, span in enumerate(spans) if i not in remove]


        return spans


if __name__ == '__main__':
    data = ['South Korea',
            'South Korea',
            'United States',
            'States of',
            'of America',
            'United States of America',
            'Korea United',
            'the United States']

    text = 'I lived in South Korea but now live in the United States of America where South Korea United States .'
    tokens = text.split()

    sm = SpanMatcher(data)
    print('===================================')
    a = sm.findall(tokens, remove_subset=False, remove_overlap=False)
    for t in sm.findall(tokens, remove_subset=False, remove_overlap=False): print(t)
    print('===================================')
    for t in sm.findall(tokens, remove_subset=True, remove_overlap=False): print(t)
    print('===================================')
    for t in sm.findall(tokens, remove_subset=True, remove_overlap=True): print(t)

# I lived in South Korea but now live in the United States of America where South Korea United States.
#           1         2         3         4         5         6         7         8         9
# 0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
