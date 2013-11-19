# -*- coding: utf8 -*-

import os

from xml.sax import parse as saxparse, SAXException
from xml.sax.handler import ContentHandler

import array
import collections

good_regions = 0
linked_nodes = 0
good_edges = 0
good_annots = 0
good_feats = 0

faulty_regions = 0
unlinked_nodes = 0
faulty_edges = 0
faulty_annots = 0
faulty_feats = 0

annotation_files = []

identifiers_r = {}
identifiers_n = {}
identifiers_e = {}
identifiers_a = {}

id_feat_name_node = 0
id_feat_name_edge = 0
id_feat_value = 0
id_region = 0
id_node = 0
id_edge = 0
id_annot = 0

feat_name_list_node_rep = {}
feat_name_list_edge_rep = {}
feat_name_list_node_int = {}
feat_name_list_edge_int = {}
feat_value_list_rep = {}
feat_value_list_int = {}
region_begin = array.array('I')
region_end = array.array('I')
node_region_list = []
edges_from = array.array('I')
edges_to = array.array('I')
feat_ref_node = collections.defaultdict(lambda:array.array('I'))
feat_value_node = collections.defaultdict(lambda:array.array('I'))
feat_ref_edge = collections.defaultdict(lambda:array.array('I'))
feat_value_edge = collections.defaultdict(lambda:array.array('I'))

class HeaderHandler(ContentHandler):
    '''Handlers used by SAX parsing the GrAF header file.

    We just collect the contents of the *loc* attributes of the *annotation* elements.
    These are the annotation files that we have to fetch and compile.
    '''
    stamp = None

    def __init__(self, stamp):
        self._tag_stack = []
        self.stamp = stamp
        pass

    def startElement(self, name, attrs):
        self._tag_stack.append(name)
        if name == "annotation":
            annotation_files.append(attrs["loc"])

    def endElement(self, name):
        self._tag_stack.pop()

    def characters(self, ch):
        name = self._tag_stack[-1]

