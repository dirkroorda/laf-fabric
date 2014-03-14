import os
import imp
import sys
import time
import glob
import subprocess
import collections
from .lib import grouper

import array
import pickle

from .settings import Names
from .laf import Laf

class Feature(object):
    def __init__(self, lafapi, feature, kind):
        self.source = lafapi
        self.kind = kind
        self.lookup = lafapi.data_items[Names.f2key(feature, kind, 'main')]
        self.alookup = lafapi.data_items[Names.f2key(feature, kind, 'annox')]

    def v(self, ne):
        return self.alookup.get(ne, self.lookup(ne))

    def s(self, value=None):
        order = self.source.data_items['node_sort_inv']
        domain = sorted(set(self.lookup) + set(self.alookup), key=lambda x:order[x])
        if value == None:
            for n in domain:
                yield n
        else:
            for n in domain:
                if self.alookup.get(n, self.lookup.get(n)) == value:
                    yield n

class Connection(object):
    def __init__(self, lafapi, feature, inv):
        self.source = lafapi
        self.inv = inv
        self.lookup = lafapi.data_items[Names.c2key(feature, inv, 'main')]
        self.alookup = lafapi.data_items[Names.f2key(feature, inv, 'annox')]

    def v(self, n):
        lookup = self.lookup
        alookup = self.alookup
        for m in set(lookup.get(n, {})) | set(alookup.get(n, {})):
            yield m

    def vv(self, n):
        lookup = self.lookup
        alookup = self.alookup
        for m in set(lookup.get(n, {})) | set(alookup.get(n, {})):
            yield (m, alookup.get(n, lookup.get(n)).get(m, lookup.get(n).get(m)))

    def endnodes(self, value=None, node_set):
        visited = set()
        result = set()
        next_set = node_set
        while next_set:
            new_next_set = set()
            for node in next_set:
                visited.add(node)
                next_nodes = set(self.v(node)) if value == None else set([n[0] for n in self.vv(node) if n[1] == value])
                if next_nodes:
                    new_next_set |= next_nodes - visited
                else:
                    result.add(node)
            next_set = new_next_set
        return result

class XMLid(object):
    def __init__(self, lafapi, kind):
        self.kind = kind
        self.code = lafapi.data_items[Names.x2key('inv', kind)]
        self.rep = lafapi.data_items[Names.x2key('rep', kind)]

    def r(self, int_code):
        return self.rep[int_code]

    def i(self, xml_id):
        return self.code[xml_id]

class Bunch(object)
    def __init__(self):
        self.item = {}

class XMLids(object):
    '''This class is responsible for holding a bunch of XML mappings (node and or edge) and makes them 
    accessible by member names.
    '''
    def __init__(self, xmlid_objects):
        '''Upon creation, a set of xmlid objects (node and or edge) is taken in,

        Args:
            xmlid_objects (iterable of :class:`XMLid`)
        '''
        for xo in xmlid_objects:
            exec("self.{} = xo".format(xo.local_name))

class PrimaryData(object):
    '''This class is responsible for giving access to the primary data.
    '''
    def __init__(self, lafapi):
        '''Upon creation, the primary data is pointed to.

        Args:
            lafapi(:class:`LafAPI <laf.task.LafAPI>`):
                The task executing object that has all the data.
        '''
        self.all_data = lafapi.data_items['data']
        '''Member that holds the primary data as a single UNICODE string.
        '''
        self.lafapi = lafapi

    def data(self, node):
        '''Gets the primary data to which a node is linked.

        Args:
            node(int):
                The node in question

        Returns:
            None:
                if the node is not linked to regions of primary data
            List of (N, text):
                all positions *N* to which the node is linked, where *text* is the primary data
                stretch starting at position *N* that is linked to the node.
                *text* may be empty.
                The list is normalized: all stretches are maximal, non overlapping and occur
                in the order of the primary data (ascending *N*). 
        '''
        lafapi = self.lafapi
        regions = lafapi.getitems(lafapi.data_items['node_anchor'], lafapi.data_items['node_anchor_items'], node)
        if not regions:
            return None
        all_text = self.all_data
        result = []
        for r in grouper(regions, 2):
            result.append((r[0], all_text[r[0]:r[1]]))
        return result

