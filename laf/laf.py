import os
import os.path
import shutil
import glob
import collections

import array
import pickle
import gzip

from .settings import Settings, Names
from .timestamp import Timestamp
from .parse import parse as xmlparse
from .model import model as remodel

GZIP_LEVEL = 2

class LafException(Exception):
    def __init__(self, message, stamp, Errors):
        Exception.__init__(self, message)
        stamp.progress(message)
        raise

class Laf(object):
    '''Base class for compiling LAF resources and running analytic tasks on them.

    The data of this class represents the compiled data on the basis of which tasks can run.
    This data is created by the method :meth:`compile_all` in this class.

    '''

    def __init__(self, settings):
        '''Upon creation, empty datastructures are initialized to hold the binary,
        compiled LAF data and create a directory for their serializations on disk.

        The Laf object holds information that Laf tasks need to perform their operations.
        The most important piece of information is the data itself.
        This data consists of arrays and dictionaries that together hold the information that is compiled from a LAF resource.

        Other things that happen: 

        #. a fresh Timestamp object is created, which records the current time and can issue progress messages containing the amount
           of time that has elapsed since this object has been created.
        #. if the directory that should hold the compiled data does not exist,
           a new directory is created Of course this means that before executing any tasks,
           the LAF resource has to be (re)compiled. 

        Args:
            settings (:py:class:`configparser.ConfigParser`):
                entries corresponding to the main configuration file
        Returns:
            object with data structures initialized, ready to load the compiled data from disk.
        '''

        self.stamp = Timestamp()
        '''Instance member holding the :class:`Timestamp <laf.timestamp.Timestamp>` object.
           Useful to deliver progress messages with timing information.
        '''
        self.progress = self.stamp.progress

        self.settings = settings
        '''Instance member to hold config settings etc'''

        self.log = None
        '''handle of a log file, usually open for writing. Used for the log of the compilation process
        and of the task executions.
        '''

        self.data_items = {}
        '''Instance member holding the compiled data in the form of a dictionary of data chunks.
        '''

    def adjust_all(self, source, annox, task, req_items, method_dict, force):
        settings = self.settings
        settings.set_env(source, annox, task)
        env = settings['env']

        try:
            if not os.path.exists(env['main_compiled_dir']):
                os.makedirs(env['main_compiled_dir'])
        except os.error:
            raise LafException(
                "ERROR: could not create bin directory {}".format(env['main_compiled_dir']),
                self.stamp, os.error
            )
        if annox != env['empty']:
            try:
                if not os.path.exists(env['annox_compiled_dir']):
                    os.makedirs(env['annox_compiled_dir'])
            except os.error:
                raise LafException(
                    "ERROR: could not create bin directory {}".format(env['annox_compiled_dir']),
                    self.stamp, os.error
                )
        try:
            if not os.path.exists(env['task_dir']):
                os.makedirs(env['task_dir'])
        except os.error:
            raise LafException(
                "ERROR: could not create result directory {}".format(env['task_dir']),
                self.stamp, os.error
            )

        correct = True
        if not self.compile_all(force):
            correct = False
        if not self.load_all(req_items, method_dict):
            correct = False

        return correct

    def compile_all(self, force):
        settings = self.settings
        env = settings['env']

        compile_uptodate['main'] = not os.path.exists(env['main_source_path']) or (
                os.path.exists(env['main_compiled_path']) and
                os.path.getmtime(env['main_compiled_path']) >= os.path.getmtime(env['main_source_path'])
            )

        uptodate = True
        for afile in glob.glob('{}/*.xml'.format(env['annox_source_dir'])):
            this_uptodate = env['annox'] == env['empty'] or (
                os.path.exists(env['annox_compiled_path']) and
                os.path.getmtime(env['annox_compiled_path']) >= os.path.getmtime(afile)
            )
            if not this_uptodate:
                uptodate = False
                break
        compile_uptodate['annox'] = uptodate
        
        has_compiled = False
        for data in ['main', 'annox']:
            if not compile_uptodate[data] or force[data]:
                self.progress("BEGIN COMPILE {}: {}".format(data, env['source'] if data == 'main' else env['annox']))
                self.clear_data(data)
                if data == 'annox':
                    self.load_all({'X': ['node', 'edge']}, {}, extra=True)
                self.compile_data(data)
                has_compiled = True
                self.progress("END   COMPILE {}: {}".format(data, env['source'] if data == 'main' else env['annox']))
            else:
                self.progress("COMPILING {}: UP TO DATE".format(data))
        if has_compiled:
            self.clear_data(data)
            settings.set_env(source, annox, task)

    def compile_data(self, data):
        '''Manages the compilation process for either the main data or extra annotation files.

        Args:
            data (str):
                whether to parse main data (``main``) or an extra annotation package (``annox``)
        '''
        settings = self.settings
        env = settings['env']
        the_log_file = env['compiled_file']
        the_log_dir = env['{}_compiled_dir'.format(data)]

        self.add_logfile(compile=data)
        self.parse(data)
        self.model(data)
        self.store_data(data)
        self.finish_logfile()

    def clear_data(self, data):
        for dkey in self.data_items:
            (feat, fkind, fdata) = Names.key2f(dkey)
            if (data == fdata):
                self.clear_file(dkey)

    def clear_file(self, dkey): 
        if dkey in self.data_items[dkey]: del self.data_items[dkey]

    def load_all(self, req_items, method_dict, extra=False):
        settings = self.settings
        self.request_files(req_items, extra=extra)

        old_data_items = settings.old_data_items
        new_data_items = settings.data_items

        correct = True

        for dkey in old_data_items:
            if dkey not in new_data_items or new_data_items[dkey][0] != old_data_items[dkey][0]:
                self.progress("clear {}".format(Names.f2con(dkey))) 
                self.clear_file(dkey)
        for dkey in new_data_items:
            if dkey in old_data_items and new_data_items[dkey][0] == old_data_items[dkey][0]:
                self.progress("keep {}".format(Names.f2con(dkey))) 
            else:
                is_annox = False
                comps = Names.key2f(dkey)
                if comps != None:
                    (feat, fkind, fdata) = Names.key2f(dkey)
                    if fdata == 'annox': is_annox = True
                this_correct = self.load_file(dkey, method_dict, accept_missing=is_annox)
                if not this_correct: correct = False

        return correct

    def load_file(self, dkey, accept_missing=False)
        settings = self.settings
        data_items = settings.data_items
        (dpath, dtype, dprep) = data_items[dkey]

        if dprep:
            if dkey not in method_dict:
                self.progress("WARNING: Cannot prepare data for {}. No preparation method available.".format(
                    Names.f2con(dkey)
                ))
                return False
            (method, method_source) = method_dict[dkey]
            up_to_date = os.path.exists(dpath) and os.path.getmtime(dpath) >= os.path.getmtime(method_source)
            if not up_to_date:
                self.progress("PREPARING {}".format(Names.f2con(dkey)))
                newdata = method(api)
                self.progress("WRITING {}".format(Names.f2con(dkey)))
                self.data_items[dkey] = newdata
                self.store_file(dkey)
                return True

        if not os.path.exists(dpath):
            if not accept_missing:
                self.progress("ERROR: Can not load data for {}: File does not exist.".format(Names.f2con(dkey))
            return accept_missing

        newdata = None
        if dtype == 'arr':
            newdata = array.array('I')
            itemsize = newdata.itemsize
            filesize = os.path.getsize(dpath)
            n_items = filesize / itemsize
            handle = gzip.open(dpath, "rb")
            newdata.fromfile(handle, n_items)
            handle.close
        elif dtype == 'dct':
            handle = gzip.open(dpath, "rb")
            newdata = pickle.load(handle)
            handle.close()
        elif dtype == 'str':
            handle = gzip.open(dpath, "rt", encoding="utf-8")
            newdata = handle.read(None)
            handle.close()
        self.data_items[dkey] = newdata

        return True

    def store_data(self, data):
        self.progress("WRITING RESULT FILES for {}".format(data))

        settings = self.settings
        data_items = settings.data_items

        for dkey in data_items:
            (feat, fkind, fdata) = Names.key2f(dkey)
            if (data == fdata):
                self.store_file(dkey)

    def store_file(self, dkey)
        settings = self.settings
        data_items = settings.data_items
        (dpath, dtype, dprep) = data_items[dkey]

        thedata = self.data_items[dkey]

        if dtype == 'arr':
            handle = gzip.open(dpath, "wb", compresslevel=GZIP_LEVEL)
            thedata.tofile(handle)
            handle.close()
        elif dtype == 'dct':
            handle = gzip.open(dpath, "wb", compresslevel=GZIP_LEVEL)
            pickle.dump(thedata, handle)
            handle.close()
        elif dtype == 'str':
            handle = gzip.open(dpath, "wt", encoding="utf-8")
            handle.write(thedata)
            handle.close()

        return True

    def parse(self, data):
        '''Call the XML parser and collect the parse results.

        Some parse results must be remodelled afterwards.
        After remodelling some parse data can be thrown away.
        Only store data that is needed for task execution in the object.

        The actual parsing is done in the module :mod:`parse <laf.parse>`.

        Args:
            data (str):
                whether to parse main data (``main``) or an extra annotation package (``annox``)
        '''
        self.progress("PARSING ANNOTATION FILES")

        settings = self.settings
        env = settings['env']

        source_dir = env['{}_source_dir'.format(data)]
        compiled_dir = env['{}_compiled_dir'format(data)]
        self.cur_dir = os.getcwd()

        try:
            os.chdir(source_dir)
        except os.error:
            raise LafException("ERROR: could not change to LAF data directory {}".format(source_dir),
                self.stamp, os.error
            )
        try:
            if not os.path.exists(compiled_dir):
                os.makedirs(compiled_dir)
        except os.error:
            os.chdir(self.cur_dir)
            raise LafException("ERROR: could not create directory for compiled data {}".format(compiled_dir),
                self.stamp, os.error,
            )
        
        parsed_items = xmlparse(
            env['{}_source_path'.format(data)],
            env['primary_data_path'],
            self.stamp,
            self.data_items,
            Names.kd2p(data, 'node'),
            Names.kd2p(data, 'edge'),
        )
        for (label, item, data) in parsed_items:
            if label not in data_items_def:
                continue
            (bpath, btype, bprep) = data_items_def[label]
            data_items["{}{}".format(label, item)] = ("{}{}".format(bpath, item), btype, bprep)

        os.chdir(self.cur_dir)

    def model(self, data):
        '''Call the remodeler and store the remodeled data in the object.

        Args:
            data (str):
                whether to parse source data (``source``) or an extra annotation package (``annox``)
        '''
        self.progress("MODELING RESULT FILES")

        settings = self.settings
        data_items = settings.data_items
        data_items_def = settings.data_items_def

        modeled_items = remodel(data, self.data_items, self.stamp)
        for (label, item) in modeled_data_items:
            if label not in data_items_def:
                self.progress('discarding temp data {}'.format(label))
                continue
            (bpath, btype, bprep) = data_items_def[label]
            data_items["{}{}".format(label, item)] = ("{}{}".format(bpath, item), btype, bprep)

    def add_logfile(self, compile=None):
        '''Create and open a log file for a given task.

        When tasks run, they generate progress messages with timing information in them.
        They may issue errors and warnings. All this information also goes into a log file.
        The log file is placed in the result directory of the task at hand.

        Args:
            compile (str):
                if it is a log file for compiling, indicate whether it is compiling the main source
                or an annox. Values: ``main``, ``annox``.
        '''
        env = self.settings['env']
        log_dir = env['task_dir'] if compile == None else env["{}_compile_dir".format(compile)]
        log_path = env['log_path'] if compile == None else env["{}_compile_path".format(compile)]

        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        except os.error:
            raise LafException(
                "ERROR: could not create log directory {}".format(log_dir),
                self.stamp, os.error
            )

        self.log = open(log_path, "w", encoding="utf-8")
        '''Instance member holding the open log handle'''

        self.stamp.connect_log(self.log)
        self.stamp.progress("LOGFILE={}".format(log_path))

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

def fabric(
        source=None, annox=None, task=None, verbose=None,
        load=None,
        force_compile = {'main': False, 'annox': False},
    ):
    settings = Settings()
    lafapi = LafAPI(settings.settings)
    lafapi.stamp.set_verbose(verbose)
    lafapi.stamp.reset()

    req_items = {
        'c': [''],
        'P': [],
        'X': [],
        'F': [],
        'E': [],
        'AF': [],
        'AE': [],
    }
    req_items['c'] = ['']
    if load != None:
        if 'primary' in load and load['primary']:
            req_items['P'] = ['']

        if 'xmlids' in load:
            for item in [k for k in load['xmlids'] if load['xmlids'][k]]:
                req_items['X'].append(item)

        if 'features' in load:
        for aspace in load['features']:
            for kind in load['features'][aspace]:
                for line in load['features'][aspace][kind]:
                    (alabel, fnamestring) = line.split('.')
                    fnames = fnamestring.split(',')
                    for fname in fnames:
                        the_feature = (aspace, alabel, fname, kind)
                        req_items['F'].append(the_feature)
                        req_items['AF'].append(the_feature)
                        if kind == 'edge':
                            req_items['E'].append(the_feature)
                            req_items['AE'].append(the_feature)

    method_dict = {}
    lafapi.adjust_all(source, annox, task, req_items, method_dict, force_compile)

    lafapi.add_logfile()
    lafapi.progress("BEGIN TASK={} SOURCE={}".format(self.env['task'], self.env['source']))
    api = lafapi.API()
    lafapi.stamp.reset()
    return api
