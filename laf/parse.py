from xml.sax import parse as saxparse, SAXException
from xml.sax.handler import ContentHandler
import array
from .names import Names, FabricError

aspace_not_given = "_original_"

def init():
    global good_regions
    good_regions = 0
    global linked_nodes
    linked_nodes = 0
    global good_edges
    good_edges = 0
    global good_annots
    good_annots = 0
    global good_feats
    good_feats = 0

    global faulty_regions
    faulty_regions = 0
    global unlinked_nodes
    unlinked_nodes = 0
    global faulty_edges
    faulty_edges = 0
    global faulty_annots
    faulty_annots = 0
    global faulty_feats
    faulty_feats = 0

    global primary_data_file
    primary_data_file = None

    global annotation_files
    annotation_files = []

    global identifiers_r
    identifiers_r = {}
    global identifiers_n
    identifiers_n = {}
    global identifiers_e
    identifiers_e = {}

    global id_region
    id_region = 0
    global id_node
    id_node = 0
    global id_edge
    id_edge = 0
    global id_annot
    id_annot = 0

    global region_begin
    region_begin = array.array('I')
    global region_end
    region_end = array.array('I')
    global node_region_list
    node_region_list = []
    global edges_from
    edges_from = array.array('I')
    global edges_to
    edges_to = array.array('I')
    global feature
    feature = {}
    global efeature
    efeature = {}

class HeaderHandler(ContentHandler):
    def __init__(self): self._tag_stack = []
    def startElement(self, name, attrs):
        global primary_data_file
        self._tag_stack.append(name)
        if name == "annotation": annotation_files.append(attrs["loc"])
        elif name == "primaryData": primary_data_file = attrs["loc"]
    def endElement(self, name): self._tag_stack.pop()
    def characters(self, ch): name = self._tag_stack[-1]

class AnnotationHandler(ContentHandler):
    file_name = None
    nid = None
    aid = None
    stamp = None

    truth = {
        'yes': True,
        '1': True,
        'on': True,
        'true': True,
        'no': False,
        '0': False,
        'off': False,
        'false': False,
    }

    def __init__(self, annotation_file, stamp):
        self.file_name = annotation_file
        self._tag_stack = []
        self.stamp = stamp
        self.aempty = None
        self.aspace_default = aspace_not_given
        self.aspace = None
        self.alabel = None
        self.atype = None
        self.aref = None
        self.node_link = None

    def startElement(self, name, attrs):
        self._tag_stack.append(name)
        if name == "annotationSpace":
            if "as.id" in attrs:
                self.aspace = attrs["as.id"]
                if "default" in attrs:
                    is_default = attrs["default"].casefold()
                    if is_default in self.truth and self.truth[is_default]: self.aspace_default = self.aspace
            if self.aspace == None: self.aspace = self.aspace_default
        elif name == "region":
            global faulty_regions
            global good_regions
            global id_region
            rid = attrs["xml:id"]
            identifiers_r[rid] = id_region
            id_region += 1
            anchors = attrs["anchors"].split(" ")
            if len(anchors) != 2:
                faulty_regions += 1
                raise FabricError("invalid anchor spec '{}' for region {} in {}".format(attrs["anchors"], rid, self.file_name), self.stamp)
                region_begin.append(0)
                region_end.append(0)
            else:
                good_regions += 1
                region_begin.append(int(anchors[0]))
                region_end.append(int(anchors[1]))
        elif name == "node":
            global id_node
            nid = attrs["xml:id"]
            identifiers_n[nid] = id_node
            id_node += 1
            self.node_link = None
            self.nid = nid 
        elif name == "link": self.node_link = attrs["targets"].split(" ")
        elif name == "edge":
            global faulty_edges
            global good_edges
            global id_edge
            eid = attrs["xml:id"]
            identifiers_e[eid] = id_edge
            id_edge += 1
            from_node = attrs["from"]
            to_node = attrs["to"]
            if not from_node or not to_node:
                faulty_edges += 1
                raise FabricError("invalid from/to spec from='{}' to='{}' for edge {} in {}".format(from_node, to_node, eid, self.file_name), self.stamp)
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
            self.aid = aid
            self.aempty = True
            if "as" in attrs: self.aspace = attrs["as"]
            else: self.aspace = self.aspace_default
            self.alabel = attrs["label"]
            node_or_edge = attrs["ref"]
            if not self.alabel or not node_or_edge:
                faulty_annots += 1
                raise FabricError("invalid annotation spec label='{}' ref='{}' for annotation {} in {}".format(self.alabel, node_or_edge, self.aid, self.file_name), self.stamp)
            else:
                self.aref = None
                self.atype = None
                if node_or_edge in identifiers_n:
                    self.aref = identifiers_n[node_or_edge]
                    self.atype = 'n'
                    good_annots += 1
                elif node_or_edge in identifiers_e:
                    self.aref = identifiers_e[node_or_edge]
                    self.atype = 'e'
                    good_annots += 1
                else:
                    faulty_annots += 1
                    raise FabricError("invalid annotation target ref='{}' (no node, no edge) for annotation {} in {}".format(node_or_edge, self.aid, self.file_name), self.stamp)
        elif name == "f":
            global faulty_feats
            global good_feats
            self.aempty = False
            fname = attrs["name"]
            if not fname:
                faulty_feats += 1
                raise FabricError("invalid feature spec name='{}' value='{}' for feature in annotation {} in file {}".format(fname, value, self.aid, self.file_name), self.stamp)
            elif self.aref == None:
                faulty_feats += 1
                raise FabricError("undetermined feature kind (node/edge) for feature {} in annotation {} in {}".format(fname, self.aid, self.file_name), self.stamp)
            else:
                good_feats += 1
                value = attrs["value"]
                dest = feature if self.atype == 'n' else efeature
                dest.setdefault((self.aspace, self.alabel, fname), {})[self.aref] = value

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
                fname = ''
                value = ''
                dest = feature if self.atype == 'n' else efeature
                dest.setdefault((self.aspace, self.alabel, fname), {})[self.aref] = value
        self._tag_stack.pop()

    def characters(self, ch): pass