class LafAPI(Laf):
    def __init__(self, settings):
        Laf.__init__(self, settings)
        self.result_files = []
        cur_dir = os.getcwd()
        task_dir = self.settings['locations']['task_dir']
        task_include_dir = None if task_dir == '<' else task_dir if task_dir.startswith('/') else '{}/{}'.format(cur_dir, task_dir)
        if task_include_dir != None:
            sys.path.append(task_include_dir)

    def API(self):
        data_items = self.data_items

        api = {
            'F': Bunch(),
            'FE': Bunch(),
            'C': Bunch(),
            'Ci': Bunch(),
            'X': Bunch(),
        }

#   FEATURES AND CONNECTIVITY
        features = {'node': set(), 'edge': set()}
        for dkey in data_items:
            comps = Names.key2f(dkey)
            if comps:
                (feat, fkind, fdata) = comps
                features[fkind].add(feat)
                (namespace, label, name) = feat

        for kind in features:
            for feat in features[kind]:
                name = Names.f2api(feat) 
                obj = Feature(self, feat, kind)
                dest = api['F'] if kind == 'node' else api['FE']
                dest.item[name] = obj
                setattr(dest, name, obj)

        for feat in features['edge']:
            name = Names.f2api(feat) 
            for inv in (False, True):
                obj = Connection(self, feat, inv)
                dest = api['Ci'] if inv else api['C']
                dest.item[name] = obj
                setattr(dest, name, obj)

        all_features = collections.defaultdict(lambda: collections.defaultdict(lambda: set()))

                all_features[fkind][namespace].add("{}.}".format(label, name))
        def feature_list(kind):
            result = []
            for namespace in sorted(all_features[kind]):
                result.append((namespace, sorted(all_features[kind][namespace])))
            
