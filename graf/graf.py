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

    This class has only a rudimentary method set. Compiling a LAF resource is done by the GrafCompiler derived class
    and running analytic tasks is done by the GrafTask class.

    The data of this class represents the compiled data on the basis of which tasks can run.
    This data is created by a :class:`GrafCompiler <graf.compiler.GrafCompiler>` that derives from this class.

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

    env = None
    '''Holds the environment parameters for the current task
    '''
    stamp = None
    '''object that contains a timestamp and can deliver progress messages with timing information
    '''
    log = None
    '''handle of a log file, open for writing
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
        '''Instance member holding the :class:`Timestamp <graf.timestamp.Timestamp>` object.'''

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

        self.data_items = {}
        '''Instance member holding the compiled data in the form of a dictionary of arrays and lists.

        See the :mod:`compiler <graf.compiler>` and :mod:`model <graf.model>` modules for the way the compiled data is organised.
        '''
        self.given_features = {}
        ''' Instance member holding the information about needed features, provided by the task at hand.
        '''
        self.clear_all()

    def adjust_all(self, directives):
        self.read_stats()
        for label in self.data_items_def:
            self.adjust_data(label, directives)

    def adjust_data(self, label, directives):
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
                self.load_data(label, xmlids=self.given_xmlids) 
                return
            if code == 2:
                unload = []
                load = []
                for kind in (True, False):
                    kind_rep = 'node' if kind else 'edge'
                    if kind in self.given_xmlids:
                        if self.is_loaded(label, xmlids=[kind]):
                            self.progress("keeping {}: ({}) ...".format(label, kind_rep))
                        else:
                            load.append(kind)
                    else:
                        unload.append(kind)
                self.clear_data(label, xmlids=unload)
                self.load_data(label, xmlids=load) 
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
                    if not self.is_loaded(label, features=[feature]):
                        load.append(feature)
                self.clear_data(label, features=unload)
                self.load_data(label, features=load) 

    def check_data(self, label):
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

    def is_loaded(self, label, xmlids=None, features=None):
        '''
        Args:
            feature (str, int):
                the kind (``node`` or ``edge``) and qualified name of a feature.
                Optional. If given, only the data for the
                feature specified, will be reset.

            xmlids (str):
                the kind (``node`` or ``edge``).
                Optional. If given, only the xmlids data for the
                nodes or edges as specified, will be reset.

        If none of the optional features is present, all data for the specified label will be reset.
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
                for kind in xmlids:
                    for sub in subs:
                        lab = label + sub
                        result = result and kind in self.data_items[lab]
        elif data_type == 'feature_mapping':
            if features != None:
                subs = ('', '_val_int', '_val_rep')
                for (aspace, alabel, fname, kind) in features:
                    for sub in subs:
                        lab = label + sub
                        result = result and kind in self.data_items[lab][aspace][alabel][fname]
        return result

    def clear_all(self):
        for label in self.data_items_def:
            self.clear_data(label)

    def clear_data(self, label, features=None, xmlids=None):
        '''
        Args:
            feature (str, int):
                the kind (``node`` or ``edge``) and qualified name of a feature.
                Optional. If given, only the data for the
                feature specified, will be reset.

            xmlids (str):
                the kind (``node`` or ``edge``).
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
            if xmlids != None:
                for kind in xmlids:
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

    def load_data(self, label, features=None, xmlids=None):
        '''
        Args:
            feature (str, int):
                the kind (``node`` or ``edge``) and qualified name of a feature.
                Optional. If given, only the data for the
                feature specified, will be loaded.

            xmlids (str):
                the kind (``node`` or ``edge``).
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
            if xmlids != None and len(xmlids):
                for kind in xmlids:
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
        for label in self.data_items_def:
            self.store_data(label)

    def store_data(self, label):
        '''
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

    def make_inverse(self, mapping):
        '''Creates the inverse lookup table for a data table

        '''
        return dict([(y,x) for (x,y) in mapping.items()])

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
        '''
        handle = codecs.open(self.env['stat_file'], "r", encoding = 'utf-8')
        self.stats = {}
        for line in handle:
            (label, count) = line.rstrip("\n").split("=")
            self.stats[label] = int(count)
        handle.close()

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

    def __del__(self):
        '''Clean up

        Close all file handles that are still open.
        '''
        self.stamp.progress("END")
        for handle in (
            self.log,
        ):
            if handle and not handle.closed:
                handle.close()

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