def parse(origin, graf_header_file, stamp, data_items):
    '''Parse a LAF/GrAF resource and deliver results.'''
    init()
    saxparse(graf_header_file, HeaderHandler())

    if origin == 'm':
        with open(primary_data_file, "r", encoding="utf-8") as f: primary_data = f.read(None)
        Names.deliver(primary_data, (origin + 'P00', ('primary_data',)), data_items)

    for kind in ('n', 'e'):
        xi_key = Names.comp('mX' + kind + 'f', ())
        xmlitems = data_items[xi_key] if xi_key in data_items else {}
        if kind == 'n':
            global identifiers_n
            identifiers_n = xmlitems
        else:
            global identifiers_e
            identifiers_e = xmlitems

    for annotation_file in annotation_files:
        stamp.Imsg("parsing {}".format(annotation_file))
        saxparse(annotation_file, AnnotationHandler(annotation_file, stamp))

    mg = '''END PARSING
{:>10} good   regions  and {:>5} faulty ones
{:>10} linked nodes    and {:>5} unlinked ones
{:>10} good   edges    and {:>5} faulty ones
{:>10} good   annots   and {:>5} faulty ones
{:>10} good   features and {:>5} faulty ones
{:>10} distinct xml identifiers
'''.format(
        good_regions, faulty_regions,
        linked_nodes, unlinked_nodes,
        good_edges, faulty_edges,
        good_annots, faulty_annots,
        good_feats, faulty_feats,  
        id_region + id_node + id_edge + id_annot,
    )
    stamp.Imsg(mg)
    if origin == 'm':
        Names.deliver(identifiers_n, (origin + 'Xnf', ()), data_items)
        Names.deliver(identifiers_e, (origin + 'Xef', ()), data_items)
        Names.deliver(edges_from, (origin + 'G00', ('edges_from',)), data_items)
        Names.deliver(edges_to, (origin + 'G00', ('edges_to',)), data_items)
        Names.deliver(region_begin, (origin + 'T00', ('region_begin',)), data_items)
        Names.deliver(region_end, (origin + 'T00', ('region_end',)), data_items)
        Names.deliver(node_region_list, (origin + 'T00', ('node_region_list',)), data_items)

    for f in feature: Names.deliver(feature[f], (origin + 'Fn0', f), data_items)
    for f in efeature: Names.deliver(efeature[f], (origin + 'Fe0', f), data_items)
