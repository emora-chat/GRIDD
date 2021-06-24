from time import time
from GRIDD.intcore_server_globals import INFERENCE

# if INFERENCE:
    # import torch

class Profiler:

    def __init__(self):
        self._starts = []
        self._durations = []
        self._i = 0

    def start(self, label=None):
        self._starts.append((time(), label, self._i))
        self._i += 1

    def next(self, label=None):
        self.stop()
        self.start(label)

    def stop(self):
        start, label, order = self._starts.pop()
        if label is None:
            label = f'block {len(self._durations)}'
        # if INFERENCE:
            # torch.cuda.synchronize()
        self._durations.append((time() - start, label, len(self._starts), order))

    def end(self):
        while self._starts:
            self.stop()

    def report(self):
        print()
        for t, l, i, o in sorted(self._durations, key=lambda e: e[3]):
            print('  '*i + f'{t:.6f}: {l}')
        print()
        self._durations = []

profiler = Profiler()