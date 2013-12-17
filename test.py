# -*- coding: utf8 -*-

ranges = [(1,1), (1,3), (2,5), (6,6), (8,10), (10, 10), (7,8), (100, 105), (83, 83), (80, 85), (82, 82)]

def normalize_ranges(ranges):
    covered = {}
    for (start, end) in ranges:
        if start == end:
            if start not in covered:
                covered[start] = False
        else:
            for i in range(start, end):
                covered[i] = True
    cur_start = None
    cur_end = None
    result = []
    for i in sorted(covered.keys()):
        if not covered[i]:
            if cur_end != None:
                result.extend((cur_start, cur_end))
            result.extend((i, i))
            cur_start = None
            cur_end = None
        elif cur_end == None or i > cur_end:
            if cur_end != None:
                result.extend((cur_start, cur_end))
            cur_start = i
            cur_end = i + 1
        else:
            cur_end = i + 1
    if cur_end != None:
        result.extend((cur_start, cur_end))

    return result

print("{}".format(normalize_ranges(ranges)))
