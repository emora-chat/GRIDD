
import torch
from itertools import chain


class JaggedTensor:

    def __init__(self, data=None, device='cpu'):
        self.device = device
        self.indices = torch.LongTensor(device=device)  # indices: rows x max_row_length
        self.values = torch.Tensor(device=device)       # values: values
        self.max_len = 0
        if data is not None:
            self.extend(data)

    def extend(self, data):
        i = len(self.values)
        values = list(chain(*data))
        self.values = torch.cat([self.values, torch.Tensor(values)], 0)
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
        self.indices = torch.cat([self.indices, torch.LongTensor(indices)], 0)

    def __getitem__(self, indices):
        padded = self.indices[indices]
        linear = torch.flatten(padded)
        val_indices = linear[linear >= 0]
        return self.values[val_indices]

if __name__ == '__main__':
    t = JaggedTensor([
        [4, 2, 5, 6],
        [1, 3],
        [3, 2, 9]
    ])

    v = t[[2, 2, 0]]
    print(v)
