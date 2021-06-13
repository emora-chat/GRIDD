
import torch
from GRIDD.data_structures.graph_matching.primes import prime
from GRIDD.utilities.profiler import profiler as p


class HashTensor:
    """
    Create a hash map to concurrently access integer -> integer
    values. Keys and values must be >= 0.
    """

    def __init__(self, mapping, device='cpu'):
        self.device = torch.device(device)
        self.keys = torch.tensor([], dtype=torch.long, device=self.device)
        self.values = torch.tensor([], dtype=torch.long, device=self.device)
        self.update(mapping)

    def update(self, mapping):
        if self.keys is not None:
            mapping.update(self.keys)
        tablesize = prime(len(mapping) * 5) or len(mapping) * 5
        self.keys = torch.full((tablesize,), -1, dtype=torch.long, device=self.device)
        self.values = torch.full((tablesize,), -1, dtype=torch.long, device=self.device)
        items = torch.tensor(list(mapping.items()), dtype=torch.long, device=self.device)
        keys, values = items[:,0], items[:,1]
        while len(keys) > 0:
            insert_index = self.insertion_index(keys)
            collisions = torch.eq(insert_index.unsqueeze(1), insert_index.unsqueeze(1).T)
            cooccupied = torch.sum(collisions, 1)
            collided = cooccupied > 1
            self.keys[insert_index] = keys
            self.values[insert_index] = values
            keys, values = keys[collided], values[collided]

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
            cmp = torch.logical_or(tkeys==-1, tkeys==key[ri])   # Tensor<remaining: bool> whether there is an empty slot, tkey==-1, or key is found
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
            result[ki] = self.values[search[found]]         # inserting table values into result
            searching = torch.logical_and(~cmp, tkeys!=-1)  # Tensor<remaining: bool> whether still searching for key (neither lost nor found)
            search = search[searching]                      # filtering search by keys still searching for
            ri = ri[searching]                              # filtering rindex to match search
            search = (search + 1) % len(self.keys)          # updating search with linear probe
        return result



if __name__ == '__main__':
    m = HashTensor({
        1: 2,
        2: 3,
        3: 4,
        11: 12,
        12: 13,
        13: 14
    })

    k = torch.tensor([1, 2, 12, 4, 14], dtype=torch.long)
    v = m[k]

    print(v)