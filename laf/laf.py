import os
import os.path
import shutil
import glob
import collections

import array
import pickle
import gzip

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

        self.temp_data_items = None
        '''Holds some data delivered by the parsed that can be thrown away later.
        The data that we must keep is stored in the object, of course.
        '''

    def adjust_all(self, source, annox, task, req_items, method_dict, force):
        self.settings.set_env(source, annox, task)
        env = self.settings['env']

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
        '''Manages the complete compilation process.
        '''
        env = self.settings['env']
        compile_uptodate['source'] = not os.path.exists(env['main_source_file']) or (
                os.path.exists(env['main_compiled_file']) and
                os.path.getmtime(env['main_compiled_file']) >= os.path.getmtime(env['main_source_file'])
            )

        uptodate = True
        for afile in glob.glob('{}/*.xml'.format(env['annox_source_dir'])):
            this_uptodate = env['annox'] == env['empty'] or (
                os.path.exists(env['annox_compiled_file']) and
                os.path.getmtime(env['annox_compiled_file']) >= os.path.getmtime(afile)
            )
            if not this_uptodate:
                uptodate = False
                break
        compile_uptodate['annox'] = uptodate
        
        for data in ['source', 'annox']:
            if data == 'annox':
                self.ensure_loaded({'X': ['node', 'edge']}, {})
            if not compile_uptodate[data] or force[data]:
                self.progress("BEGIN COMPILE {}: {}".format(data_group, self.source if data == 'source' else self.annox))
                self.compile_data(data)
                self.progress("END   COMPILE {}: {}".format(data_group, self.source if data == 'source' else self.annox))
            else:
                self.progress("COMPILING {}: UP TO DATE".format(data_group))

    def load_all(self, req_items, method_dict):
        self.request_files(req_items)

        correct = True

        for x in self.settings.old_data_items:
            if x not in self.settings.data_items:
                self.progress("clear {}".format(self.format_key(x[0], x[1]))) 
                self.clear_file(x)
        for x in self.settings.data_items:
            if x in self.settings.old_data_items:
                self.progress("keep {}".format(self.format_key(x[0], x[1]))) 
            else:
                this_correct = self.load_file(x)
                if not this_correct: correct = False

        for x in self.settings.old_prep_list:
            if x not in self.settings.prep_list:
                self.progress("clear {}".format(self.format_key(x[0], x[1]))) 
                self.clear_file(x)
        for x in self.settings.prep_list:
            if x in preplist_old:
                self.progress("keep {}".format(self.format_key(x[0], x[1]))) 
            else:
                this_correct = self.prepare_file(x, method_dict)
                if not this_correct: correct = False
        self.loadlist = loadlist_new

        return correct

    def ensure_loaded(self, req_items, method_dict):
        loadlist_old = self.loadlist
        preplist_old = self.preplist
        (loadlist_new, preplist_new) = self.request_files(primary, xmlids, features)

        correct = True

        new_updates = []
        prep_updates = []

        for x in loadlist_new:
            if x in loadlist_old:
                self.progress("keep {}".format(self.format_key(x[0], x[1]))) 
            else:
                this_correct = self.load_file(x)
                new_updates.append(x)
                if not this_correct: correct = False

        for x in preplist_new:
            if x in preplist_old:
                self.progress("keep {}".format(self.format_key(x[0], x[1]))) 
            else:
                this_correct = self.prepare_file(x, method_dict)
                prep_updates.append(x)
                if not this_correct: correct = False
        self.loadlist = loadlist_new + new_updates
        self.preplist = preplist_new + prep_updates

        return correct

    def print_file_list(self, filelist):
        for (dkeypath, dkeyname, dtype, dpath) in filelist:
            print("data_items[{}][{}] = {} from file {}".format(
                ']['.join(dkeypath),
                dkeyname,
                "''" if dtype == 'str' else
                0 if dtype == 'num' else
                '{}' if dtype == 'dct' else
                "array.array('I')" if dtype == 'arr' else
                'None',
                dpath,
            ))

    def clear_source(self):
        self.data_items['source'] = {} 

    def clear_annox(self):
        self.data_items['annox'] = {} 

    def clear_file(self, filespec): 
        (dkeypath, dkeyname, dtype, dpath) = filespec

        newdata = None
        if dtype == 'arr':
            newdata = array.array('I')
        elif dtype == 'dct':
            newdata = {}
        elif dtype == 'str':
            newdata = ''

        place = self.data_items
        for comp in dkeypath:
            if comp not in place: place[comp] = {}
            place = place[comp]
        place[dkeyname] = newdata

    def load_file(self, file_spec)
        (dkeypath, dkeyname, dtype, dpath) = filespec

        if not os.path.exists(dpath):
            laf.progress("ERROR: Can not load data for {}: File {} does not exist.".format(self.format_key(dkeypath, dkeyname), dpath))
            return False

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
            handle = open(dpath, "r", encoding="utf-8")
            newdata = handle.read(None)
            handle.close()

        place = self.data_items
        for comp in dkeypath:
            if comp not in place: place[comp] = {}
            place = place[comp]
        place[dkeyname] = newdata

        return True

    def prepare_file(self, file_spec, method_dict)
        (dkeypath, dkeyname, dtype, dpath) = filespec
        method_key = dkeypath + (dkeyname,)

        if method_key not in method_dict:
            self.progress("WARNING: Cannot prepare data for {}. No preparation method available.".format(self.format_key(dkeypath, dkeyname)))
            return False
        (method, method_source) = method_dict[method_key]
        up_to_date = os.path.exists(dpath) and os.path.getmtime(dpath) >= os.path.getmtime(method_source)
        if not up_to_date:
            self.progress("PREPARING {}".format(format_key(dkeypath, dkeyname)))
            newdata = method(api)
            self.progress("WRITING {} (prepared)".format(format_key(dkeypath, dkeyname)))
        return self.load_file(file_spec)

    def store_file(self, filespec)
        (dkeypath, dkeyname, dtype, dpath) = filespec

        place = self.data_items
        for comp in dkeypath + (dkeyname,):
            if comp not in place:
                laf.progress("Error: Can not write data for {} to {}: Data selected by {} is not present.".format(self.format_key(dkeypath, dkeyname), dpath, comp))
                return False
            place = place[comp]
        newdata = place[dkeyname]

        if dtype == 'arr':
            handle = gzip.open(dpath, "wb", compresslevel=GZIP_LEVEL)
            newdata.tofile(handle)
            handle.close()
        elif dtype == 'dct':
            handle = gzip.open(dpath, "wb", compresslevel=GZIP_LEVEL)
            pickle.dump(newdata, handle)
            handle.close()
        elif dtype == 'str':
            handle = open(dpath, "w", encoding="utf-8")
            handle.write(newdata)
            handle.close()

        return True

    def format_key(self, dpath, dkey):
        return "{}: {}".format('/'.join(dpath), dkey)


    def format_item(self, data_group, item, asFile=False):
        if data_group == 'common':
            return item
        if data_group == 'xmlids':
            return item
        if data_group == 'primary':
            return item
        if data_group == 'feature' or data_group == 'annox':
            if asFile:
                return '{}_{}_{}_{}'.format(*item)
            else:
                return '{}:{}.{} ({})'.format(*item)

    def compile_data(self, data_group):
        '''Manages the compilation process for either the source data or extra annotation files.

        Args:
            data_group (str):
                whether to parse source data (``source``) or an extra annotation package (``annox``)
        '''
        the_log_file = self.COMPILE_NAME
        the_log_dir = self.main_compiled_dir if data_group == 'source' else self.annox_compiled_dir

        self.add_logfile(the_log_dir, the_log_file)
        self.parse(data_group)
        self.model(data_group)
        self.write_data(data_group)
        self.finish_logfile()

    def parse(self, data_group, xmlitems):
        '''Call the XML parser and collect the parse results.

        Some parse results must be remodelled afterwards.
        After remodelling some parse data can be thrown away.
        Only store data that is needed for task execution in the object.

        The actual parsing is done in the module :mod:`parse <laf.parse>`.

        Args:
            data_group (str):
                whether to parse source data (``source``) or an extra annotation package (``annox``)
        '''
        self.progress("PARSING ANNOTATION FILES")

        source_file = self.main_source_path if data_group == 'source' else self.annox_source_path
        source_dir = self.main_source_dir if data_group == 'source' else self.annox_source_dir
        compiled_dir = self.main_compiled_dir if data_group == 'source' else self.annox_compiled_dir
        feature_dir = self.main_feature_dir if data_group == 'source' else self.annox_feature_dir
        self.cur_dir = os.getcwd()

        try:
            os.chdir(source_dir)
        except os.error:
            raise LafException("ERROR: could not change to LAF data directory {}".format(source_dir),
                self.stamp, os.error
            )
        try:
            if not os.path.exists(feature_dir):
                os.makedirs(feature_dir)
        except os.error:
            os.chdir(self.cur_dir)
            raise LafException("ERROR: could not create directory for compiled data {}".format(the_bin_dir),
                self.stamp, os.error,
            )
        
        prim_bin_file = "{}/{}".format(self.main_compiled_dir, self.settings['locations']['primary_data']) if data_group == 'source' else None

        parsed_data_items = xmlparse(source_file, prim_bin_file, self.stamp, self.data_items['xid'])

        self.temp_data_items = {}

        for parsed_data_item in parsed_data_items:
            (keypath, keyname, data, keep) = parsed_data_item
            dest = self.data_items if keep else self.temp_data_items
            for comp in keypath:
                if comp not in dest:
                    dest[comp] = {}
                    dest = dest[comp]
            dest[keyname] = data

        os.chdir(self.cur_dir)

    def model(self, data_group):
        '''Call the remodeler and store the remodeled data in the object.

        Args:
            data_group (str):
                whether to parse source data (``source``) or an extra annotation package (``annox``)
        '''
        if data_group == 'source':
            self.progress("MODELING RESULT FILES")
            modeled_data_items = remodel(self.data_items, self.temp_data_items, self.stamp)
            for modeled_data_item in modeled_data_items:
                (label, data) = modeled_data_item
                self.data_items[label] = data
            self.temp_data_items = None

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
        log_dir = self.result_dir if not location else location
        log_name = "{}{}.{}".format(self.LOG_NAME, self.task if not name else name, self.TEXT_EXT)

        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        except os.error:
            raise LafException(
                "ERROR: could not create log directory {}".format(log_dir),
                self.stamp, os.error
            )

        log_file = "{}/{}".format(log_dir, log_name)
        self.log = open(log_file, "w", encoding="utf-8")
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

    def make_inverse(self, mapping):
        '''Creates the inverse lookup table for a data table given as a dictionary.

        This is a low level function for creating inverse mappings.
        When mappings (such as from xml-ids to integers vv.) are stored to disk, the inverse mapping is not stored.
        Upon loading, the inverse mapping is generated by means of this function.
        '''
        return dict([(y,x) for (x,y) in mapping.items()])

    def make_array_inverse(self, arraylist):
        '''Creates the inverse lookup table for a data table given as a Python array.

        This is a low level function for creating inverse mappings.
        When mappings (such as from xml-ids to integers vv.) are stored to disk, the inverse mapping is not stored.
        Upon loading, the inverse mapping is generated by means of this function.
        '''
        return dict([(x,n) for (n,x) in enumerate(arraylist)])

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

