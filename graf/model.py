# -*- coding: utf8 -*-

import os

import array

def arrayify(source_list):
    '''Efficient storage of a list of lists of integers in two Python :py:mod:`array`.

    *This is one of the most important tricks of the whole workbench, and yet it is only 10 lines of code!*

    Args:
        source_list (iterable): a list of lists of integers
    
    Returns:
        (index_array, items_array): two :py:mod:`array` s.
        *index_array* contains an index for each item in *source_list*.
        *items_array* contains all the items in the following way: if an item with *n* members has to be added,
        then first the number *n* is added, and then all the members.
        This is how you get the original information back: if you want the 
        members of item *i* in *source_list*, read number *i* in *index_array*, say *k*, go to position *k* in
        *items_array*, read the number at that position, say *n*,
        and then find the members at the next *n* positions in *items_array*.

    '''
    dest_array = array.array('I')
    dests_array = array.array('I')
    j = 0

    for i in xrange(len(source_list)):
        items = source_list[i]
        dest_array.append(j)
        dests_array.append(len(items))
        dests_array.extend(items)
        j += 1 + len(items)
    return (dest_array, dests_array)

def model(data_items, temp_data_items, stamp):
    result_items = []

    stamp.progress("NODES AND REGIONS")

    node_region_list = temp_data_items["node_region_list"]
    n_node = len(node_region_list)
    (node_region, node_region_items) = arrayify(node_region_list)
    result_items.append(("node_region", node_region))
    result_items.append(("node_region_items", node_region_items))

    stamp.progress("NODES DETERMINING ANCHOR BOUNDARIES")

    node_anchor_min = array.array('I', [0 for i in xrange(n_node)])
    node_anchor_max = array.array('I', [0 for i in xrange(n_node)])
    node_linked = array.array('I')
    region_begin = data_items["region_begin"]
    region_end = data_items["region_end"]

    for node in range(n_node):
        links = node_region_list[node]
        if len(links) == 0:
            continue
        node_linked.append(node + 1)
        cur_min = 0
        cur_max = 0
        first = True
        for r in links:
            this_anchor_begin = region_begin[r - 1]
            this_anchor_end = region_end[r - 1]
            if first:
                cur_min = this_anchor_begin
                cur_max = this_anchor_end
                first = False
            else:
                if this_anchor_begin < cur_min:
                    cur_min = this_anchor_begin
                if this_anchor_end > cur_max:
                    cur_max = this_anchor_end
        node_anchor_min[node] = cur_min
        node_anchor_max[node] = cur_max

    node_region_list = None
    del temp_data_items["node_region_list"]

    stamp.progress("NODES SORTING BY REGIONS")

    def sort_by_region(l, r):
        ''' Comparison function used when sorting objects according to the extreme boundaries of its regions.
        Object1 comes before Object2 if Object 1 starts before Object 2.
        Object1 comes after Object2 if Object 1 starts after Object 2.
        If Object1 and Object2 start at the same monad, the object that ends last comes first.
        Otherwise objects count as equal.
        If the objects are sorted in this way, embedding objects come before all objects that are embedded in it.
        '''

        l_min_anchor = node_anchor_min[l - 1]
        l_max_anchor = node_anchor_max[l - 1]
        r_min_anchor = node_anchor_min[r - 1]
        r_max_anchor = node_anchor_max[r - 1]
        maincmp = cmp(l_min_anchor, r_min_anchor)
        return maincmp if maincmp else cmp(r_max_anchor, l_max_anchor)

    node_sort = array.array('I', sorted(node_linked, sort_by_region))
    result_items.append(("node_sort", node_sort))

    node_anchor_min = None
    node_anchor_max = None

    stamp.progress("NODES AND EDGES")

    edges_from = data_items["edges_from"]
    edges_to = data_items["edges_to"]
    n_edge = len(edges_from)

    edges_in = [[] for i in xrange(n_node)]
    edges_out = [[] for i in xrange(n_node)]

    for i in xrange(n_edge):
        node_from = edges_from[i]
        node_to = edges_to[i]
        edges_out[node_from - 1].append(node_to)
        edges_in[node_to - 1].append(node_from)

    (node_out, node_out_items) = arrayify(edges_out)
    (node_in, node_in_items) = arrayify(edges_in)
    result_items.append(("node_out", node_out))
    result_items.append(("node_out_items", node_out_items))
    result_items.append(("node_in", node_in))
    result_items.append(("node_in_items", node_in_items))

    edges_out = None
    edges_in = None

    return result_items

