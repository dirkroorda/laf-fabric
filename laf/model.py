import os
import collections
import array
from .lib import grouper

def arrayify(source_list):
    '''Efficient storage of a list of lists of integers in two Python :py:mod:`array`.

    *This is one of the most important tricks of the LAF-Fabric, and yet it is only 10 lines of code!*

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
            data structures coming from :mod:`parse <laf.parse>`, that are here to stay

        temp_data_items:
            data structures coming from :mod:`parse <laf.parse>` that may be thrown away

        stamp (:class:`Timestamp <laf.timestamp.Timestamp>`):
            object for issuing progress messages

    Returns:
        The resulting permanent remodelled data structures.

    The transformations are:

    Nodes and regions:
        The list linking regions to nodes is transformed into a double array.

    Nodes and anchors:
        As a preparation to sorting, the minimal and maximal anchors of each node
        are determined. Nodes may be linked to many regions.

        It also creates a list of node events:

        For each anchor position, a list will be created of nodes that start, terminate, suspend and resume there.
        
        * A node *starts* at an anchor if the anchor is the first anchor position of that node
        * A node *terminates* at an anchor if the anchor is the last anchor position of that node
        * A node *suspends* at an anchor position if
            #. the anchor position belongs to that node, 
            #. the next anchor position does not belong to that node
            #. there are later anchor positions that belong to that node
        * A node *resumes* at an anchor position if
            #. the anchor position belongs to that node, 
            #. the previous anchor position does not belong to that node
            #. there are earlier anchor positions that belong to that node

    Node sorting:
        Create a list of nodes in a sort order derived from their linking to regions,
        and the ordered nature of the primary data. 

        *node1* comes before *node2* if *node1* starts before *node2*.
        If *node1* and *node2* start at the same point, the object that ends last comes first.
        Otherwise objects count as equal in position.
        If the objects are sorted in this way, embedding objects come before all objects that are embedded in it.

    Nodes and edges:
        Collect the outgoing and incoming edges for each node in a pair of double arrays.

        Collect the set of unannotated edges.

    '''
    result_items = []

    stamp.progress("NODES AND REGIONS")

    node_region_list = temp_data_items["node_region_list"]
    n_node = len(node_region_list)

    stamp.progress("NODES ANCHOR BOUNDARIES")

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
    result_items.append(("node_anchor_min", node_anchor_min))
    result_items.append(("node_anchor_max", node_anchor_max))
    result_items.append(("node_anchor", node_anchor))
    result_items.append(("node_anchor_items", node_anchor_items))
    node_region_list = None
    del temp_data_items["node_region_list"]

    def interval(node):
        ''' Key function used when sorting objects according to embedding and left right.

        Args:
            node (int):
                interval

        Returns:
            a tuple containing the left boundary and the nagative of the right boundary
        '''
        return (node_anchor_min[node - 1], -node_anchor_max[node - 1])

    stamp.progress("NODES EVENTS")

    anchor_max = max(node_anchor_max)
    node_events = list([collections.deque([]) for n in range(anchor_max + 1)])

    for (n, ranges) in enumerate(node_anchor_list):
        for (r, (a_start, a_end)) in enumerate(grouper(ranges, 2)):
            is_first = r == 0
            is_last = r == (len(ranges) / 2) - 1
            start_kind = 0 if is_first else 1 # 0 = start,   1 = resume
            end_kind = 3 if is_last else 2    # 2 = suspend, 3 = end
            node_events[a_start].append((n + 1, start_kind))
            node_events[a_end].appendleft((n + 1, end_kind))

    node_events_n = array.array('I')
    node_events_k = array.array('I')
    node_events_a = list([[] for n in range(anchor_max + 1)])

    e_index = 0
    for (anchor, events) in enumerate(node_events):
        for (node, kind) in sorted(events, key=lambda e: (interval(e[0]), e[1])):
            node_events_n.append(node)
            node_events_k.append(kind)
            node_events_a[anchor].append(e_index)
            e_index += 1

    node_events = None
    (node_events, node_events_items) = arrayify(node_events_a)
    node_events_a = None

    result_items.append(("node_events_n", node_events_n))
    result_items.append(("node_events_k", node_events_k))
    result_items.append(("node_events", node_events))
    result_items.append(("node_events_items", node_events_items))

    node_anchor_list = None

    stamp.progress("NODES SORTING BY REGIONS")

    node_sort = array.array('I', sorted(node_linked, key=interval))
    result_items.append(("node_sort", node_sort))

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

    stamp.progress("PLAIN EDGES")

    return result_items

