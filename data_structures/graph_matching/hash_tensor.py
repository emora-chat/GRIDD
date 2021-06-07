
import torch
from GRIDD.data_structures.graph_matching.primes import prime


class HashTensor:
    """
    Create a hash map to concurrently access integer -> integer
    values. Keys must be >= 0.
    """

    def __init__(self, mapping, device='cpu'):
        self.keys = torch.tensor([], dtype=torch.long, device=device)
        self.values = torch.tensor([], dtype=torch.long, device=device)
        self.device = device
        self.update(mapping)

    def update(self, mapping):
        if self.keys is not None:
            mapping.update(self.keys)
        tablesize = prime(len(mapping) * 2) or len(mapping) * 2
        self.keys = torch.full((tablesize,), -1, dtype=torch.long, device=self.device)
        self.values = torch.full((tablesize,), -1, dtype=torch.long, device=self.device)
        items = torch.tensor(list(mapping.items()), dtype=torch.long, device=self.device)
        keys, values = items[:,0], items[:,1]
        for i in range(len(keys)):
            index = self.insertion_index(keys[i].unsqueeze(0))
            self.keys[index] = keys[i]
            self.values[index] = values[i]

    def index(self, key):
        """
        Take keys as input and output the table index of those keys,
        or -1 if the key is not in the table at all.
        """
        result = torch.full(key.size(), -1,                 # Tensor<key: index> mapping of keys to table indices (or -1 if no entry)
                            device=self.device)
        search = key % len(self.keys)                       # Tensor<remaining: index> mapping remaining keys to table indices
        ri = torch.arange(0, len(key),                      # Tensor<remaining: rindex> mapping remaining keys to original key indices
                          dtype=torch.long, device=self.device)
        while len(search) > 0:                              # while there are undecided keys (neither found nor lost)
            tkeys = self.keys[search]                       # Tensor<remaining: tablekey> keys in table corresponding with searched keys
            cmp = tkeys == key[ri]                          # Tensor<remaining: bool> whether there is a match, tablekey==key
            found = torch.nonzero(cmp)                      # Tensor<remaining_after_search: rindex_into_search> subset of search that is found
            ki = ri[found]                                  # Tensor<found: keyindex> indices of found keys in original key tensor
            result[ki] = search[found]                      # inserting table indices into result
            searching = torch.logical_and(~cmp, tkeys!=-1)  # Tensor<remaining: bool> whether still searching for key (neither lost nor found)
            search = search[searching]                      # filtering search by keys still searching for
            ri = ri[searching]                              # filtering rindex to match search
            search = (search + 1) % len(self.keys)          # updating search with linear probe
        return result

    def insertion_index(self, key):
        result = torch.full(key.size(), -1,                 # Tensor<key: index> mapping of keys to empty table indices
                            device=self.device)
        search = key % len(self.keys)                       # Tensor<remaining: index> mapping remaining keys to table indices
        ri = torch.arange(0, len(key),                      # Tensor<remaining: rindex> mapping remaining keys to original key indices
                          dtype=torch.long, device=self.device)
        while len(search) > 0:                              # while there are undecided keys (neither found nor lost)
            tkeys = self.keys[search]                       # Tensor<remaining: tablekey> keys in table corresponding with searched keys
            cmp = tkeys == -1                               # Tensor<remaining: bool> whether there is an empty slot, tkey==-1
            found = torch.nonzero(cmp)                      # Tensor<remaining_after_search: rindex_into_search> subset of search that is found
            ki = ri[found]                                  # Tensor<found: keyindex> indices of found keys in original key tensor
            result[ki] = search[found]                      # inserting table indices into result
            search = search[~cmp]                           # filtering search by keys that still haven't found empty slots
            ri = ri[~cmp]                                   # filtering rindex to match search
            search = (search + 1) % len(self.keys)          # updating search with linear probe
        return result

    def __contains__(self, key):
        return self.index(key) >= 0

    def __getitem__(self, key):
        return self.values[self.index(key)]



if __name__ == '__main__':
    m = HashTensor({
        6: -6,
        2: -2,
        5: -5,
        18: -18,
        17: -17
    })

    k = torch.tensor([2, 6, 6, 5, 3, 2, 18, 17, 17, 18], dtype=torch.long)
    v = m[k]

    print(v)