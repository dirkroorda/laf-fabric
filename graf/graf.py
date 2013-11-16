# -*- coding: utf8 -*-

import os
import os.path
import codecs

import array

from timestamp import Timestamp

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
        '''Upon creation, empty datastructures are initialized to hold the binary, compiled LAF data and create a directory for their serializations on disk.

        The Graf object holds information that Graf tasks need to perform their operations. The most important piece of information is the data itself.
        This data consists of arrays and dictionaries that together hold the information that is compiled from a LAF resource.

        Other things that happen: 

        #. a fresh Timestamp object is created, which records the current time and can issue progress messages containing the amount
           of time that has elapsed since this object has been created.
        #. if the directory that should hold the compiled data does not exist, a new directory is created Of course this means that before executing any tasks,
           the LAF resource has to be (re)compiled. 

        Returns:
            object with data structures initialized, ready to load the compiled data from disk.
        '''
        self.stamp = Timestamp()
        '''Instance member holding the :class:`Timestamp <graf.timestamp.Timestamp>` object.'''

        self.data_items = {
            "feat_name_list_rep": [False, {}],
            "feat_name_list_int": [False, {}],
            "feat_value_list_rep": [False, {}],
            "feat_value_list_int": [False, {}],
            "region_begin": [True, array.array('I')],
            "region_end": [True, array.array('I')],
            "node_region": [True, array.array('I')],
            "node_region_items": [True, array.array('I')],
            "node_sort": [True, array.array('I')],
            "node_out": [True, array.array('I')],
            "node_out_items": [True, array.array('I')],
            "node_in": [True, array.array('I')],
            "node_in_items": [True, array.array('I')],
            "node_feat": [True, array.array('I')],
            "node_feat_items": [True, array.array('I')],
            "edges_from": [True, array.array('I')],
            "edges_to": [True, array.array('I')],
            "edge_feat": [True, array.array('I')],
            "edge_feat_items": [True, array.array('I')],
            "feat_label": [True, array.array('H')],
            "feat_name": [True, array.array('H')],
            "feat_value": [True, array.array('I')],
        }
        '''Instance member holding the compiled data in the form of a dictionary of arrays and lists.

        See the :mod:`compiler <graf.compiler>` and :mod:`model <graf.model>` modules for the way the compiled data is organised.
        '''

        try:
            if not os.path.exists(env['bin_dir']):
                os.makedirs(env['bin_dir'])
        except os.error:
            raise GrafException(
                "ERROR: could not create bin directory {}".format(env['bin_dir']),
                self.stamp, os.error
            )
        self.env['stat_file'] = "{}/{}{}.{}".format(
            env['bin_dir'], self.STAT_NAME, self.COMPILE_TASK, self.TEXT_EXT
        )
        '''Instance member holding name and location of the statistics file that describes the compiled data'''

    def set_environment(self, source, task, settings):
        '''Set the source and result locations for a task execution.

        Args:
            source (str): key for the source
            task: the chosen task
            settings (dict): the parsed contents of the main configuration file

        Sets *self.env*, a dictionary containg:

        * source: *source*
        * task: *task*
        * data_file (str): file name of the GrAF header file indicated by *source*
        * data_dir (str): absolute path to where the LAF data resides
        * bin_dir (str): absolute path to where the compiled binary data resides
        * feat_dir (str): absolute path to where the compiled binary feature data resides
        * result_dir (str): absolute path to where the results of the execution of *task* ends up
        * compile (bool): whether to force (re)compilation

        '''
        data_root = settings.get('locations', 'data_root')
        laf_source = settings.get('locations', 'laf_source')
        compiled_source = settings.get('locations', 'compiled_source')
        bin_subdir = settings.get('locations', 'bin_subdir')
        feat_subdir = settings.get('locations', 'feat_subdir')

        self.env = {
            'source': source,
            'task': task,
            'data_file': source_choices[source],
            'data_dir': '{}/{}'.format(data_root, laf_source),
            'bin_dir': '{}/{}/{}/{}'.format(data_root, compiled_source, source, bin_subdir),
            'feat_dir': '{}/{}/{}/{}/{}'.format(data_root, compiled_source, source, bin_subdir, feat_subdir),
            'result_dir': '{}/{}/{}/{}'.format(data_root, compiled_source, source, task),
            'compile': False,
        }

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
        log_dir = self.env['result_dir'] if not location and not name else u'{}/{}'.format(location, name)

        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        except os.error:
            raise GrafException(
                "ERROR: could not create log directory {}".format(log_dir),
                self.stamp, os.error
            )

        log_file = "{}/{}{}.{}".format(
            log_dir, self.LOG_NAME, self.env['task'], self.TEXT_EXT
        )
        self.log = codecs.open(log_file, "w", encoding = 'utf-8')
        '''Instance member holding the open log handle'''

        self.stamp.connect_log(self.log)
        self.stamp.progress("LOGFILE={}".format(log_file))

    def progress(self, msg):
        '''Convenience method to call the progress of the associated stamp directly from the Graf object'''
        self.stamp.progress(msg)

    def write_stats(self):
        '''Write compilation statistics to file

        The compile process generates some statistics that must be read by the task that loads the compiled data.
        '''
        stat = codecs.open(self.env['stat_file'], "w", encoding = 'utf-8')
        for (label, info) in self.data_items.items():
            (is_binary, data) = info 
            stat.write(u"{}={}\n".format(label, len(data)))
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

