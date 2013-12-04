# -*- coding: utf8 -*-

import os
import os.path
import codecs
import collections

import array
import pickle


from graf.timestamp import Timestamp

class GrafException(Exception):
    def __init__(self, message, stamp, Errors):
        Exception.__init__(self, message)
        stamp.progress(message)
        raise

class Graf(object):
    '''Base class for compiling LAF resources and running analytic tasks on them.

    The data of this class represents the compiled data on the basis of which tasks can run.
    This data is created by a :class:`GrafCompiler <graf.compiler.GrafCompiler>` that derives from this class.

    The :class:`Graf` knows the structure of the data, and how to load it into memory.
    It can also see what it loaded and what not, and it can compute conditions that require compiling and (re)loading.
    '''

    BIN_EXT = 'bin'
    '''extension for binary files
    '''
    TEXT_EXT = 'txt'
    '''extension for text files
    '''
    LOG_NAME = '__log__'
    '''log file base name for a task
    '''
    STAT_NAME = '__stat__'
    '''statistics file base name for a task
    '''
    COMPILE_TASK = 'compile'
    '''name of the compile task
    '''


    def __init__(self):
        '''Upon creation, empty datastructures are initialized to hold the binary,
        compiled LAF data and create a directory for their serializations on disk.

        The Graf object holds information that Graf tasks need to perform their operations.
        The most important piece of information is the data itself.
        This data consists of arrays and dictionaries that together hold the information that is compiled from a LAF resource.

        Other things that happen: 

        #. a fresh Timestamp object is created, which records the current time and can issue progress messages containing the amount
           of time that has elapsed since this object has been created.
        #. if the directory that should hold the compiled data does not exist,
           a new directory is created Of course this means that before executing any tasks,
           the LAF resource has to be (re)compiled. 

        Returns:
            object with data structures initialized, ready to load the compiled data from disk.
        '''

        self.stamp = Timestamp()
        '''Instance member holding the :class:`Timestamp <graf.timestamp.Timestamp>` object.
           Useful to deliver progress messages with timing information.
        '''
        self.env = None
        '''Holds the context information for the current task, such as chosen source and task.
        '''
        self.log = None
        '''handle of a log file, usually open for writing. Used for the log of the compilation process
        and of the task executions.
        '''

        self.data_items_def = collections.OrderedDict([
            ("xid", ('x_mapping', 'xmlids')),
            ("region_begin", ('array', 'common')),
            ("region_end", ('array', 'common')),
            ("node_region", ('double_array', 'common')),
            ("node_sort", ('array', 'common')),
            ("node_out", ('double_array', 'common')),
            ("node_in", ('double_array', 'common')),
            ("edges_from", ('array', 'common')),
            ("edges_to", ('array', 'common')),
            ("feature", ('feature_mapping', 'feature')),
        ])

        '''There are various kinds of data, by their shape and by their function.
        The instance member *data_items_def* contains their declarations in the
        form of an ordered dictionary, keyed by labels and with a tuple of data type and data group
        as values.

        The instance member *data_items* contains the data itself.

        The types of data are

        ``x_mapping``, group ``xmlids``:
            mappings between xml identifiers as they occur in the original LAF source
            and the node/edge numbers in the compiled data.
            There are two dictionaries: ``xid_int`` (going from xml to integer) and
            ``xid_rep`` (going from integer to xml).
            Both contain two dictionaries, one for nodes and one for edges separately.

        ``array``, group ``common``:
            Simply tables of integer values. 
            Most of the data common to all tasks is in ``array`` s and ``double_array`` s (see below).

            ``region_begin`` and ``region_end``:
                At position ``i``: the start and end anchors for region ``i``.

            ``node_sort``:
                All nodes ordered as induced by the region anchors.
                Nodes that start before others, come before them, 
                nodes that have equal start points are ordered such that the one with the later end point
                comes first. If both have equal end points, the order is arbitrary.
                If the nodes correspond to objects in a hierarchy without gaps, then embedding objects come before
                embedded objects.
                
            ``edges_from`` and ``edges_to``:
                At position ``i``: the source and the target of edge ``i``.

        ``double_array``, group ``common``: 
            Twin arrays representing a list of records where records may have variable length.
            The primary array is has the name given, and contains at position ``i`` the starting
            point for record ``i`` in the secondary array.
            The record in the second array starts with a cell containing the length of the record,
            and then so many cells of information.
            This array has as its name the name of the primary array plus ``_items``.

            ``node_region`` and ``node_region_items``:
                For node ``i`` the record ``i`` consists of all regions that this node is linked to.

            ``node_out`` and ``node_out_items``:
                For node ``i`` the record ``i`` consists of all outgoing edges from this node.

            ``node_in`` and ``node_in_items``:
                For node ``i`` the record ``i`` consists of all incoming edges into this node.

        ``feature_mapping``, group ``feature``:
            Contains all the feature data. There are in fact three related dictionaries that do the job.
            
            ``feature``:
                Keyed by *annotation space*, then by *annotation label* (both referring to the annotation that 
                contains the feature at hand), then by *feature name*, then by *kind* (``True`` for nodes, 
                ``False`` for edges). At this level we have a dictionary, keyed by either the nodes or the edges
                (both as integers), and the value for each key is the value of the feature, again coded as
                integer.
            
            ``feature_val_int`` and ``feature_val_rep``:
                Raw values are not entered in the ``feature`` dictionary. Instead, every distinct value is uniquely
                identified by an integer. It is this integer that is stored in the ``feature`` dictionary.
                ``feature_val_int`` maps from raw values to integers, and ``feature_val_raw`` maps from integers to
                raw values.
                The mapping of values is per individual feature.
            
            .. note::
                If a feature occurs on both nodes and edges, the feature is split into two features with the same name,
                the one acting on nodes and the other acting on edges. In the compiled version, every feature has a kind,
                and in order to obtain a feature value, you have to specify the feature name and the feature kind (and of course
                the annotation space and annotation label).
            
            So the complete road to a value is::
            
                val = self.data_items['feature``][annotation_space][annotation_label][feature_name][kind][node_or_edge_id]
            
            and if you want to get the raw value back you can do so by::
            
                raw_val = self.data_items['feature_val_rep``][annotation_space][annotation_label][feature_name][kind][val]
            
            Of course, when you do this for various features inside a loop that runs over hundred thousands of nodes,
            you want to give these dictionaries local names outside the loop, so that most dictionary lookup calculations
            only need to be done a few times.
            
            The API will help you to lookup feature values and raw values efficiently, and with clean looking code. 
            See :mod:`task <graf.task>` for a description of the API, especially
            :meth:`get_mappings <graf.task.GrafTask.get_mappings>`
        '''

        self.data_items = {}
        '''Instance member holding the compiled data in the form of a dictionary of arrays and lists.
        
        This dictionary is keyed by the same keys as ``data_items_def`` plus a few additional ones,
        dependent on tnd predictable from he data type and data group.

        See the :mod:`compiler <graf.compiler>` and :mod:`model <graf.model>` modules for the way the compiled data is created.
        '''
        self.given_features = {}
        ''' Instance member holding the information about needed features, provided by the task at hand.
        '''
        self.clear_all()

    def adjust_all(self, directives):
        '''Top level data management function: adjust the data to the task at hand.
        Load what is needed, discard what is no longer need, leave alone what does not to be changed.

        Args:
            directives (dict):
                specification of the needs of the task at hand, in terms of
                which features it uses and whether there is need for the orginal XML ids.
        '''
        self.read_stats()
        for label in self.data_items_def:
            self.adjust_data(label, directives)

    def adjust_data(self, label, directives):
        '''Top level data management function for adjusting data.
        Now per key in the ``data_items_def`` dictionary.

        Args:
            label (str):
                key in ``data_items_def``, indicating the portion of data that has to be adjusted.
            directives (dict):
                passed directly from :meth:`adjust_all`.

        It calls :meth:`check_data` to see whether there is a change affecting the data under this ``label``.
        The answer might be: no (0), or yes absolutely (1) or partly (2), depending on the *directives*.

        Clearance of data is deferred to :meth:`clear_data`, loading to :meth:`load_data`.

        The interesting part is what happens if the answer was *partly (2)*. 
        It then happens on the *directives* argument. The difference between what is needed and what is already
        loaded, is computed, and selective clearing and loading takes place, avoiding clearing
        and loading of the same items.
        '''

        code = self.check_data(label)
        if not code:
            return

        data_group = self.data_items_def[label][1]
        if data_group == 'common':
            self.clear_data(label)
            self.load_data(label)
            return
        if data_group == 'xmlids':
            self.given_xmlids = {}
            for kind_rep in [k for k in directives['xmlids'] if directives['xmlids'][k]]:
                kind = kind_rep == 'node'
                self.given_xmlids[kind] = None
            if code == 1:
                self.clear_data(label)
                self.load_data(label, kinds=self.given_xmlids) 
                return
            if code == 2:
                unload = []
                load = []
                for kind in (True, False):
                    kind_rep = 'node' if kind else 'edge'
                    if kind in self.given_xmlids:
                        if self.is_loaded(label, kind=kind):
                            self.progress("keeping {}: ({}) ...".format(label, kind_rep))
                        else:
                            load.append(kind)
                    else:
                        unload.append(kind)
                self.clear_data(label, kinds=unload)
                self.load_data(label, kinds=load) 
                return
        if data_group == 'feature':
            self.given_features = {}
            for aspace in directives['features']:
                for kind_rep in directives['features'][aspace]:
                    kind = kind_rep == 'node'
                    for line in directives['features'][aspace][kind_rep]:
                        (alabel, fnamestring) = line.split('.')
                        fnames = fnamestring.split(',')
                        for fname in fnames:
                            self.given_features[(aspace, alabel, fname, kind)] = None
            if code == 1:
                self.clear_data(label)
                self.load_data(label, features=self.given_features)
                return
            if code == 2:
                unload = []
                load = []
                for aspace in self.data_items['feature']:
                    for alabel in self.data_items['feature'][aspace]:
                        for fname in self.data_items['feature'][aspace][alabel]:
                            for kind in self.data_items['feature'][aspace][alabel][fname]:
                                kind_rep = 'node' if kind else 'edge'
                                if (aspace, alabel, fname, kind) not in self.given_features:
                                    unload.append((aspace, alabel, fname, kind))
                                else:
                                    self.progress("keeping {}: {}:{}.{} ({}) ...".format(label, aspace, alabel, fname, kind_rep))
                for feature in self.given_features:
                    if not self.is_loaded(label, feature=feature):
                        load.append(feature)
                self.clear_data(label, features=unload)
                self.load_data(label, features=load) 

    def check_data(self, label):
        '''Medium level datamanagement function to check how conditions have changed since
        last task execution and what it implies for the data at hand.

        Args:
            label (str):
                key in ``data_items_def``, indicating the portion of data that has to be adjusted.
        '''

        data_group = self.data_items_def[label][1]
        if data_group == 'common':
            if self.source_changed or self.source_changed == None:
                return 1
        if data_group == 'xmlids':
            if self.source_changed or self.source_changed == None:
                return 1
            if self.task_changed or self.task_changed == None:
                return 2
        if data_group == 'feature':
            if self.source_changed or self.source_changed == None:
                return 1
            if self.annox_changed or self.annox_changed == None:
                return 1
            if self.task_changed or self.task_changed == None:
                return 2
        return False

    def is_loaded(self, label, kind=None, feature=None):
        '''Medium level datamanagement function to check what data is actually loaded.

        Args:
            label (str):
                key in ``data_items_def``, indicating the portion of data that has to be adjusted.
            feature (tuple):
                Specification of the feature of interest.
                Only the load status of this feature will be returned.
            kind (str):
                The kind (``node`` or ``edge``).
                Only the xmlids data status for the given kind will be returned.
                nodes or edges as specified, will be reset.
        '''

        data_type = self.data_items_def[label][0]
        result = True
        if data_type == 'array' or data_type == 'double_array':
            subs = ('',)
            if data_type == 'double_array':
                subs = ('', '_items')
            for sub in subs:
                lab = label + sub
                result = result and lab in self.data_items
        elif data_type =='x_mapping':
            if xmlids != None:
                subs = ('_int', '_rep')
                for sub in subs:
                    lab = label + sub
                    result = result and kind in self.data_items[lab]
        elif data_type == 'feature_mapping':
            if feature != None:
                subs = ('', '_val_int', '_val_rep')
                (aspace, alabel, fname, kind) = feature
                for sub in subs:
                    lab = label + sub
                    result = result and kind in self.data_items[lab][aspace][alabel][fname]
        return result

    def clear_all(self):
        '''Low level data management function to clear all data.
        '''
        for label in self.data_items_def:
            self.clear_data(label)

    def clear_data(self, label, features=None, kinds=None):
        '''Low level data management function to clear all data.
        Now per key in the ``data_items_def`` dictionary.

        Args:
            features (iterable):
                A list of (aspace, alabel, fname, kind) tuples that each specify a feature.
                Optional. If given, only the data for the features specified, will be reset.
            kinds (iterable):
                A list of kinds (``node`` or ``edge``).
                Optional. If given, only the xmlids data for the
                nodes or edges as specified, will be reset.

        If none of the optional features is present, all data for the specified label will be reset.
        '''
        data_type = self.data_items_def[label][0]
        if data_type == 'array' or data_type == 'double_array':
            subs = ('',)
            if data_type == 'double_array':
                subs = ('', '_items')
            if label in self.data_items:
                self.progress("clearing {} ...".format(label))
                for sub in subs:
                    lab = label + sub
                    del self.data_items[lab]

        elif data_type =='x_mapping':
            subs = ('_int', '_rep')
            if kinds != None:
                for kind in kinds:
                    if kind in self.data_items[label+'_int']:
                        kind_rep = 'node' if kind else 'edge'
                        self.progress("clearing {}: ({}) ...".format(label, kind_rep))
                        for sub in subs:
                            lab = label + sub
                            del self.data_items[lab][kind]
            else:
                if label+'_int' in self.data_items:
                    self.progress("clearing all {} data ...".format(label))
                    for sub in subs:
                        lab = label + sub
                        del self.data_items[lab]
                for sub in ('_int', '_rep'):
                    lab = label + sub
                    self.data_items[lab] = collections.defaultdict(lambda: None)

        elif data_type == 'feature_mapping':
            subs = ('', '_val_int', '_val_rep')
            if features != None:
                for (aspace, alabel, fname, kind) in features:
                    if kind in self.data_items[label][aspace][alabel][fname]:
                        kind_rep = 'node' if kind else 'edge'
                        self.progress("clearing {}: {}:{}.{} ({}) ...".format(label, aspace, alabel, fname, kind_rep))
                        for sub in subs:
                            lab = label + sub
                            del self.data_items[lab][aspace][alabel][fname][kind]
            else:
                if label in self.data_items:
                    self.progress("clearing all {} data ...".format(label))
                    for sub in subs:
                        lab = label + sub
                        del self.data_items[lab]
                for sub in subs:
                    lab = label + sub
                    self.data_items[lab] = collections.defaultdict(
                        lambda: collections.defaultdict(
                        lambda: collections.defaultdict(
                        lambda: collections.defaultdict(
                        lambda: None
                    ))))

    def load_data(self, label, features=None, kinds=None):
        '''Low level data management function to load data from disk into memory.

        Args:
            features (iterable):
                A list of (aspace, alabel, fname, kind) tuples that each specify a feature.
                Optional. If given, only the data for the features specified, will be loaded.
            kinds (iterable):
                A list of kinds (``node`` or ``edge``).
                Optional. If given, only the xmlids data for the
                nodes or edges as specified, will be loaded.

        If none of the optional features is present, all data for the specified label will be loaded.
        '''
        data_type = self.data_items_def[label][0]
        if data_type == 'array' or data_type == 'double_array':
            self.progress("loading {:<40}: ... ".format(label), newline=False)
            subs = ('',)
            if data_type == 'double_array':
                subs = ('', '_items')
            for sub in subs:
                lab = label + sub
                self.data_items[lab] = array.array('I')
                b_path = "{}/{}.{}".format(self.env['bin_dir'], lab, self.BIN_EXT)
                b_handle = open(b_path, "rb")
                self.data_items[lab].fromfile(b_handle, self.stats[lab])
                b_handle.close()
            if data_type == 'double_array':
                self.progress("{:>10} records   with {:>10} items".format(len(self.data_items[label]), len(self.data_items[label+'_items'])), withtime=False)
            else:
                self.progress("{:>10} items".format(len(self.data_items[label])), withtime=False)
        if data_type =='x_mapping':
            if kinds != None and len(kinds):
                for kind in kinds:
                    kind_rep = 'node' if kind else 'edge'
                    self.progress("loading {:<40}: ... ".format("{} ({})".format(label, kind_rep)), newline=False)
                    lab_int = label + '_int'
                    lab_rep = label + '_rep'
                    b_path = "{}/{}_{}.{}".format(self.env['bin_dir'], lab_int, kind_rep, self.BIN_EXT)
                    b_handle = open(b_path, "rb")
                    self.data_items[lab_int][kind] = collections.defaultdict(lambda: None, pickle.load(b_handle))
                    b_handle.close()
                    self.data_items[lab_rep][kind] = self.make_inverse(self.data_items[lab_int][kind])
                    self.progress("{:>10} identifiers".format(len(self.data_items[lab_int][kind])), withtime=False)
        elif data_type == 'feature_mapping':
            if features != None and len(features):
                for feature in features:
                    (aspace, alabel, fname, kind) = feature
                    kind_rep = 'node' if kind else 'edge'
                    found = True
                    self.progress("loading {:<40}: ... ".format("{} {}:{}.{} ({})".format(label, aspace, alabel, fname, kind_rep)), newline=False)
                    absolute_feat_path = "{}/{}_{}_{}_{}_{}.{}".format(self.env['feat_dir'], label, aspace, alabel, fname, kind_rep, self.BIN_EXT)
                    try:
                        b_handle = open(absolute_feat_path, "rb")
                        self.data_items[label][aspace][alabel][fname][kind] = pickle.load(b_handle)
                        b_handle.close()
                    except:
                        found = False

                    absolute_feat_path = "{}/{}_{}_{}_{}_{}.{}".format(self.env['feat_dir'], 'values', aspace, alabel, fname, kind_rep, self.BIN_EXT)
                    lab_int = label + '_val_int'
                    lab_rep = label + '_val_rep'
                    try:
                        b_handle = open(absolute_feat_path, "rb")
                        self.data_items[lab_int][aspace][alabel][fname][kind] = pickle.load(b_handle)
                        b_handle.close()
                        self.data_items[lab_rep][aspace][alabel][fname][kind] = self.make_inverse(self.data_items[lab_int][aspace][alabel][fname][kind])
                    except:
                        found = False

                    if not found: 
                        self.progress("WARNING: feature {}:{}.{} ({}) not found in this source".format(aspace, alabel, fname, kind_rep))
                    else:
                        self.progress("{:>10} instances with {:>10} distinct values".format(len(self.data_items[label][aspace][alabel][fname][kind]), len(self.data_items[lab_int][aspace][alabel][fname][kind])), withtime=False)

    def store_all(self):
        '''Top level data management function: write data from memory to disk.

        This function is typically invoked at the end of compilation. 
        When in the business of running user tasks, there is no need for this function, 
        since tasks do not modify the data.
        '''
        for label in self.data_items_def:
            self.store_data(label)

    def store_data(self, label):
        '''Top level data management function for writing data to disk.
        Now per key in the ``data_items_def`` dictionary.

        Args:
            label (str):
                key in ``data_items_def``, indicating the portion of data that has to be adjusted.
        '''

        data_type = self.data_items_def[label][0]
        if data_type == 'array' or data_type == 'double_array':
            subs = ('',)
            if data_type == 'double_array':
                subs = ('', '_items')
            for sub in subs:
                lab = label + sub
                b_path = "{}/{}.{}".format(self.env['bin_dir'], lab, self.BIN_EXT)
                b_handle = open(b_path, "wb")
                self.data_items[lab].tofile(b_handle)
                b_handle.close()
        elif data_type =='x_mapping':
            lab_int = label + '_int'
            for kind in self.data_items[lab_int]:
                kind_rep = 'node' if kind else 'edge'
                b_path = "{}/{}_{}.{}".format(self.env['bin_dir'], lab_int, kind_rep, self.BIN_EXT)
                b_handle = open(b_path, "wb")
                pickle.dump(self.data_items[lab_int][kind], b_handle)
                b_handle.close()
        elif data_type == 'feature_mapping':
            for aspace in self.data_items[label]:
                for alabel in self.data_items[label][aspace]:
                    for fname in self.data_items[label][aspace][alabel]:
                        for kind in self.data_items[label][aspace][alabel][fname]:
                            kind_rep = 'node' if kind else 'edge'
                            absolute_feat_path = "{}/{}_{}_{}_{}_{}.{}".format(self.env['feat_dir'], label, aspace, alabel, fname, kind_rep, self.BIN_EXT)
                            b_handle = open(absolute_feat_path, "wb")
                            pickle.dump(self.data_items[label][aspace][alabel][fname][kind], b_handle)
                            b_handle.close()

                            lab_int = label + '_val_int'
                            absolute_feat_path = "{}/{}_{}_{}_{}_{}.{}".format(self.env['feat_dir'], 'values', aspace, alabel, fname, kind_rep, self.BIN_EXT)
                            b_handle = open(absolute_feat_path, "wb")
                            pickle.dump(self.data_items[lab_int][aspace][alabel][fname][kind], b_handle)
                            b_handle.close()

    def write_stats(self):
        '''Write compilation statistics to file

        The compile process generates some statistics that must be read by the task that loads the compiled data.
        '''
        handle = codecs.open(self.env['stat_file'], "w", encoding = 'utf-8')
        for label in self.data_items_def:
            data_type = self.data_items_def[label][0]
            if data_type == 'array' or data_type == 'double_array':
                subs = ('',)
                if data_type == 'double_array':
                    subs = ('', '_items')
                for sub in subs:
                    lab = label + sub
                    handle.write("{}={}\n".format(lab, len(self.data_items[lab])))
            if data_type =='x_mapping':
                lab_int = label + '_int'
                for kind in self.data_items[lab_int]:
                    kind_rep = 'node' if kind else 'edge'
                    handle.write("{}.{}={}\n".format(label, kind_rep, len(self.data_items[lab_int])))
            elif data_type == 'feature_mapping':
                for aspace in self.data_items[label]:
                    for alabel in self.data_items[label][aspace]:
                        for fname in self.data_items[label][aspace][alabel]:
                            for kind in self.data_items[label][aspace][alabel][fname]:
                                kind_rep = 'node' if kind else 'edge'
                                handle.write("{}.{}.{}.{}.{}={}\n".format(label, aspace, alabel, fname, kind_rep, len(self.data_items[label][aspace][alabel][fname][kind])))
        handle.close()

    def read_stats(self):
        '''Read compilation statistics from file

        The compile process generates some statistics that must be read by the task that loads the compiled data.
        In order to read an :py:mod:`array` by means of its :py:meth:`array.array.fromfile` method,
        we need to know the length of it on beforehand.
        
        And later, when we want to load new feature data on top of the existing data, we need to know
        how many distinct values features have.
        '''
        handle = codecs.open(self.env['stat_file'], "r", encoding = 'utf-8')
        self.stats = {}
        for line in handle:
            (label, count) = line.rstrip("\n").split("=")
            self.stats[label] = int(count)
        handle.close()

    def make_inverse(self, mapping):
        '''Creates the inverse lookup table for a data table

        This is a low level function for creating inverse mappings.
        When mappings (such as from xml-ids to integers vv.) are stored to disk, the inverse mapping is not stored.
        Upon loading, the inverse mapping is generated by means of this function.
        '''
        return dict([(y,x) for (x,y) in mapping.items()])

    def set_environment(self, source, annox, task):
        '''Set the source and result locations for a task execution.

        Args:
            source (str):
                key for the source
            annox (str):
                name of the extra annotation package
            task:
                the chosen task

        Sets *self.env*, a dictionary containg:

        * source: *source*
        * annox: *annox*
        * task: *task*
        * compile (bool): whether to force (re)compilation
        * settings (:py:class:`configparser.ConfigParser`): entries corresponding to the main configuration file
        * additional computed settings adapt to the current source and task

        '''
        settings = self.settings
        data_file = settings['source_choices'][source]
        data_root = settings['locations']['data_root']
        laf_source = settings['locations']['laf_source']
        compiled_source = settings['locations']['compiled_source']
        bin_subdir = settings['locations']['bin_subdir']
        task_dir = settings['locations']['task_dir']
        feat_subdir = settings['locations']['feat_subdir']

        self.env = {
            'source': source,
            'annox': annox,
            'task': task,
            'task_dir': task_dir,
            'data_file': data_file,
            'data_dir': '{}/{}'.format(data_root, laf_source),
            'bin_dir': '{}/{}/{}/{}'.format(data_root, compiled_source, source, bin_subdir),
            'feat_dir': '{}/{}/{}/{}/{}'.format(data_root, compiled_source, source, bin_subdir, feat_subdir),
            'result_dir': '{}/{}/{}/{}'.format(data_root, compiled_source, source, task),
            'compile': False,
            'settings': settings,
        }
        try:
            if not os.path.exists(self.env['bin_dir']):
                os.makedirs(self.env['bin_dir'])
        except os.error:
            raise GrafException(
                "ERROR: could not create bin directory {}".format(self.env['bin_dir']),
                self.stamp, os.error
            )
        try:
            if not os.path.exists(self.env['result_dir']):
                os.makedirs(self.env['result_dir'])
        except os.error:
            raise GrafException(
                "ERROR: could not create result directory {}".format(self.env['result_dir']),
                self.stamp, os.error
            )
        self.env['stat_file'] = "{}/{}{}.{}".format(
            self.env['bin_dir'], self.STAT_NAME, self.COMPILE_TASK, self.TEXT_EXT
        )
        '''Instance member holding name and location of the statistics file that describes the compiled data'''

    def add_logfile(self, location=None, name=None):
        '''Create and open a log file for a given task.

        When tasks run, they generate progress messages with timing information in them.
        They may issue errors and warnings. All this information also goes into a log file.
        The log file is placed in the result directory of the task at hand.

        Args:
            location (str):
                override default directory for log file
            name (str):
                override default name for log file
        '''
        log_dir = self.env['result_dir'] if not location else location
        log_name = "{}{}.{}".format(self.LOG_NAME, self.env['task'] if not name else name, self.TEXT_EXT)

        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        except os.error:
            raise GrafException(
                "ERROR: could not create log directory {}".format(log_dir),
                self.stamp, os.error
            )

        log_file = "{}/{}".format(log_dir, log_name)
        self.log = codecs.open(log_file, "w", encoding = 'utf-8')
        '''Instance member holding the open log handle'''

        self.stamp.connect_log(self.log)
        self.stamp.progress("LOGFILE={}".format(log_file))

    def finish_logfile(self):
        '''Explicitly close log file.

        Do not rely on the ``__del__`` method and hence on garbage collection.
        The program might terminate without writing the last bits to file.
        '''
        try:
            self.log.close()
        except:
            pass
        self.stamp.disconnect_log()
        self.log = None

    def flush_logfile(self):
        try:
            self.log.flush()
        except:
            pass

    def progress(self, msg, newline=True, withtime=True):
        '''Convenience method to call the progress of the associated stamp directly from the Graf object'''
        self.stamp.progress(msg, newline, withtime)

    def __del__(self):
        '''Clean up

        Close all file handles that are still open.
        But really, this ought to have done explicitly already!
        '''
        self.stamp.progress("END")
        for handle in (
            self.log,
        ):
            if handle and not handle.closed:
                handle.close()

