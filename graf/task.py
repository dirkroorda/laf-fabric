# -*- coding: utf8 -*-

import os
import sys
import codecs
import subprocess
import collections

import array
import cPickle

from compiler import GrafCompiler
from graf import Graf

class GrafTask(Graf):
    '''Task processor.

    A task processor must know how to compile, where the source data is and where the result is going to.
    And it must be able to *import*: and :py:func:`reload`: the tasks.
    To that end the search path for modules will be adapted according to the *task_dir* setting
    in the main configuration file.
    '''

    loaded = collections.defaultdict(lambda: collections.defaultdict(lambda: False))
    '''Set of feature data sets that have been loaded, node features and edge features under different keys'''
    result_files = []
    '''List of handles to result files created by the task through the method :meth:`add_result`'''

    def __init__(self, settings):
        '''Upon creation, the configuration settings are store in the object as is

        Args:
            settings (:py:class:`ConfigParser.ConfigParser`): entries corresponding to the main configuration file
        '''
        Graf.__init__(self)
        self.has_compiled = False
        '''Instance member to tell whether compilation has actually taken place'''
        self.source_changed = None
        '''Instance member to tell whether the source name has changed'''
        self.task_changed = None
        '''Instance member to tell whether the task name has changed'''
        self.settings = settings
        '''Instance member to hold configuration settings'''

        cur_dir = os.getcwd()
        task_dir = self.settings.get('locations', 'task_dir')
        task_include_dir = task_dir if task_dir.startswith('/') else '{}/{}'.format(cur_dir, task_dir)
        sys.path.append(task_include_dir)

    def __del__(self):
        '''Upon destruction, all file handles used by the task will be closed.
        '''
        for handle in self.result_files:
            if handle and not handle.closed:
                handle.close()
        Graf.__del__(self)

    def run(self, source, task, force_compile=False):
        '''Run a task.

        That is:
        * Load the data
        * (Re)load the task code
        * Initialize the task
        * Run the task code
        * Finalize the task

        Args:
            source (str): key for the source
            task: the chosen task
            force_compile (bool): whether to force (re)compilation of the LAF source
        '''
        if self.env == None:
            self.source_changed = None 
            self.task_changed = None 
        else:
            if self.env['source'] != source:
                self.source_changed = True 
            else:
                self.source_changed = False
            if self.env['task'] != task:
                self.task_changed = True 
            else:
                self.task_changed = False

        self.stamp.reset()
        self.set_environment(source, task)
        self.add_logfile()
        self.progress("INITIALIZATION TASK={} SOURCE={}".format(self.env['task'], self.env['source']))

        self.compile(force_compile)

        self.stamp.reset()

        exec("import {}".format(task))
        exec("reload({})".format(task))

        features = eval("{}.features".format(task))
        taskcommand = eval("{}.task".format(task))

        self.loader(source, task, features)
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
        *feature data*
            Data that is requested by the task at hand.
            It is the data that holds feature information,
            for those features that are requested by a task's *feature* declaration.

        The *common data* can be loaded in bulk fast, but it still takes 5 to 10 seconds,
        and should be avoided if possible.
        This data only needs to be loaded if the source has changed or if compilation has taken place.
        It is taken care of by :meth:`common_loader`.

        The *feature data* is loaded and unloaded on demand
        and the feature manager method :meth:`feature_loader` takes care of that. 

        Args:
            directives (dict): a dictionary of information
            relevant to :meth:`common_loader` and :meth:`feature_loader`.

        .. note:: directives are only used by :meth:`feature_loader`.

        '''

        self.common_loader(source)
        self.feature_loader(directives)

    def common_loader(self, source):
        '''Manage the common data to be loaded.

        Common data is data  common to all tasks but specific to a source.
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
                msg = "loaded {:<30} ... ".format(label)
                b_handle = open(b_path, "rb")
                if is_binary:
                    data.fromfile(b_handle, self.stats[label])
                else:
                    self.data_items[label] = collections.defaultdict(lambda: None,cPickle.load(b_handle))
                msg += u"{:>10}".format(len(self.data_items[label]))
                b_handle.close()
                self.progress(msg)
            self.progress("END   LOADING COMMON DATA")
        else:
            self.progress("COMMON DATA ALREADY LOADED")

    def feature_loader(self, directives):
        '''Manage the feature data to be loaded.

        The specification of which features are selected is still a string.
        Here we compile it into a dictionary *only*, keyed with the extended feature name.

        The loaded features together form a dictionary, keyed with the extended feature name.
        The values are dictionaries keyed by the element, with as values the feature values.
        
        Args:
            directives (dict): dictionary of strings string specifying the features selected for feature loading. 
                There are two keys: *node* and *edge*, because node features and edge features are handled separately.
        '''

        self.progress("BEGIN LOADING FEATURE DATA")
        for kind in ("node", "edge"):
            only = collections.defaultdict(lambda:collections.defaultdict(lambda:None))
            labelitems = directives[kind].split(" ")
            feature_name_rep = self.data_items["feat_name_list_{}_rep".format(kind)]

            for labelitem in labelitems:
                if not labelitem:
                    continue
                (label_rep, namestring) = labelitem.split(":")
                names = namestring.split(",")
                for name_rep in names:
                    fname_rep = u'{}.{}'.format(label_rep, name_rep)
                    fname = feature_name_rep[fname_rep]
                    if fname == None:
                        self.progress("WARNING: {} feature {}.{} not encountered in this source".format(kind, label_rep, fname_rep))
                        continue
                    only[fname_rep] = None

            for fname_rep in only:
                fname = feature_name_rep[fname_rep]
                if self.check_feat_loaded(kind, fname_rep):
                    self.progress("{} feature data for {} already loaded".format(kind, fname_rep))
                else:
                    self.progress("{} feature data for {} loading".format(kind, fname_rep))
                    self.load_feat(kind, fname_rep)

            for fname_rep in self.loaded[kind]:
                fname = feature_name_rep[fname_rep]
                if fname_rep not in only:
                    self.progress("{} feature data for {} unloading".format(kind, fname_rep))
                    self.unload_feat(kind, fname_rep)
        self.progress("END   LOADING FEATURE DATA")

    def check_feat_loaded(self, kind, fname_rep):
        '''Checks whether feature data for a specific feature is loaded in memory.

        Args:
            kind (str): kind (node or edge) of the feature
            fname_rep: the qualified name of the feature.

        Returns:
            True if data is in memory, otherwise False.
        '''
        return self.loaded[kind][fname_rep] and (not self.source_changed) and self.source_changed != None

    def load_feat(self, kind, fname_rep):
        ''' Loads selected feature into memory.

        Args:
            kind (str): kind (node or edge) of the feature
            fname_rep: the qualified name of the feature.
        '''
        feature_name_rep = self.data_items["feat_name_list_{}_rep".format(kind)]
        fname = feature_name_rep[fname_rep]
        for label in self.feat_labels:
            absolute_feat_path = "{}/{}_{}_{}.{}".format(self.env['feat_dir'], label, kind, fname_rep, self.BIN_EXT)
            p_handle = open(absolute_feat_path, "rb")
            self.data_items[label][kind][fname].fromfile(p_handle, self.stats[u'{}_{}_{}'.format(label, kind, fname)])
            self.loaded[kind][fname_rep] = True
        this_feat_ref = self.data_items['feat_ref'][kind][fname]
        this_feat_value = self.data_items['feat_value'][kind][fname]

        dest = self.node_feat if kind == 'node' else self.edge_feat
        i = -1
        for ref in this_feat_ref:
            i += 1
            dest[fname][ref] = this_feat_value[i]
        for label in self.feat_labels:
            self.init_data(feature=(kind, fname))

    def unload_feat(self, kind, fname_rep):
        ''' Unloads selected feature from memory.

        Args:
            kind (str): kind (node or edge) of the feature
            fname_rep: the qualified name of the feature.
        '''
        feature_name_rep = self.data_items["feat_name_list_{}_rep".format(kind)]
        fname = feature_name_rep[fname_rep]
        dest = self.node_feat if kind == 'node' else self.edge_feat
        for label in self.feat_labels:
            self.init_data((kind, fname))
        if fname in dest:
            del dest[fname]
        self.loaded[kind][fname_rep] = False

    def add_result(self, file_name):
        '''Opens a file for writing and stores the handle.

        Every task is advised to use this method for opening files for its output.
        The file will be closed by the workbench when the task terminates.

        Args:
            file_name (str): name of the output file.
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
        self.progress("BEGIN TASK {}".format(self.env['task']))

    def finish_task(self):
        '''Finalizes the current task.

        There will be a progress message, and a directory listing of the result directory,
        for the convenience of the user.
        '''

        self.progress("END TASK {}".format(self.env['task']))

        msg = subprocess.check_output("ls -lh {}".format(self.env['result_dir']), shell=True)
        self.progress("\n" + msg)

        msg = subprocess.check_output("du -h {}".format(self.env['result_dir']), shell=True)
        self.progress("\n" + msg)

    def FNi(self, node, name):
        '''Node feature value lookup returning the value string representation.
        ''' 
        return self.node_feat[name][node]

    def FNr(self, node, name):
        '''Node feature value lookup returning the value string representation.
        See method :meth:`FNi()`.
        ''' 
        feat_value_list_int = self.data_items["feat_value_list_int"]
        return feat_value_list_int[self.node_feat[name][node]]

    def FEi(self, edge, name):
        '''Edge feature value lookup returning the value string representation.
        ''' 
        return self.edge_feat[name][edge]

    def FEr(self, edge, name):
        '''Edge feature value lookup returning the value string representation.
        See method :meth:`FEi()`.
        ''' 
        feat_value_list_int = self.data_items["feat_value_list_int"]
        return feat_value_list_int[self.edge_feat[name][edge]]

    def next_node(self):
        '''API: iterator of all nodes in primary data order.

        Each call *yields* the next node. The iterator walks through all nodes.
        The order is implied by the attachment of nodes to the primary data,
        which is itself linearly ordered.
        This order is explained in the :ref:`guidelines for task writing <node-order>`.
        '''
        for node in self.data_items["node_sort"]:
            yield node

    def next_node_with_fval(self, name, value):
        '''API: iterator of all nodes in primary data order that have a
        given value for a given feature.

        See also :meth:`next_node`.

        Args:
            name (int): the code of a feature name
            value (int): the code of a feature value
        '''
        for node in self.data_items["node_sort"]:
            if value == self.FNi(node, name):
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

    def int_fname_node(self, rep):
        '''API: *feature name* (on nodes) conversion from string representation as found in LAF resource
        to corresponding integer as used in compiled resource.
        '''
        return self.data_items["feat_name_list_node_rep"][rep]

    def int_fname_edge(self, rep):
        '''API: *feature name* (on edges) conversion from string representation as found in LAF resource
        to corresponding integer as used in compiled resource.
        '''
        return self.data_items["feat_name_list_edge_rep"][rep]

    def int_fval(self, rep):
        '''API: *feature value* conversion from string representation as found in LAF resource
        to corresponding integer as used in compiled resource.
        '''
        return self.data_items["feat_value_list_rep"][rep]

    def rep_fname_node(self, intl):
        '''API: *feature name* (on nodes) conversion from integer code as used in compiled LAF resource
        to corresponding string representation as found in original LAF resource.
        '''
        return self.data_items["feat_name_list_node_int"][intl]

    def rep_fname_edge(self, intl):
        '''API: *feature name* (on edges) conversion from integer code as used in compiled LAF resource
        to corresponding string representation as found in original LAF resource.
        '''
        return self.data_items["feat_name_list_edge_int"][intl]

    def rep_fval(self, intl):
        '''API: *feature value* conversion from integer code as used in compiled LAF resource
        to corresponding string representation as found in original LAF resource.
        '''
        return self.data_items["feat_value_list_int"][intl]

    def get_mappings(self):
        '''Return references to API methods of this class.

        The caller can give convenient, local names to these methods.
        It also saves method lookup,
        at least, I think so.
        ''' 
        return (
            self.progress,
            self.data_items["feat_name_list_node_rep"],
            self.data_items["feat_name_list_node_int"],
            self.data_items["feat_name_list_edge_rep"],
            self.data_items["feat_name_list_edge_int"],
            self.data_items["feat_value_list_rep"],
            self.data_items["feat_value_list_int"],
            self.next_node,
            self.next_node_with_fval,
            self.FNi,
            self.FNr,
            self.FEi,
            self.FEr,
        )

    def getitems(self, data, data_items, elem):
        '''Get related items from an arrayified data structure.

        If a relation between integers and sets of integers has been stored as a double array
        by the :func:`arrayify() <graf.model.arrayify>` function,
        this is the way to look up the set of related integers for each integer.

        Args:
            data (array): see next
            data_items (array): together with *data* the arrayified data
            elem (int): the integer for which we want its related set of integers.

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
            data (array): see next
            data_items (array): together with *data* the arrayified data
            elem (int): the integer for which we want its related set of integers.
            item (int): the integer whose presence in the related items set is to be tested.

        Returns:
            bool: whether the integer is in the related set or not.
        '''
        return item in self.getitems(data, data_items, elem) 

    def hasitems(self, data, data_items, elem, items):
        '''Check whether a set of integers intersects with the set of related items
        with respect to an arrayified data structure (see also :meth:`getitems`).

        Args:
            data (array): see next
            data_items (array): together with *data* the arrayified data
            elem (int): the integer for which we want its related set of integers.
            items (array or list of integers): the set of integers
            whose presence in the related items set is to be tested.

        Returns:
            bool: whether one of the integers is in the related set or not.
        '''
        these_items = self.getitems(data, data_items, elem) 
        found = None
        for item in items:
            if item in these_items:
                found = item
                break
        return found

