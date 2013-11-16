# -*- coding: utf8 -*-

import os
import codecs
import subprocess
import collections

import array
import cPickle

from compiler import GrafCompiler
from graf import Graf

edge_prop = {}
node_prop = {}

class GrafTask(Graf):
    '''Task processor.

    A task processor must know how to compile, where the source data is and where the result is going to.
    '''

    result_files = []
    '''List of handles to result files created by the task through the method :meth:`add_result`'''

    force = False

    def __init__(self, source, task, settings):
        '''Upon creation, information is passed and stored about locations.

        Args:
            source (str): key for the source
            task: the chosen task
            settings (dict): the parsed contents of the main configuration file
        '''

        Graf.__init__(self)
        self.set_environment(source, task, settings)
        self.add_logfile()
        self.progress("INITIALIZATION TASK={} SOURCE={}".format(env['task'], env['source']))

        grafcompiler = GrafCompiler(env)
        grafcompiler = None

    def __del__(self):
        '''Upon destruction, all file handles used by the task will be closed.
        '''

        for handle in self.result_files:
            if handle and not handle.closed:
                handle.close()
        Graf.__del__(self)


    def setup(self, directives):
        '''Set up everything that is needed to run a task.
        That is: load the compiled data, take in the features declared by the task, and initialize the task itself.

        Args:
            directives (dict): a dictionary of information items, i.e. the list of declare features. This information is read from the chosen task (the *features* dictionary).
        '''
        self.loader(directives)
        self.init_task()

    def loader(self, directives):
        '''Loads compiled LAF data.

        After this loading, the feature manager method (:meth:`fmanager`) is executed. 

        Args: directives (dict): a dictionary of information relevant to loader and fmanager.

        .. note:: directives are only used by the fmanager.

        '''

        self.progress("BEGIN LOADING")
        self.read_stats()
        for (label, info) in sorted(self.data_items.items()):
            (is_binary, data) = info 
            b_path = "{}/{}.{}".format(self.env['bin_dir'], label, self.BIN_EXT)
            msg = "loaded {:<30} ... ".format(label)
            b_handle = open(b_path, "rb")
            if is_binary:
                data.fromfile(b_handle, self.stats[label])
            else:
                self.data_items[label][1] = collections.defaultdict(lambda: None,cPickle.load(b_handle))
            msg += u"{:>10}".format(len(self.data_items[label][1]))
            b_handle.close()
            self.progress(msg)
        self.progress("END LOADING")
        self.nodes = directives['nodes'] if 'nodes' in directives else None
        self.edges = directives['edges'] if 'edges' in directives else None
        self.assemble("node", "node_feat", "node_feat_items", node_prop, self.nodes)
        self.assemble("edge", "edge_feat", "edge_feat_items", edge_prop, self.edges)
        self.progress("END ASSEMBLING")

    def assemble(self, kind, lsource_feat, lsource_feat_items, dest, onlystring):
        '''Manage the feature data to be loaded.

        The specification of which features are selected is still a string.
        Here we compile it into a dictionary *only*, keyed with the feature label and then the feature name.

        The loaded features together forms a dictionary, keyed with the extended feature name.
        The values are dictionaries keyed by the element, with as values the feature values.
        
        Args:
            kind (str): indication whether nodes or edges are considered. Only used for progress and log messages.
            lsource_feat (array): see below
            lsource_feat_items (array): together with *lsource_feat* the array data for the feature set to be loaded
            dest (dict): the destination dictionary for the overall feature data
            onlystring (str): string specifying the features selected for feature loading
        '''
        self.progress("LOADING REQUESTED {} FEATURES ... ".format(kind))

        only = collections.defaultdict(lambda:collections.defaultdict(lambda:None))
        labelitems = onlystring.split(" ")

        do_indexing = False
        for labelitem in labelitems:
            (label_rep, namestring) = labelitem.split(":")
            names = namestring.split(",")
            for name_rep in names:
                name = self.int_fname(name_rep)
                if label == None or name == None:
                    self.progress("WARNING: {} feature {}.{} not encountered in this source".format(kind, label_rep, name_rep))
                    continue
                only[label][name] = None
                if self._needs_indexing(kind, label, name):
                    do_indexing = True

        if do_indexing:
            self.progress("PRECOMPUTING FEATURE VALUES ...")
            feat_label = self.data_items["feat_label"][1]
            feat_name = self.data_items["feat_name"][1]
            feat_value = self.data_items["feat_value"][1]
            source = self.data_items[lsource_feat][1]
            source_items = self.data_items[lsource_feat_items][1]
            elem = 0
            for to_items in source:
                elem += 1
                n_items = source_items[to_items]
                for i in range(n_items):
                    feat = source_items[to_items + 1 + i]
                    label = feat_label[feat - 1]
                    if label not in only:
                        continue
                    name = feat_name[feat - 1]
                    if name not in only[label]:
                        continue
                    if label not in dest:
                        dest[label] = {}
                    if name not in dest[label]:
                        dest[label][name] = {}
                    dest[label][name][elem] = feat_value[feat - 1]
            self.progress("SAVING FEATURE VALUES TO DISK ...")
            self._save_index(kind, only, dest)
        else:
            self.progress("LOADING FEATURE VALUES FROM DISK ...")
            self._load_index(kind, only, dest)

    def _load_index(self, kind, only, dest):
        '''Load all computed indexes from disk

        Args:
            kind (str): indication whether nodes or edges are considered. Only used for progress and log messages.
            only (dict): dictionary specifying the index selection
            dest (dict): the index material
        '''
        for label in only:
            for name in only[label]:
                index_file = self._index_file(kind, label, name)
                self.progress("loading {}".format(os.path.basename(index_file)))
                p_handle = open(index_file, "rb")
                if label not in dest:
                    dest[label] = {}
                dest[label][name] = cPickle.load(p_handle)

    def _index_file(self, kind, label, name):
        '''Compute the file path of the index for the feature with *name* and *label*.
        '''
        return "{}/index_{}_{}.bin".format(self.env['bin_dir'], kind, self.rep_fname(name))

    def _needs_indexing(self, kind, label, name):
        '''Determine whether the index for the feature with *name* and *label* exists and is up to date.

        Up to date means that the index is newer than the compiled LAF resource.
        Every compiled LAF resource has a statistics file, and its modification time is used as reference.
        So if you *touch* that file, all indexes will be recomputed. But you can also pass the ``--force-index`` flag.

        .. note:: Rebuilding the index.
            There is a difference however. If you say ``--force-index`` when issuing a task, only indexes used by that task 
            will be rebuilt.

            If you *touch* the compiled statistics file, every task will recompute its indexes until all indexes have been rebuilt.
        '''

        index_file = self._index_file(kind, label, name)
        return not os.path.exists(index_file) or os.path.getmtime(index_file) < os.path.getmtime(self.env['stat_file'])

    def add_result(self, file_name):
        '''Opens a file for writing and stores the handle.

        Every task is advised to use this method for opening files for its output.
        The file will be closed by the workbench when the task terminates.

        Args:
            file_name (str): name of the output file. Its location is the result directory for this task and this source.
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
        self.progress("BEGIN TASK {}".format(self.env['task']))

    def finish_task(self):
        '''Finalizes the current task.

        There will be a progress message, and a directory listing of the result directory, for the convenience of the user.
        '''

        self.progress("END TASK {}".format(self.env['task']))

        msg = subprocess.check_output("ls -lh {}".format(self.env['result_dir']), shell=True)
        self.progress("\n" + msg)

        msg = subprocess.check_output("du -h {}".format(self.env['result_dir']), shell=True)
        self.progress("\n" + msg)

    def Fi(self, node, label, name):
        '''Feature value lookup returning the value string representation.
        ''' 
        return node_prop[label][name][node]

    def Fr(self, node, label, name):
        '''Feature value lookup returning the value string representation.
        See method :meth:`Fi()`.
        ''' 
        feat_value_list_int = self.data_items["feat_value_list_int"][1]
        return feat_value_list_int[node_prop[label][name][node]]

    def next_node(self):
        '''API: iterator of all nodes in primary data order.

        Each call returns the next node. The iterator walks through all nodes.
        The order is implied by the attachment of nodes to the primary data, which is itself linearly ordered.
        This order is explained in the :ref:`guidelines for task writing <node-order>`.
        '''
        for node in self.data_items["node_sort"][1]:
            yield node

    def next_node_with_fval(self, label, name, value):
        '''API: iterator of all nodes in primary data order that have a given value for a given feature.

        See also :meth:`next_node`.

        Args:
            label (int): the code of an annotation label
            name (int): the code of a feature name
            value (int): the code of a feature value
        '''
        for node in self.data_items["node_sort"][1]:
            if value == self.Fi(node, label, name):
                yield node

    def next_node(self):
        '''API: iterator of all nodes in primary data order.

        Each call returns the next node. The iterator walks through all nodes.
        The order is implied by the attachment of nodes to the primary data, which is itself linearly ordered.
        This order is explained in the :ref:`guidelines for task writing <node-order>`.
        '''
        for node in self.data_items["node_sort"][1]:
            yield node

    def next_node_with_fval(self, label, name, value):
        '''API: iterator of all nodes in primary data order that have a given value for a given feature.

        See also :meth:`next_node`.

        Args:
            label (int): the code of an annotation label
            name (int): the code of a feature name
            value (int): the code of a feature value
        '''
        for node in self.data_items["node_sort"][1]:
            if value == self.Fi(node, label, name):
                yield node

    def int_fname(self, rep):
        '''API: *feature name* conversion from string representation as found in LAF resource to corresponding integer as used in compiled resource.
        '''
        return self.data_items["feat_name_list_rep"][1][rep]

    def int_fval(self, rep):
        '''API: *feature value* conversion from string representation as found in LAF resource to corresponding integer as used in compiled resource.
        '''
        return self.data_items["feat_value_list_rep"][1][rep]

    def rep_fname(self, intl):
        '''API: *feature name* conversion from integer code as used in compiled LAF resource to corresponding string representation as found in original LAF resource.
        '''
        return self.data_items["feat_name_list_int"][1][intl]

    def rep_fval(self, intl):
        '''API: *feature value* conversion from integer code as used in compiled LAF resource to corresponding string representation as found in original LAF resource.
        '''
        return self.data_items["feat_value_list_int"][1][intl]

    def get_mappings(self):
        '''Return references to API methods of this class.

        The caller can give convenient, local names to these methods. It also saves method lookup,
        at least, I think so.
        ''' 
        return (
            self.progress,
            self.data_items["feat_name_list_rep"][1],
            self.data_items["feat_name_list_int"][1],
            self.data_items["feat_value_list_rep"][1],
            self.data_items["feat_value_list_int"][1],
            self.next_node,
            self.next_node_with_fval,
            self.Fi,
            self.Fr,
        )

    def getitems(self, data, data_items, elem):
        '''Get related items from an arrayified data structure.
        If a relation between integers and sets of integers has been stored as a double array by the :func:`arrayify() <graf.model.arrayify>` function, this is the way to look up the set of related integers for each integer.

        Args:
            data (array): see next
            data_items (array): together with *data* the arrayified data
            elem (int): the integer for which we want its related set of integers.
        '''
        data_items_index = data[elem - 1]
        n_items = data_items[data_items_index]
        items = {}
        for i in range(n_items):
            items[data_items[data_items_index + 1 + i]] = None
        return items

    def hasitem(self, data, data_items, elem, item):
        '''Check whether an integer is in the set of related items with respect to an arrayified data structure (see also :meth:`getitems`).

        Args:
            data (array): see next
            data_items (array): together with *data* the arrayified data
            elem (int): the integer for which we want its related set of integers.
            item (int): the integer whose presence in the related items set is to be tested.
        '''
        return item in self.getitems(data, data_items, elem) 

    def hasitems(self, data, data_items, elem, items):
        '''Check whether a set of integers intersects with the set of related items with respect to an arrayified data structure (see also :meth:`getitems`).

        Args:
            data (array): see next
            data_items (array): together with *data* the arrayified data
            elem (int): the integer for which we want its related set of integers.
            items (array or list of integers): the set of integers whose presence in the related items set is to be tested.
        '''
        these_items = self.getitems(data, data_items, elem) 
        found = None
        for item in items:
            if item in these_items:
                found = item
                break
        return found

