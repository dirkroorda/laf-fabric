from itertools import zip_longest

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper([1,2,3,4,5], 2, 0) --> [1,2] [3,4] [5,0]"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

