# -*- coding: utf8 -*-

import os
import os.path
import codecs
import collections

import array

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

        self.data_items_def = {
            "feat_name_list_node_rep": 0,
            "feat_name_list_node_int": 0,
            "feat_name_list_edge_rep": 0,
            "feat_name_list_edge_int": 0,
            "feat_value_list_rep": 0,
            "feat_value_list_int": 0,
            "region_begin": 1,
            "region_end": 1,
            "node_region": 1,
            "node_region_items": 1,
            "node_sort": 1,
            "node_out": 1,
            "node_out_items": 1,
            "node_in": 1,
            "node_in_items": 1,
            "edges_from": 1,
            "edges_to": 1,
            "feat_ref": 2,
            "feat_value": 2,
        }

        self.data_items = {}
        '''Instance member holding the compiled data in the form of a dictionary of arrays and lists.

        See the :mod:`compiler <graf.compiler>` and :mod:`model <graf.model>` modules for the way the compiled data is organised.
        '''
        self.node_feat = None
        '''Feature data (for features on nodes) stored in dictionary for fast access'''
        self.edge_feat = None
        '''Feature data (for features on edges) stored in dictionary for fast access'''

        self.init_data()

    def init_data(self, feature=None):
        '''Resets all loaded data to initial values, or just the data of a single feature

        Args:
            feature (str, int): the kind (``node`` or ``edge``) and qualified name of a feature.
            Optional. If None, all data will be reset, if given, only the data for the
            feature specified.

        This is needed when the task processor switches from one source to another,
        or when a recompile has been performed.
        '''
        if (feature == None):
            self.node_feat = collections.defaultdict(lambda: collections.defaultdict(lambda: None))
            self.edge_feat = collections.defaultdict(lambda: collections.defaultdict(lambda: None))
            for label in self.data_items_def:
                is_binary = self.data_items_def[label]
                if not is_binary:
                    self.data_items[label] = {}
                elif is_binary == 1:
                    self.data_items[label] = array.array('I')
                elif is_binary == 2:
                    self.data_items[label] = collections.defaultdict(lambda: collections.defaultdict(lambda:array.array('I')))
        else:
            (kind, fname) = feature
            for label in self.feat_labels:
                self.data_items[label][kind][fname] = array.array('I')

    def set_environment(self, source, task):
        '''Set the source and result locations for a task execution.

        Args:
            source (str): key for the source
            task: the chosen task

        Sets *self.env*, a dictionary containg:

        * source: *source*
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
            location (str): override default directory for log file
            name (str): override default name for log file
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

    def progress(self, msg):
        '''Convenience method to call the progress of the associated stamp directly from the Graf object'''
        self.stamp.progress(msg)

    def write_stats(self):
        '''Write compilation statistics to file

        The compile process generates some statistics that must be read by the task that loads the compiled data.
        '''
        stat = codecs.open(self.env['stat_file'], "w", encoding = 'utf-8')
        for (label, is_binary) in self.data_items_def.items():
            data = self.data_items[label]
            if is_binary == 2:
                for kind in data:
                    for fname in data[kind]:
                        stat.write("{}_{}_{}={}\n".format(label, kind, fname, len(data[kind][fname])))
            else:
                stat.write("{}={}\n".format(label, len(data)))

        stat.close()

    def read_stats(self):
        '''Read compilation statistics from file

        The compile process generates some statistics that must be read by the task that loads the compiled data.
        '''
        stat = codecs.open(self.env['stat_file'], "r", encoding = 'utf-8')
        self.stats = {}
        for line in stat:
            (label, count) = line.rstrip("\n").split("=")
            self.stats[label] = int(count)
        stat.close()

