
import torch
from itertools import chain


class JaggedTensor:

    def __init__(self, data=None, device='cpu'):
        self.device = device
        self.indices = torch.tensor([], dtype=torch.long, device=device)    # indices: rows x max_row_length
        self.values = torch.tensor([], dtype=torch.long, device=device)     # values: values
        self.max_len = 0
        if data is not None:
            self.extend(data)

    def extend(self, data):
        i = len(self.values)
        values = list(chain(*data))
        nvals = torch.tensor(values, dtype=torch.long, device=self.device)
        self.values = torch.cat([self.values, nvals], 0)
        max_len = max([*[len(row) for row in data], self.max_len])
        indices = []
        for row in data:
            indices.append(list(range(i, i+len(row))) + [-1] * (max_len - len(row)))
            i = i + len(row)
        if max_len > self.max_len:
            diff = max_len - self.max_len
            pad = torch.full([self.indices.size()[0], diff], -1,
                             device=self.device, dtype=torch.long )
            self.indices = torch.cat([self.indices, pad], 1)
            self.max_len = max_len
        nidx = torch.tensor(indices, dtype=torch.long, device=self.device)
        self.indices = torch.cat([self.indices, nidx], 0)

    def __getitem__(self, indices):
        padded = self.indices[indices]
        linear = torch.flatten(padded)
        val_indices = linear[linear >= 0]
        return self.values[val_indices]

    def map(self, indices):
        padded = self.indices[indices]
        results = padded >= 0
        inverse = torch.nonzero(results)[:,0]
        val_indices = torch.flatten(padded[results])
        return self.values[val_indices], inverse

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