class AnnotationHandler(ContentHandler):
    '''Handlers used by SAX parsing the annotation files themselves

    We have to collect all elements *region*, *node* and subelement *link*, *edge*, *a* (annotation) and *f* (feature).
    From these elements we retrieve identifiers and other attributes. we map all identifiers to integers. When we have to associate one piece of data to other pieces, we create arrays of those integers.

    The parse process is robust, we are not dependent on a particular ordering or distribution of the regions, nodes, edges, annotations and features in/over the annotation files.

    Here is a description of the arrays we create:

    *region_begin*, *region_end*
        Every region has an *anchors* attribute specifying a point or interval in the primary data. We consider a point *i* as the interval *i .. i*.
        *region_begin* contains the start anchor of region *i* for each *i*, and *region_end* the end anchor.

    *edges_from*, *edges_to*
        Every edge goes from one node to an other. *edges_from* contains the from node of edge *i* for each *i*, and *edges_end* the to node.

    Here is a description of the dictionaries we create:

    *feat_name_list_node_rep*, *feat_name_list_edge_rep*, *feat_name_list_node_int*, *feat_name_list_edge_int*
        Mappings from the string representations to the internal codes and vice versa, respectively, for feature names.
        These are the *extended* feature names, i.e. with the label of the annotation in which the feature occurs prepended to it (separated with a ``.``).
        Features for nodes occupy and features for edges occupy separate but similar datastructures.

    *feat_value_list_rep*, *feat_value_list_int*
        Mappings from the string representations to the internal codes and vice versa, respectively, for feature values.

    There is also a list of arrays:

    *node_region_list*
        Element *i* of this list contains an array with the regions attached to node *i*.
    '''

    file_name = None
    nid = None
    aid = None
    alabel = None
    atype = None
    aref = None
    node_link = None
    stamp = None

    def __init__(self, annotation_file, stamp):
        self.file_name = annotation_file
        self._tag_stack = []
        self.stamp = stamp
        pass

    def startElement(self, name, attrs):
        self._tag_stack.append(name)
        if name == "region":
            global faulty_regions
            global good_regions
            global id_region
            rid = attrs["xml:id"]
            id_region += 1
            identifiers_r[rid] = id_region
            anchors = attrs["anchors"].split(" ")
            if len(anchors) != 2:
                faulty_regions += 1
                msg = u"ERROR: invalid anchor spec '{}' for region {} in {}".format(attrs["anchors"], rid, self.file_name)
                self.stamp.progress(msg)
                region_begin.append(0)
                region_end.append(0)
            else:
                good_regions += 1
                region_begin.append(int(anchors[0]))
                region_end.append(int(anchors[1]))
        elif name == "node":
            global id_node
            nid = attrs["xml:id"]
            id_node += 1
            identifiers_n[nid] = id_node
            self.node_link = None
            self.nid = nid 
        elif name == "link":
            self.node_link = attrs["targets"].split(" ")
        elif name == "edge":
            global faulty_edges
            global good_edges
            global id_edge
            eid = attrs["xml:id"]
            id_edge += 1
            identifiers_e[eid] = id_edge
            from_node = attrs["from"]
            to_node = attrs["to"]
            if not from_node or not to_node:
                faulty_edges += 1
                msg = u"ERROR: invalid from/to spec from='{}' to='{}' for edge {} in {}".format(from_node, to_node, eid, self.file_name)
                self.stamp.progress(msg)
                print msg
            else:
                good_edges += 1
                edges_from.append(identifiers_n[from_node])
                edges_to.append(identifiers_n[to_node])
        elif name == "a":
            global faulty_annots
            global good_annots
            global id_annot
            aid = attrs["xml:id"]
            id_annot += 1
            identifiers_a[aid] = id_annot
            self.aid = aid
            self.aempty = True
            label = attrs["label"]
            node_or_edge = attrs["ref"]
            if not label or not node_or_edge:
                faulty_annots += 1
                msg = u"ERROR: invalid annotation spec label='{}' ref='{}' for annotation {} in {}".format(label, node_or_edge, self.aid, self.file_name)
                self.stamp.progress(msg)
                print msg
            else:
                ref_id = None
                ref_type = None
                if node_or_edge in identifiers_n:
                    ref_id = identifiers_n[node_or_edge]
                    ref_type = True
                elif node_or_edge in identifiers_e:
                    ref_id = identifiers_e[node_or_edge]
                    ref_type = False
                else:
                    msg = u"ERROR: invalid annotation target ref='{} (no node, no edge)' for annotation {} in {}".format(node_or_edge, self.aid, self.file_name)
                    self.stamp.progress(msg)
                    print msg
                good_annots += 1
                self.alabel = label
                self.atype = ref_type
                self.aref = ref_id
        elif name == "f":
            global faulty_feats
            self.aempty = True
            name = attrs["name"]
            if not name:
                faulty_feats += 1
                msg = u"ERROR: invalid feature spec name='{}' value='{}' for feature in annotation in file {}".format(name, value, self.aid, self.file_name)
                self.stamp.progress(msg)
                print msg
            name = u'{}.{}'.format(self.alabel, attrs["name"])
            value = attrs["value"]
            add_feature_instance(self.atype, name, self.aref, value)

    def endElement(self, name):
        if name == "node":
            global unlinked_nodes
            global linked_nodes
            if not self.node_link:
                unlinked_nodes += 1
                node_region_list.append(array.array('I', []))
            else:
                linked_nodes += 1
                node_region_list.append(array.array('I',[identifiers_r[r] for r in self.node_link]))
        elif name == "a":
            if self.aempty:
                name = self.alabel
                value = 1
                add_feature_instance(self.atype, name, self.aref, value)

        self._tag_stack.pop()

    def characters(self, ch):
        pass

