
import torch
from itertools import chain

from GRIDD.utilities.profiler import profiler as p


class JaggedTensor:

    def __init__(self, data=None, device='cpu'):
        self.device = device
        self.values = None    # indices: rows x max_row_length
        self.max_len = 0
        if data is not None:
            self.extend(data)

    def extend(self, data):
        p.start('length calc')
        lengths = torch.tensor([len(row) for row in data], dtype=torch.long, device=self.device)
        maxlen = torch.max(lengths).item()
        p.next('create rows')
        row_data = list(chain(*[[(value, i, j) for j, value in enumerate(row)] for i, row in enumerate(data)]))
        row_data = torch.tensor(row_data, dtype=torch.long, device=self.device)
        vals, i, j = row_data[:,0], row_data[:,1], row_data[:,2]
        p.next('setup')
        values = torch.full((len(data), maxlen), -1, dtype=torch.long, device=self.device)
        p.next('insertion')
        values[i, j] = vals
        p.next('concat and finish')
        if self.values is None:
            self.values = values
            self.max_len = maxlen
        else:
            if maxlen > self.max_len:
                self.max_len = maxlen
                small = self.values
                large = values
                new_is_larger = True
            else:
                small = values
                large = self.values
                new_is_larger = False
            diff = large.size()[1] - small.size()[1]
            pad = torch.full((small.size()[0], diff), -1, dtype=torch.long, device=self.device)
            small = torch.cat([small, pad], 1)
            self.values = torch.cat([small, large] if new_is_larger else [large, small], 0)
        p.stop()

    def __getitem__(self, indices):
        padded = self.values[indices]
        linear = torch.flatten(padded)
        values = linear[linear >= 0]
        return values

    def map(self, indices):
        padded = self.values[indices]
        linear = torch.flatten(padded)
        is_value = linear >= 0
        values = linear[is_value]
        inverse = torch.floor_divide(torch.nonzero(is_value).squeeze(1), self.max_len)
        return values, inverse

if __name__ == '__main__':
    t = JaggedTensor([
        [4, 2, 5, 6],
        [1, 3],
        [3, 2, 9]
    ])

    v = t[[2, 2, 0]]
    print(v)

    k = torch.tensor([2, 2, 0, 1], dtype=torch.long)
    v, i = t.map(k)
    print(v.long())
    print(i)
    print(k[i])
    print(torch.cat([k[i].unsqueeze(1), v.unsqueeze(1)], 1))
