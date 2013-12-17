import os
import array

def arrayify(source_list):
    '''Efficient storage of a list of lists of integers in two Python :py:mod:`array`.

    *This is one of the most important tricks of the whole workbench, and yet it is only 10 lines of code!*

    Args:
        source_list (iterable):
            a list of lists of integers
    
    Returns:
        (index_array, items_array):
            two :py:mod:`array` s.

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

    for i in range(len(source_list)):
        items = source_list[i]
        dest_array.append(j)
        dests_array.append(len(items))
        dests_array.extend(items)
        j += 1 + len(items)
    return (dest_array, dests_array)

def normalize_ranges(ranges):
    '''Normalizes a set of ranges.

    Ranges come from the regions in the primary data.
    The anchors in the regions point to positions between characters in the primary data.
    So range (1,1) points to the point after the first character and before the second one.
    This range does not include any character. But the range (0,1) correspondes with the interval
    between the points before any character and the point after the first character.
    So this is character [0] in the string.
    
    Nodes may be linked to multiple regions. Then we get multiple ranges associated to nodes.
    This function simplifies a set of ranges: overlapping ranges will be joined, adjacent regions
    will be combined, ranges will be ordered.

    Args:
        ranges(iterable of 2-tuples):
            List of ranges, where every range is a tuple of exactly 2 integers.

    Returns:
        The result is a plain list of integers. The number of integers is even.
        The first two correspond to the first range, the second two to the second range and so on.
        This way we can deliver the results of many nodes as a compact *double_array*.
    '''
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

def model(data_items, temp_data_items, stamp):
    '''Remodels various data structures

    Args:
        data_items:
            data structures coming from :mod:`parse <graf.parse>`, that are here to stay

        temp_data_items:
            data structures coming from :mod:`parse <graf.parse>` that may be thrown away

        stamp (:class:`Timestamp <graf.timestamp.Timestamp>`):
            object for issuing progress messages

    Returns:
        The resulting permanent remodelled data structures.

    The transformations are:

    Nodes and regions:
        The list linking regions to nodes is transformed into a double array.

    Nodes and anchors:
        As a preparation to sorting, the minimal and maximal anchors of each node
        are determined. Nodes may be linked to many regions.

    Node sorting:
        Create a list of nodes in a sort order derived from their linking to regions,
        and the ordered nature of the primary data. 

        *node1* comes before *node2* if *node1* starts before *node2*.
        If *node1* and *node2* start at the same point, the object that ends last comes first.
        Otherwise objects count as equal in position.
        If the objects are sorted in this way, embedding objects come before all objects that are embedded in it.

    Nodes and edges:
        Collect the outgoing and incoming edges for each node in a pair of double arrays.

    '''
    result_items = []

    stamp.progress("NODES AND REGIONS")

    node_region_list = temp_data_items["node_region_list"]
    n_node = len(node_region_list)

    stamp.progress("NODES DETERMINING ANCHOR BOUNDARIES")

    node_anchor_min = array.array('I', [0 for i in range(n_node)])
    node_anchor_max = array.array('I', [0 for i in range(n_node)])
    node_linked = array.array('I')
    region_begin = temp_data_items["region_begin"]
    region_end = temp_data_items["region_end"]

    node_anchor_list = []
    for node in range(n_node):
        links = node_region_list[node]
        if len(links) == 0:
            node_anchor_list.append([])
            continue
        node_linked.append(node + 1)
        ranges = []
        for r in links:
            this_anchor_begin = region_begin[r - 1]
            this_anchor_end = region_end[r - 1]
            ranges.append((this_anchor_begin, this_anchor_end))
        norm_ranges = normalize_ranges(ranges)
        node_anchor_list.append(norm_ranges)

        node_anchor_min[node] = min(norm_ranges)
        node_anchor_max[node] = max(norm_ranges)

    (node_anchor, node_anchor_items) = arrayify(node_anchor_list)
    result_items.append(("node_anchor", node_anchor))
    result_items.append(("node_anchor_items", node_anchor_items))
    node_region_list = None
    node_anchor_list = None
    del temp_data_items["node_region_list"]

    stamp.progress("NODES SORTING BY REGIONS")

    def interval(ob):
        ''' Key function used when sorting objects according to embedding and left right.

        Args:
            iv (int, int):
                interval

        Returns:
            a tuple containing the left boundary and the nagative of the right boundary
        '''
        return (node_anchor_min[ob - 1], -node_anchor_max[ob - 1])

    node_sort = array.array('I', sorted(node_linked, key=interval))
    result_items.append(("node_sort", node_sort))

    node_anchor_min = None
    node_anchor_max = None

    stamp.progress("NODES AND EDGES")

    edges_from = data_items["edges_from"]
    edges_to = data_items["edges_to"]
    n_edge = len(edges_from)

    edges_in = [[] for i in range(n_node)]
    edges_out = [[] for i in range(n_node)]

    for i in range(n_edge):
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

