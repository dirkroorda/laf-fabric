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
        self.prev_tasks = {}
        '''List of tasks executed in this run of the workbench, with the modification time of the task program file
        at the time it was last run'''

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

        this_mtime = self.get_task_mtime(task)
        if task in self.prev_tasks:
            prev_mtime = self.prev_tasks[task]
            if prev_mtime < this_mtime:
                self.prev_tasks[task] = this_mtime
                self.task_changed = True
        else:
            self.prev_tasks[task] = this_mtime

        self.stamp.reset()
        self.set_environment(source, annox, task)
        self.compile(force_compile)
        self.stamp.reset()

        exec("import {}".format(task))
        exec("imp.reload({})".format(task))

        load = eval("{}.load".format(task))
        self.adjust_all(load)

        taskcommand = eval("{}.task".format(task))

        self.stamp.reset()

        self.init_task()
        taskcommand(self) 
        self.finish_task()

    def get_task_mtime(self, task):
        task_dir = self.settings['locations']['task_dir']
        return os.path.getmtime('{}/{}.py'.format(task_dir, task))

    def compile(self, force_compile):
        grafcompiler = GrafCompiler(self.env)
        grafcompiler.compiler(force=force_compile)
        grafcompiler.finish()
        self.has_compiled = grafcompiler.has_compiled
        grafcompiler = None

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

    def get_mappings(self):
        '''Return references to API methods of this class.

        The caller can give convenient, local names to these methods.
        It also saves method lookup,
        at least, I think so.
        ''' 

        def next_node(test=None, value=None):
            '''API: iterator of all nodes in primary data order that have a
            given value for a given feature.

            See also :meth:`next_node`.

            Args:
                name (int):
                    the code of a feature name

                value (int):
                    the code of a feature value
            '''
            if test != None:
                for node in self.data_items["node_sort"]:
                    if value == test(node):
                        yield node
            else:
                for node in self.data_items["node_sort"]:
                    yield node

        feature_objects = []

        for (aspace, alabel, fname, kind) in self.given_features:
            feature_objects.append(Feature(self, aspace, alabel, fname, kind))

        xmlid_objects = []

        for kind in self.given_xmlids:
            xmlid_objects.append(XMLid(self, kind))

        return (
            self.progress,
            next_node,
            Features(feature_objects),
            XMLids(xmlid_objects)
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

class Feature(object):
    def __init__(self, graftask, aspace, alabel, fname, kind):
        kind_rep = 'node' if kind else 'edge'
        self.fspec = "{}:{}.{} ({})".format(aspace, alabel, fname, kind_rep)
        self.local_name = "{}_{}_{}{}".format(aspace, alabel, fname, '' if kind else '_e')
        self.kind = kind
        self.lookup = graftask.data_items['feature'][aspace][alabel][fname][kind]
        self.code = graftask.data_items['feature_val_int'][aspace][alabel][fname][kind]
        self.rep = graftask.data_items['feature_val_rep'][aspace][alabel][fname][kind]

    def v(self, ne):
        return self.lookup[ne]

    def vr(self, ne):
        return self.rep[self.lookup[ne]]

    def r(self, ne):
        return self.rep[ne]

    def i(self, ne):
        return self.code[ne]

class Features(object):
    def __init__(self, feature_objects):
        for fo in feature_objects:
            exec("self.{} = fo".format(fo.local_name))

class XMLid(object):
    def __init__(self, graftask, kind):
        kind_rep = 'node' if kind else 'edge'
        self.local_name = kind_rep
        self.kind = kind
        self.code = graftask.data_items['xid_int'][kind]
        self.rep = graftask.data_items['xid_rep'][kind]

    def r(self, ne):
        return self.rep[ne]

    def i(self, ne):
        return self.code[ne]

class XMLids(object):
    def __init__(self, xmlid_objects):
        for xo in xmlid_objects:
            exec("self.{} = xo".format(xo.local_name))

