
import torch
from itertools import chain


class JaggedTensor:

    def __init__(self, data=None, device='cpu'):
        self.device = device
        self.indices = torch.LongTensor(device=device)
        self.values = torch.Tensor(device=device)

    def extend(self, data):
        indices = []
        i = len(self.indices)
        for ls in data:
            j = i + len(ls)
            indices.append([i, j])
        self.indices = torch.cat([self.indices, torch.Tensor(indices)], 0)
        values = list(chain(*data))
        self.values = torch.cat([self.values, torch.Tensor(values)], 0)

    def __getitem__(self, item):
        if isinstance(item, int):
            indices = self.indices[item]
            return self.values[indices[0]:indices[1]]
        elif isinstance(item, slice):
            indices = self.indices[item]
            # expand indices into full index list



        else:
            pass

    def map(self, keys, indices):
        pass # concatenate


def index_range_select(values, indices):
    all_indices = torch.arange(0, values.size()[0])



if __name__ == '__main__':
    t = JaggedTensor([
        [4, 2, 5, 6],
        [1, 3],
        [3, 2, 9]
    ])