# XML IDS



        node_anchor_min = data_items["node_anchor_min"]
        node_anchor_max = data_items["node_anchor_max"]

        def before(nodea, nodeb):
            '''Compares two nodes based on its linking to the primary data.

            This is the canonical order, based on *(x,-y)*, where *x* is the leftmost
            anchor and *y* the rightmost anchor of a node.

            Args:
                nodea, nodeb(int): the nodes to compare.

            Returns:
                True:
                    if *nodea* comes before *nodeb*
                False:
                    if *nodea* comes after *nodeb*
                None
                    if *nodea* and *nodeb* have equal leftmost and rightmost anchors
                    (this includes the case that *nodea* == *nodeb*)
            '''
            if node_anchor_min[nodea] == node_anchor_max[nodea] or node_anchor_min[nodeb] == node_anchor_max[nodeb]: return None
            if node_anchor_min[nodea] < node_anchor_min[nodeb]: return True
            if node_anchor_min[nodea] > node_anchor_min[nodeb]: return False
            if node_anchor_max[nodea] > node_anchor_max[nodeb]: return True
            if node_anchor_max[nodea] < node_anchor_max[nodeb]: return False
            return None

        def next_node(test=None, value=None, values=None, extrakey=None):
            '''Iterator of all nodes in primary data order that have a
            given value for a given feature.
            Only nodes that are linked to primary data are yielded.

            Args:
                test (callable):
                    Function to test whether a node should be passed on.
                    Optional. If not present, all nodes will be passed on and the parameters
                    *value* and *values* do not have effect.

                value, values (any type, list(any type)):
                    Only effective if the parameter *test* is present.
                    The values found in *value* and *values* are collected in a dictionary.
                    All nodes node, whose *test(node)* result is in this dictionary
                    are passed on, and none of the others.

                extrakey (callable):
                    Extra key to sort nodes that do not have a defined mutual order, i.e. the nodes
                    that have equal left most anchorsand equal right most anchors.
                    With ``extrakey`` you can enforce an order on these cases.
                    The existing order between all other nodes remains the same.

            If you use an extra module that has prepared another sorting of the nodes,
            then that order will be used, instead of the order that has been created upon compiling the laf resource.
            '''

            class Extra_key(object):
                '''The initialization function of this class is a new key function for sorting nodes.

                The class wraps the node given in the initialization function into an object.
                If two node wrapping objects are compared, the comparison methods of this class
                are used. 
                Hence we can compare several bits of related information of the two nodes.
                In this case we need the minimum and maximum anchor positions associated with the nodes.

                Because Python sorting is *stable*, equal elements retain their position.
                The pre-existing order is such that nodes with equal min-max positions
                are already lumped together. 

                We only want to sort in case nodes have equal min-max anchor positions.
                So, for the sake of additional sorting, we will deem two nodes as *unequal*
                if both of their min-max positions are *different*!
                
                Hence only the lumps of nodes with equal min-max positions will be sorted. 
                '''
                __slots__ = ['value', 'amin', 'amax']
                def __init__(self, node):
                    self.amin = node_anchor_min[node] - 1
                    self.amax = node_anchor_max[node] - 1
                    self.value = extrakey(node)

                def __lt__(self, other):
                    return (
                        self.amin == other.amin and
                        self.amax == other.amax and
                        self.value < other.value
                    )
                def __gt__(self, other):
                    return (
                        self.amin == other.amin and
                        self.amax == other.amax and
                        self.value > other.value
                    )
                def __eq__(self, other):
                    return (
                        self.amin != other.amin or
                        self.amax != other.amax or
                        self.value == other.value
                    )
                __hash__ = None

            original = data_items['node_sort']
            new = data_items['node_resorted'] if 'node_resorted' in data_items else original
            given = new if new else original

            if extrakey != None:
                self.progress("Resorting {} nodes...".format(len(given)))
                given = sorted(given, key=Extra_key)
                self.progress("Done")

            if test != None:
                test_values = {}
                if value != None:
                    test_values[value] = None
                if values != None:
                    for val in values:
                        test_values[val] = None
                for node in given:
                    if test(node) in test_values:
                        yield node
            else:
                for node in given:
                    yield node

        def next_event(key=None, simplify=None):
            '''Iterator of all node events grouped by anchor.

            This iterator tries hard to achieve useful event sequences.
            The sequences coming out of this iterator can be used to
            generate open/close/suspend/resume tags corresponding to nodes.
            There are several problems to be solved concerning order and discontinuity.
            See the argument description below.

            Args:
                key (callable):
                    The key function serves two purposes: filtering and additional ordering.
                    It is optional.
                    If not present, no filtering and additional ordering will take place.
                    The key function must be a callable with one argument, it will be called
                    with a node argument.

                    If the key function returns ``None`` for a node, no node events for that
                    node will be yielded.

                    The node events are already ordered in a natural order, such that embedding
                    nodes open before embedded nodes and close after them.
                    But if two nodes have the same minimal and maximal anchor positions, the
                    order of their events is arbitrary.
                    Those node events will be sorted on the basis of the given key function.
                    The opening and resuming nodes will be ordered with the key function,
                    the closing and suspending nodes will be reverse ordered with the key.

                simplify (callable): 
                    There may be stretches of primary data that are not covered by any
                    of the nodes that pass the key filter.
                    Nodes that have gaps corresponding these uncovered ranges, 
                    will trigger suspend and resume events around them.
                    
                    If simplify is given, it should be a callable.
                    It will be passed a node, and nodes that yield True will be considered
                    in simplifying the event stream.
                    
                    If there are gaps which are not covered by any of the nodes for which the key()
                    and simplify() yield a True value, all such spurious suspending and resuming
                    of nodes around this gap will be suppressed from the node evetn stream.

            Returns:
                (anchor, events) where:
                    * anchor is the anchor position of the set of events returned
                    * events is a dictionary, keyed by event kind and valued by node lists
                where *kind* is:
                    0 meaning *start*
                    1 meaning *resume*
                    2 meaning *suspend*
                    3 meaning *end*
            '''

            class Additional_key(object):
                '''The initialization function of this class is a new key function for sorting events.

                The class wraps the node given in the initialization function into an object.
                If two node wrapping objects are compared, the comparison methods of this class
                are used. 
                Hence we can compare several bits of related information of the two nodes.
                In this case we need the minimum and maximum anchor positions associated with the nodes.

                Because Python sorting is *stable*, equal elements retain their position.
                The pre-existing order is such that nodes with equal min-max positions
                are already lumped together. 

                We only want to sort in case nodes have equal min-max anchor positions.
                So, for the sake of additional sorting, we will deem two nodes as *unequal*
                if both of their min-max positions are *different*!
                
                Hence only the lumps of nodes with equal min-max positions will be sorted. 
                '''
                __slots__ = ['value', 'kind', 'amin', 'amax']
                def __init__(self, event):
                    (node, kind) = event
                    self.amin = node_anchor_min[node] - 1
                    self.amax = node_anchor_max[node] - 1
                    self.value = key(node) * (-1 if kind < 2 else 1)
                    self.kind = kind

                def __lt__(self, other):
                    return (
                        self.amin == other.amin and
                        self.amax == other.amax and
                        (self.kind == other.kind or self.amin == self.amax) and
                        self.value < other.value
                    )
                def __gt__(self, other):
                    return (
                        self.amin == other.amin and
                        self.amax == other.amax and
                        (self.kind == other.kind or self.amin == self.amax) and
                        self.value > other.value
                    )
                def __eq__(self, other):
                    return (
                        self.amin != other.amin or
                        self.amax != other.amax or
                        (self.kind != other.kind and (self.amin != self.amax or other.amin != other.amax)) or
                        self.value == other.value
                    )
                __hash__ = None

            nodes = data_items["node_events_n"]
            kinds = data_items["node_events_k"]
            node_events = data_items["node_events"]
            node_events_items = data_items["node_events_items"]
            bufferevents = collections.deque([(-1, [])], 2)
            
            active = {}
            for anchor in range(len(node_events)):
                event_ids = self.getitems(node_events, node_events_items, anchor)
                if len(event_ids) == 0:
                    continue
                eventset = []
                for event_id in event_ids:
                    node = nodes[event_id]
                    if key == None or key(node) != None:
                        eventset.append((nodes[event_id], kinds[event_id]))
                if not eventset:
                    continue
                if key != None:
                    eventset = sorted(eventset, key=Additional_key)
                if simplify == None:
                    yield (anchor, eventset)
                    continue

                bufferevents.append([anchor, eventset])
                if bufferevents[0][0] == -1:
                    continue
                (this_anchor, these_events) = bufferevents[0]
                (next_anchor, next_events) = bufferevents[1]
                deleted = {}
                for (n, kind) in these_events:
                    if simplify(n):
                        if kind == 3:
                            deleted[n] = None
                        elif kind == 2:
                            active[n] = False
                        elif kind == 1:
                            active[n] = True
                        elif kind == 0:
                            active[n] = True
                for n in deleted:
                    if n in active:
                        del active[n]
                if True not in active.values():
                    weed = collections.defaultdict(lambda: False)
                    for (n, k) in these_events:
                        if k == 2:
                            weed[n] = None
                    for (n, k) in next_events:
                        if k == 1:
                            if n in weed:
                                weed[n] = True
                    if True in weed.values():
                        bufferevents[0][1] = [(n, k) for (n, k) in these_events if not (k == 2 and weed[n])] 
                        bufferevents[1][1] = [(n, k) for (n, k) in next_events if not (k == 1 and weed[n])] 
                yield (bufferevents[0])
            yield (bufferevents[1])

        self.progress("LOADING API: please wait ... ")

        xmlid_objects = []

        for kind in self.given['xmlids']:
            xmlid_objects.append(XMLid(self, kind))

        self.progress("P: Primary Data", verbose='INFO')
        P = PrimaryData(self) if self.given['primary'] else None

        self.progress("BF, NN, NE: Before, Next Node and Node Events", verbose='INFO')
        BF = before
        NN = next_node
        NE = next_event if self.given['primary'] else None

        self.progress("F: Features", verbose='INFO')
        F = Features(self)

        self.progress("C, Ci: Connections", verbose='INFO')
        conn = Conn(self)
        C = Connections(conn)
        Ci = Connectionsi(conn)

        self.progress("X: XML ids", verbose='INFO')
        X = XMLids(xmlid_objects)

        api = {}
        prep = lambda task, lab, myfile: self.prep_data(api, task, lab, myfile)

        self.progress("LOADING API: DONE")

        api.update({
            'infile':  self.add_input,
            'outfile': self.add_output,
            'my_file': self.result,
            'msg':     self.progress,
            'P':       P,
            'NN':      NN,
            'NE':      NE,
            'X':       X,
            'prep':    prep,
        })

        api.update({
            'Fall_node': feature_list['node'],
            'Fall_edge': feature_list['node'],
            'BF'       : before
        })
        return api

    def run(self, source, annox, task, verbose, force_compile={}, load=None, function=None, stage=None):
        '''Run a task.

        That is:
        * Load the data
        * (Re)load the task code
        * Initialize the task
        * Run the task code
        * Finalize the task

        Args:
            source (str):
                key for the source
            annox (str):
                name of the extra annotation package
            task (str):
                the chosen task
            load (dict):
                a dictionary specifying what to load
            force_compile (dict):
                whether to force (re)compilation of the LAF source for either 'source' or 'annox'.
            verbose (string): 
                verbosity level
        '''
        if stage == None or stage == 'init':
            self.check_status(source, annox, task)
            self.stamp.set_verbose(verbose)
            self.stamp.reset()
            self.compile_all(force_compile)
            self.stamp.reset()

            if load == None:
                exec("import {}".format(task))
                exec("imp.reload({})".format(task))
                load = eval("{}.load".format(task))
            self.adjust_all(load)

            if function == None:
                function = eval("{}.task".format(task))

            self.stamp.reset()

            self.init_task()

        if stage == None or stage == 'execute':
            function(self) 

        if stage == None or stage == 'final':
            self.finish_task()

    def add_output(self, file_name):
        '''Opens a file for writing and stores the handle.

        Every task is advised to use this method for opening files for its output.
        The file will be closed by LAF-Fabric when the task terminates.

        Args:
            file_name (str):
                name of the output file.
                Its location is the result directory for this task and this source.

        Returns:
            A handle to the opened file.
        '''
        result_file = "{}/{}".format(self.env['result_dir'], file_name)
        handle = open(result_file, "w", encoding="utf-8")
        self.result_files.append(handle)
        return handle

    def add_input(self, file_name):
        '''Opens a file for reading and stores the handle.

        Every task is advised to use this method for opening files for its input.
        The file will be closed by LAF-Fabric when the task terminates.

        Args:
            file_name (str):
                name of the input file.
                Its location is the result directory for this task and this source.

        Returns:
            A handle to the opened file.
        '''
        result_file = "{}/{}".format(self.env['result_dir'], file_name)
        handle = open(result_file, "r", encoding="utf-8")
        self.result_files.append(handle)
        return handle

    def result(self, file_name=None):
        '''The location where the files of this task can be found

        Args:
            file_name (str):
                the name of the file, without path information.
                Optional. If not present, returns the path to the output directory.

        Returns:
            the path to *file_name* or the directory of the output files.
        '''
        if file_name == None:
            return self.env['result_dir']
        else:
            return "{}/{}".format(self.env['result_dir'], file_name)

    def init_task(self):
        '''Initializes the current task.

        Provide a log file, reset the timer, and issue a progress message.
        '''
        self.add_logfile()
        self.stamp.reset()
        self.progress("BEGIN TASK={} SOURCE={}".format(self.env['task'], self.env['source']))

    def finish_task(self):
        '''Finalizes the current task.

        Open result files will be closed.

        There will be a progress message, and a directory listing of the result directory,
        for the convenience of the user.
        '''

        for handle in self.result_files:
            if handle and not handle.closed:
                handle.close()
        self.result_files = []

        self.progress("END TASK {}".format(self.env['task']))
        self.flush_logfile()

        msg = []
        result_dir = self.env['result_dir']
        self.progress("Results directory:\n{}".format(result_dir))
        for name in sorted(os.listdir(path=result_dir)):
            path = "{}/{}".format(result_dir, name) 
            size = os.path.getsize(path)
            mtime = time.ctime(os.path.getmtime(path))
            msg.append("{:<30} {:>12} {}".format(name, size, mtime))
        self.progress("\n".join(msg), withtime=False)

        self.finish_logfile()

    def getitems_dict(self, data, data_items, elem):
        '''Get related items from an arrayified data structure.

        If a relation between integers and sets of integers has been stored as a double array
        by the :func:`arrayify() <laf.model.arrayify>` function,
        this is the way to look up the set of related integers for each integer.

        Args:
            data (array):
                see next

            data_items (array):
                together with *data* the arrayified data

            elem (int):
                the integer for which we want its related set of integers.

        Returns:
            a dict of the related integers, with values none.
        '''
        data_items_index = data[elem]
        n_items = data_items[data_items_index]
        items = {}
        for i in range(n_items):
            items[data_items[data_items_index + 1 + i]] = None
        return items

    def getitems(self, data, data_items, elem):
        '''Get related items from an arrayified data structure.

        If a relation between integers and sets of integers has been stored as a double array
        by the :func:`arrayify() <laf.model.arrayify>` function,
        this is the way to look up the set of related integers for each integer.

        Args:
            data (array):
                see next

            data_items (array):
                together with *data* the arrayified data

            elem (int):
                the integer for which we want its related set of integers.

        Returns:
            a list of the related integers.
        '''
        data_items_index = data[elem]
        n_items = data_items[data_items_index]
        return data_items[data_items_index + 1:data_items_index + 1 + n_items]

    def hasitem(self, data, data_items, elem, item):
        '''Check whether an integer is in the set of related items
        with respect to an arrayified data structure (see also :meth:`getitems_dict`).

        Args:
            data (array):
                see next

            data_items (array):
                together with *data* the arrayified data

            elem (int):
                the integer for which we want its related set of integers.

            item (int):
                the integer whose presence in the related items set is to be tested.

        Returns:
            bool: whether the integer is in the related set or not.
        '''
        return item in self.getitems_dict(data, data_items, elem) 

    def hasitems(self, data, data_items, elem, items):
        '''Check whether a set of integers intersects with the set of related items
        with respect to an arrayified data structure (see also :meth:`getitems_dict`).

        Args:
            data (array):
                see next

            data_items (array):
                together with *data* the arrayified data

            elem (int):
                the integer for which we want its related set of integers.

            items (array or list of integers):
                the set of integers
                whose presence in the related items set is to be tested.

        Returns:
            bool:
                whether one of the integers is in the related set or not.
        '''
        these_items = self.getitems_dict(data, data_items, elem) 
        found = None
        for item in items:
            if item in these_items:
                found = item
                break
        return found

    def get_task_mtime(self, task):
        '''Get the last modification date of the file that contains the task code
        '''
        task_dir = self.settings['locations']['task_dir']
        if task_dir == '<':
            return time.time()
        else:
            return os.path.getmtime('{}/{}.py'.format(task_dir, task))

    def __del__(self):
        '''Upon destruction, all file handles used by the task will be closed.
        '''
        for handle in self.result_files:
            if handle and not handle.closed:
                handle.close()
        Laf.__del__(self)


