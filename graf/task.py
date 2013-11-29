# -*- coding: utf8 -*-

import os
import imp
import sys
import codecs
import subprocess
import collections

import array
import pickle

from graf.compiler import GrafCompiler
from graf.graf import Graf

class GrafTask(Graf):
    '''Task processor.

    A task processor must know how to compile, where the source data is and where the result is going to.
    And it must be able to *import*: and :py:func:`imp.reload`: the tasks.
    To that end the search path for modules will be adapted according to the *task_dir* setting
    in the main configuration file.
    '''

    def __init__(self, settings):
        '''Upon creation, the configuration settings are store in the object as is

        Args:
            settings (:py:class:`configparser.ConfigParser`):
                entries corresponding to the main configuration file
        '''
        Graf.__init__(self)
        self.has_compiled = False
        '''Instance member to tell whether compilation has actually taken place'''
        self.source_changed = None
        '''Instance member to tell whether the source name has changed'''
        self.annox_changed = None
        '''Instance member to tell whether the annox name has changed'''
        self.task_changed = None
        '''Instance member to tell whether the task name has changed'''
        self.settings = settings
        '''Instance member to hold configuration settings'''

        self.loaded = collections.defaultdict(lambda: collections.defaultdict(lambda: False))
        '''Set of feature data sets that have been loaded, node features and edge features under different keys'''
        self.xloaded = collections.defaultdict(lambda: False)
        '''Set of xmlid data sets that have been loaded, keys for ``node`` and ``edge``.'''
        self.result_files = []
        '''List of handles to result files created by the task through the method :meth:`add_result`'''

        cur_dir = os.getcwd()
        task_dir = self.settings['locations']['task_dir']
        task_include_dir = task_dir if task_dir.startswith('/') else '{}/{}'.format(cur_dir, task_dir)
        sys.path.append(task_include_dir)

    def __del__(self):
        '''Upon destruction, all file handles used by the task will be closed.
        '''
        for handle in self.result_files:
            if handle and not handle.closed:
                handle.close()
        Graf.__del__(self)

    def run(self, source, annox, task, force_compile=False):
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

            task:
                the chosen task

            force_compile (bool):
                whether to force (re)compilation of the LAF source
        '''
        if self.env == None:
            self.source_changed = None 
            self.annox_changed = None 
            self.task_changed = None 
        else:
            self.source_changed = self.env['source'] != source
            self.annox_changed = self.env['annox'] != annox
            self.task_changed = self.env['task'] != task

        self.stamp.reset()
        self.set_environment(source, annox, task)
        self.compile(force_compile)
        self.stamp.reset()

        exec("import {}".format(task))
        exec("imp.reload({})".format(task))

        load = eval("{}.load".format(task))
        taskcommand = eval("{}.task".format(task))

        self.loader(source, task, load)
        self.stamp.reset()

        self.init_task()
        taskcommand(self) 
        self.finish_task()

    def compile(self, force_compile):
        grafcompiler = GrafCompiler(self.env)
        grafcompiler.compiler(force=force_compile)
        self.has_compiled = grafcompiler.has_compiled
        grafcompiler = None

    def loader(self, source, task, directives):
        '''Loads compiled LAF data.

        There are two kinds of data to be loaded:

        *common data*
            Data that is common to all tasks, but dependent on the choice of source.
            It is the data that holds the regions, nodes, edges, but not the features.
            Also the original xml-ids of nodes and edges.
        *feature data*
            Data that is requested by the task at hand.
            It is the data that holds feature information,
            for those features that are requested by a task's *load['feature']* declaration.

        The *common data* can be loaded in bulk fast, but it still takes 5 to 10 seconds,
        and should be avoided if possible.
        This data only needs to be loaded if the source has changed or if compilation has taken place.
        It is taken care of by :meth:`common_loader`.

        The *feature data* is loaded and unloaded on demand
        and the feature manager method :meth:`feature_loader` takes care of that. 

        Args:
            directives (dict):
                a dictionary of information relevant to :meth:`common_loader` and :meth:`feature_loader`.

        .. note:: some directives are used by :meth:`common_loader` and some by :meth:`feature_loader`.

        '''

        self.common_loader(directives)
        self.xmlids_loader(directives)
        self.feature_loader(directives)

    def common_loader(self, directives):
        '''Manage the common data to be loaded.

        Common data is data  common to all tasks but specific to a source.

        Args:
            directives (dict):
                Currently not used.

        '''
        if self.source_changed:
            self.progress("UNLOAD ALL DATA (source changed)")
            self.init_data()
        if self.has_compiled or self.source_changed or self.source_changed == None:
            self.progress("BEGIN LOADING COMMON DATA")
            self.read_stats()
            self.feat_labels = []
            for (label, is_binary) in sorted(self.data_items_def.items()):
                if is_binary == 2: 
                    self.feat_labels.append(label)
                    continue
                data = self.data_items[label]
                b_path = "{}/{}.{}".format(self.env['bin_dir'], label, self.BIN_EXT)
                inv_label = ''
                if is_binary:
                    b_handle = open(b_path, "rb")
                    data.fromfile(b_handle, self.stats[label])
                    b_handle.close()
                else:
                    if '_xid_' in label:
                        continue

                    b_handle = open(b_path, "rb")
                    self.data_items[label] = collections.defaultdict(lambda: None, pickle.load(b_handle))
                    b_handle.close()

                    inv_label = self.inv_label(label)
                    if inv_label != None:
                        self.make_inverse(label, inv_label)
                        inv_label = '/rep'
                    else:
                        inv_label = ''
                msg = "{:<16} {:<30} {:>10}".format('loaded', label + inv_label, len(self.data_items[label]))
                self.progress(msg)
            self.progress("END   LOADING COMMON DATA")
        else:
            self.progress("COMMON DATA ALREADY LOADED")

    def xmlids_loader(self, directives):
        '''Manage the common data to be loaded.

        Loading of xml-id information.

        Args:
            directives (dict):
                dictionary specifying what to load. 
                Relevant is:
                
                directives['xmlids']:
                    booleans specifying whether xmlids should be loaded.
                    There are two keys: *node* and *edge*, because nodes and edges are handled separately.

        '''
        self.progress("BEGIN LOADING XMLID DATA")
        for (label, is_binary) in sorted(self.data_items_def.items()):
            action = 'loaded'
            if is_binary or "_xid_" not in label: 
                continue
            kind = 'node' if label.startswith('node') else 'edge'
            data = self.data_items[label]


            inv_label = ''

            is_present = self.xloaded[label] and (not self.source_changed) and self.source_changed != None
            is_needed = kind in directives['xmlids'] and directives['xmlids'][kind]
            if is_present != is_needed:
                if is_present:
                    self.init_data(xmlids=kind)
                    self.xloaded[label] = False
                    action = 'unloaded'
                else:
                    b_path = "{}/{}.{}".format(self.env['bin_dir'], label, self.BIN_EXT)
                    b_handle = open(b_path, "rb")
                    self.data_items[label] = collections.defaultdict(lambda: None, pickle.load(b_handle))
                    b_handle.close()
                    action = 'loaded'
                    self.xloaded[label] = True

                    inv_label = self.inv_label(label)
                    if inv_label != None:
                        self.make_inverse(label, inv_label)
                        inv_label = '/rep'
                    else:
                        inv_label = ''
            else:
                action = 'already loaded' if is_present else 'already unloaded'

            msg = "{:<16} {:<30} {:>10}".format(action, label + inv_label, len(self.data_items[label]))
            self.progress(msg)
        self.progress("END   LOADING XMLID DATA")

    def make_inverse(self, label, inv_label):
        '''Creates the inverse lookup table for a data table

        Args:
            label (str):
                if label ends with ``_int``, a new label will be created with ``_int`` replaced by ``_rep``.

        The data table with name *label* is a dictionary mapping string representations to integers (one-to-one).
        We create a table with the new label holding the inverse mapping, i.e. from integers back to the representations.
        '''
        self.data_items[inv_label] = dict([(y,x) for (x,y) in self.data_items[label].items()])

    def feature_loader(self, directives):
        '''Manage the feature data to be loaded.

        The specification of which features are selected is still a string.
        Here we compile it into a dictionary *only*, keyed with the qualified feature name.

        The loaded features together form a dictionary, keyed with the qualified feature name.
        The values are dictionaries keyed by the element, with as values the feature values.
        
        Args:
            directives (dict): dictionary items to load. 
                Relevant is:
                
                directives['features']:
                    strings specifying the features selected for feature loading. 
                    There are two keys: *node* and *edge*, because node features and edge features are handled separately.
        '''

        self.progress("BEGIN LOADING FEATURE DATA")
        for kind in ("node", "edge"):
            only = collections.defaultdict(lambda:collections.defaultdict(lambda:None))
            labelitems = directives['features'][kind].split(" ")

            for labelitem in labelitems:
                if not labelitem:
                    continue
                (label_rep, namestring) = labelitem.split(":")
                names = namestring.split(",")
                for name_rep in names:
                    fname = '{}.{}'.format(label_rep, name_rep)
                    only[fname] = None

            for fname in only:
                if self.check_feat_loaded(kind, fname):
                    self.progress("{} feature data for {} already loaded".format(kind, fname))
                else:
                    self.progress("{} feature data for {} loading".format(kind, fname))
                    self.load_feat(kind, fname)

            for fname in self.loaded[kind]:
                if fname not in only:
                    self.progress("{} feature data for {} unloading".format(kind, fname))
                    self.unload_feat(kind, fname)
        self.progress("END   LOADING FEATURE DATA")

    def check_xmlid_loaded(self, kind):
        '''Checks whether xmlid data for nodes or edges are loaded into memory

        Args:
            kind (str):
                kind (node or edge)

        Returns:
            True if data is in memory, otherwise False.
        '''
        return 

    def check_feat_loaded(self, kind, fname):
        '''Checks whether feature data for a specific feature is loaded in memory.

        Args:
            kind (str):
                kind (node or edge) of the feature

            fname:
                the qualified name of the feature.

        Returns:
            True if data is in memory, otherwise False.
        '''
        return self.loaded[kind][fname] and (not self.source_changed) and self.source_changed != None

    def load_feat(self, kind, fname):
        ''' Loads selected feature into memory.

        Args:
            kind (str):
                kind (node or edge) of the feature

            fname:
                the qualified name of the feature.
        '''
        found = True
        for label in self.feat_labels:
            absolute_feat_path = "{}/{}_{}_{}.{}".format(self.env['feat_dir'], label, kind, fname, self.BIN_EXT)
            try:
                p_handle = open(absolute_feat_path, "rb")
                self.data_items[label][kind][fname].fromfile(p_handle, self.stats['{}_{}_{}'.format(label, kind, fname)])
            except:
                found = False
            self.loaded[kind][fname] = True
        if not found: 
            self.progress("WARNING: {} feature {} not found in this source".format(kind, fname))
        this_feat_ref = self.data_items['feat_ref'][kind][fname]
        this_feat_value = self.data_items['feat_value'][kind][fname]

        dest = self.node_feat if kind == 'node' else self.edge_feat
        i = -1
        for ref in this_feat_ref:
            i += 1
            dest[fname][ref] = this_feat_value[i]
        for label in self.feat_labels:
            self.init_data(feature=(kind, fname))

    def unload_feat(self, kind, fname):
        ''' Unloads selected feature from memory.

        Args:
            kind (str):
                kind (node or edge) of the feature

            fname:
                the qualified name of the feature.
        '''
        dest = self.node_feat if kind == 'node' else self.edge_feat
        for label in self.feat_labels:
            self.init_data((kind, fname))
        if fname in dest:
            del dest[fname]
        self.loaded[kind][fname] = False

    def add_result(self, file_name):
        '''Opens a file for writing and stores the handle.

        Every task is advised to use this method for opening files for its output.
        The file will be closed by the workbench when the task terminates.

        Args:
            file_name (str):
                name of the output file.

            Its location is the result directory for this task and this source.

        Returns:
            A handle to the opened file.
        '''
        result_file = "{}/{}".format(
            self.env['result_dir'], file_name
        )
        handle = codecs.open(result_file, "w", encoding = 'utf-8')
        self.result_files.append(handle)
        return handle

    def init_task(self):
        '''Initializes the current task.

        Very trivial initialization: just issue a progress message.
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

        msg = subprocess.check_output("ls -lh {}".format(self.env['result_dir']), shell=True)
        self.progress("\n" + msg.decode('utf-8'))

        msg = subprocess.check_output("du -h {}".format(self.env['result_dir']), shell=True)
        self.progress("\n" + msg.decode('utf-8'))
        self.finish_logfile()

    def get_node_feature_value(self, node, fname):
        '''Node feature value lookup returning the internal integer representation.
        ''' 
        return self.node_feat[fname][node]

    def get_edge_feature_value(self, edge, fname):
        '''Edge feature value lookup returning the internal integer representation.
        ''' 
        return self.edge_feat[fname][edge]

    def next_node(self):
        '''API: iterator of all nodes in primary data order.

        Each call *yields* the next node. The iterator walks through all nodes.
        The order is implied by the attachment of nodes to the primary data,
        which is itself linearly ordered.
        This order is explained in the :ref:`guidelines for task writing <node-order>`.
        '''
        for node in self.data_items["node_sort"]:
            yield node

    def next_node_with_fval(self, fname, value):
        '''API: iterator of all nodes in primary data order that have a
        given value for a given feature.

        See also :meth:`next_node`.

        Args:
            name (int):
                the code of a feature name

            value (int):
                the code of a feature value
        '''
        for node in self.data_items["node_sort"]:
            if value == self.node_feat[fname][node]:
                yield node

    def next_node(self):
        '''API: iterator of all nodes in primary data order.

        Each call *yields* the next node. The iterator walks through all nodes.
        The order is implied by the attachment of nodes to the primary data,
        which is itself linearly ordered.
        This order is explained in the :ref:`guidelines for task writing <node-order>`.
        '''
        for node in self.data_items["node_sort"]:
            yield node

    def int_node_xid(self, rep):
        '''API: *xml node id* conversion from string representation as found in LAF resource
        to corresponding integer as used in compiled resource.
        '''
        return self.data_items["node_xid_int"][rep]

    def rep_node_xid(self, intl):
        '''API: *xml node id* conversion from integer code as used in compiled LAF resource
        to corresponding string representation as found in original LAF resource.
        '''
        return self.data_items["node_xid_rep"][intl]

    def int_edge_xid(self, rep):
        '''API: *xml edge id* conversion from string representation as found in LAF resource
        to corresponding integer as used in compiled resource.
        '''
        return self.data_items["edge_xid_int"][rep]

    def rep_edge_xid(self, intl):
        '''API: *xml edge id* conversion from integer code as used in compiled LAF resource
        to corresponding string representation as found in original LAF resource.
        '''
        return self.data_items["edge_xid_rep"][intl]

    def int_fval(self, rep):
        '''API: *feature value* conversion from string representation as found in LAF resource
        to corresponding integer as used in compiled resource.
        '''
        return self.data_items["feat_value_list_int"][rep]

    def rep_fval(self, intl):
        '''API: *feature value* conversion from integer code as used in compiled LAF resource
        to corresponding string representation as found in original LAF resource.
        '''
        return self.data_items["feat_value_list_rep"][intl]

    def get_mappings(self):
        '''Return references to API methods of this class.

        The caller can give convenient, local names to these methods.
        It also saves method lookup,
        at least, I think so.
        ''' 
        return (
            self.progress,
            self.data_items["feat_value_list_int"],
            self.data_items["feat_value_list_rep"],
            self.next_node,
            self.next_node_with_fval,
            self.get_node_feature_value,
            self.get_edge_feature_value,
            self.data_items["node_xid_int"],
            self.data_items["node_xid_rep"],
            self.data_items["edge_xid_int"],
            self.data_items["edge_xid_rep"],
        )

    def getitems(self, data, data_items, elem):
        '''Get related items from an arrayified data structure.

        If a relation between integers and sets of integers has been stored as a double array
        by the :func:`arrayify() <graf.model.arrayify>` function,
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
        data_items_index = data[elem - 1]
        n_items = data_items[data_items_index]
        items = {}
        for i in range(n_items):
            items[data_items[data_items_index + 1 + i]] = None
        return items

    def hasitem(self, data, data_items, elem, item):
        '''Check whether an integer is in the set of related items
        with respect to an arrayified data structure (see also :meth:`getitems`).

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
        return item in self.getitems(data, data_items, elem) 

    def hasitems(self, data, data_items, elem, items):
        '''Check whether a set of integers intersects with the set of related items
        with respect to an arrayified data structure (see also :meth:`getitems`).

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
        these_items = self.getitems(data, data_items, elem) 
        found = None
        for item in items:
            if item in these_items:
                found = item
                break
        return found