def add_feature_instance(atype, name, aref, value):
    global good_feats
    global id_feat_name_node
    global id_feat_name_edge
    global id_feat_value
    this_fn_id = None
    if atype:
        if name in feat_name_list_node_rep:
            this_fn_id = feat_name_list_node_rep[name]
        else:
            id_feat_name_node += 1
            feat_name_list_node_rep[name] = id_feat_name_node
            feat_name_list_node_int[id_feat_name_node] = name
            this_fn_id = id_feat_name_node
    else:
        if name in feat_name_list_edge_rep:
            this_fn_id = feat_name_list_edge_rep[name]
        else:
            id_feat_name_edge += 1
            feat_name_list_edge_rep[name] = id_feat_name_edge
            feat_name_list_edge_int[id_feat_name_edge] = name
            this_fn_id = id_feat_name_edge
    this_fv_id = None
    if value in feat_value_list_rep:
        this_fv_id = feat_value_list_rep[value]
    else:
        id_feat_value += 1
        feat_value_list_rep[value] = id_feat_value
        feat_value_list_int[id_feat_value] = value
        this_fv_id = id_feat_value
    good_feats += 1
    if atype:
        feat_ref_node[this_fn_id].append(aref)
        feat_value_node[this_fn_id].append(this_fv_id)
    else:
        feat_ref_edge[this_fn_id].append(aref)
        feat_value_edge[this_fn_id].append(this_fv_id)

def parse(graf_header_file, stamp):
    '''Parse a GrAF resource.
    
    Parses a GrAF resource, starting by SAX parsing its header file and subsequently parsing all
    files mentioned in that header file.

    Args:
        graf_header_file (str): path to the GrAF header file

    Returns:
        a tuple of items which comprise the parse results.

    Every member of the returned tuple is itself a tuple of 3 pieces of information:

    #. A *key* which acts as a name for this part of the result data
    #. The data itself, as described in :class:`AnnotationHandler`
    #. A boolean indicating whether this data is a temporary result or a permanent result

    Temporary results will be discarded after the remodeling step, permanent results will be incorporated in 
    the task-executing object.
    '''

    saxparse(graf_header_file, HeaderHandler(stamp))

    for annotation_file in annotation_files:
        msg = u"parsing {}".format(annotation_file)
        stamp.progress(msg)
        saxparse(annotation_file, AnnotationHandler(annotation_file, stamp))

    msg = u'''END PARSING
{:>10} good   regions  and {:>5} faulty ones
{:>10} linked nodes    and {:>5} unlinked ones
{:>10} good   edges    and {:>5} faulty ones
{:>10} good   annots   and {:>5} faulty ones
{:>10} good   features and {:>5} faulty ones
{:>10} distinct feature names for nodes
{:>10} distinct feature names for edges
{:>10} distinct feature values
{:>10} distinct xml identifiers
'''.format(
        good_regions, faulty_regions,
        linked_nodes, unlinked_nodes,
        good_edges, faulty_edges,
        good_annots, faulty_annots,
        good_feats, faulty_feats,  
        len(feat_name_list_node_rep),
        len(feat_name_list_edge_rep),
        len(feat_value_list_rep),
        id_region + id_node + id_edge + id_annot
    )
    stamp.progress(msg)
    return (
        ("feat_name_list_node_rep", feat_name_list_node_rep, True),
        ("feat_name_list_node_int", feat_name_list_node_int, True),
        ("feat_name_list_edge_rep", feat_name_list_edge_rep, True),
        ("feat_name_list_edge_int", feat_name_list_edge_int, True),
        ("feat_value_list_rep", feat_value_list_rep, True),
        ("feat_value_list_int", feat_value_list_int, True),
        ("region_begin", region_begin, True),
        ("region_end", region_end, True),
        ("node_region_list", node_region_list, False),
        ("edges_from", edges_from, True),
        ("edges_to", edges_to, True),
        ("feat_ref", {'node': feat_ref_node, 'edge': feat_ref_edge}, True),
        ("feat_value", {'node': feat_value_node, 'edge': feat_value_edge}, True),
    )


