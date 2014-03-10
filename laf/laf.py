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
    COMPILE_NAME = 'compile__'
    '''name of the compile task
    '''

    file_list = '''
source/node_anchor         = arr = primary  = {source}/{bin}/{{name}}.{bext}
source/node_anchor_items   = arr = primary  = {source}/{bin}/{{name}}.{bext}
source/node_anchor_min     = arr = common   = {source}/{bin}/{{name}}.{bext}
source/node_anchor_max     = arr = common   = {source}/{bin}/{{name}}.{bext}
source/node_events         = arr = primary  = {source}/{bin}/{{name}}.{bext}
source/node_events_items   = arr = primary  = {source}/{bin}/{{name}}.{bext}
source/node_events_k       = arr = primary  = {source}/{bin}/{{name}}.{bext}
source/node_events_n       = arr = primary  = {source}/{bin}/{{name}}.{bext}
source/node_sort           = arr = common   = {source}/{bin}/{{name}}.{bext}
source/node_sort_inv       = dct = common   = {source}/{bin}/{{name}}.{bext}
source/node_resorted       = arr = prepared = {source}/{bin}/{prp}/{{name}}.{bext}
source/node_resorted_inv   = arr = prepared = {source}/{bin}/{prp}/{{name}}.{bext}
source/edges_from          = arr = common   = {source}/{bin}/{{name}}.{bext}
source/edges_to            = arr = common   = {source}/{bin}/{{name}}.{bext}
source/primary_data        = str = primary  = {source}/{bin}/{{name}}.{text}
source/xid/{{comp}}_int    = dct = xmlids   = {source}/{bin}/{xid}/{{comp}}_int.{bext}
source/xid/{{comp}}_rep    = dct = xmlids   = {source}/{bin}/{xid}/{{comp}}_rep.{bext}
source/feat/{{comp}}       = dct = feature  = {source}/{bin}/{feat}/{{compr}}.{bext}
source/cfeat/{{comp}}      = dct = efeature = {source}/{bin}/{feat}/conn+{{compr}}.{bext}
annox/feat/{{comp}}        = dct = feature  = {source}/{bin}/{anx}/{annox}/{{compr}}.{bext}
annox/cfeat/{{comp}}       = dct = efeature = {source}/{bin}/{anx}/{annox}/conn+{{compr}}.{bext}
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

        self.env = {}
        '''Holds the context information for the current task, such as chosen source, annox and task.
        '''

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

        self.source = None
        self.annox = None
        self.loadlist = {}
        self.preparedlist = {}

    def requested_files(self, source, annox, primary, xmlids, features):
        locations = self.settings['locations']
        lines = self.file_list.split("\n")
        newlist = []
        preparedlist = []
        for line in lines:
            if not len(line): continue
            xline = line.format(
                source=source,
                annox=annox,
                bin=locations['bin_subdir'],
                bext=self.BIN_EXT,
                text=self.TEXT_EXT,
                prp=self.locations['prep_subdir'],
                xid=self.locations['xid_subdir'],
                feat=self.locations['feat_subdir'],
                anx=self.locations['annox_subdir'],
            )
            (dkey, dtype, dcond, dpath) = [x.strip() for x in xline.split("=")]
            dkeyparts = dkey.split('/')
            dkeypath = dkeyparts[0:len(dkeyparts)-1]
            dkeyname = dkeyparts[-1]
            if dcond == 'common': newlist.append((dkeypath, dkeyname, dtype, dpath.format(name=dkeyname)))
            if dcond == 'prepared': preparedlist.append((dkeypath, dkeyname, dtype, dpath.format(name=dkeyname)))
            elif dcond == 'primary' and primary: newlist.append((dkeypath, dkeyname, dtype, dpath.format(name=dkeyname)))
            elif dcond == 'xmlids':
                for comp in xmlids:
                    comprep = comp
                    if type(comp) == type(()):
                        comprep = '_'.join(comp)
                    newlist.append((dkeypath, dkeyname.format(comp=comp), dtype, dpath.format(comp=comp, compr=comprep)))
            elif dcond == 'feature':
                for comp in features:
                    comprep = comp
                    if type(comp) == type(()):
                        comprep = '_'.join(comp)
                    newlist.append((dkeypath, dkeyname.format(comp=comp), dtype, dpath.format(comp=comp, compr=comprep)))
            elif dcond == 'efeature':
                for comp in features:
                    if comp[3] != 'edge': continue
                    comprep = comp
                    if type(comp) == type(()):
                        comprep = '_'.join(comp)
                    newlist.append((dkeypath, dkeyname.format(comp=comp), dtype, dpath.format(comp=comp, compr=comprep)))
        return (newlist, preparedlist)

    def adjust_all(self, source, annox, primary, xmlids, features, method_dict):
        loadlist_old = self.loadlist
        preparedlist_old = self.preparedloadlist
        (loadlist_new, preparedlist_new) = self.requested_files(source, annox, primary, xmlids, features)

        correct = True

        for x in loadlist_old:
            if x not in loadlist_new:
                self.progress("clear {}".format(self.format_key(x[0], x[1]))) 
                self.clear_file(x)
        for x in loadlist_new:
            if x in loadlist_old:
                self.progress("keep {}".format(self.format_key(x[0], x[1]))) 
            else:
                this_correct = self.load_file(x)
                if not this_correct: correct = False

        for x in preparedlist_old:
            if x not in preparedlist_new:
                self.progress("clear {}".format(self.format_key(x[0], x[1]))) 
                self.clear_file(x)
        for x in preparedlist_new:
            if x in preparedlist_old:
                self.progress("keep {}".format(self.format_key(x[0], x[1]))) 
            else:
                this_correct = self.prepare_file(x, method_dict)
                if not this_correct: correct = False

        self.source = source
        self.annox = annox
        self.loadlist = loadlist_new
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

    def compile_all(self, force):
        '''Manages the complete compilation process.
        '''
        self.compile_data('source', force['source'])
        self.compile_data('annox', force['annox'])

    def compile_data(self, data_group, force):
        '''Manages the compilation process for either the source data or extra annotation files.

        Detects the need for compiling, responds to the *force* argument. Then parses, remodels and writes.

        Args:
            data_group (str):
                whether to parse source data (``source``) or an extra annotation package (``annox``)
            force (bool):
                whether to compile even if the binary data looks up to date.
        '''
        if force or self.status['compile'][data_group] == False:
            xmlitems = None
            if data_group == 'annox':
                self.check_load_status()
                self.adjust_data('xmlids', items=['node', 'edge'])
                xmlitems = self.data_items['xid_int']

            the_what = self.env['source'] if data_group == 'source' else self.env['annox']
            the_log_file = self.COMPILE_NAME + the_what
            the_log_dir = self.env['bin_dir'] if data_group == 'source' else self.env['annox_base_bdir']
            the_data_file = self.env['source'] if data_group == 'source' else self.env['annox_file']

            self.progress("BEGIN COMPILE {}: {}".format(data_group, the_what))
            self.add_logfile(the_log_dir, the_log_file)
            self.parse(data_group, xmlitems)
            self.model(data_group)
            self.write_data(data_group)
            self.progress("END COMPILE {}: {}".format(data_group, the_what))
            self.finish_logfile()
            self.status['compile'][data_group] = None
        else:
            self.progress("COMPILING {}: UP TO DATE".format(data_group))

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
        self.cur_dir = os.getcwd()

        the_data_file = self.env['source'] if data_group == 'source' else self.env['annox_file']
        the_laf_dir = self.env['laf_dir'] if data_group == 'source' else self.env['annox_dir']
        the_bin_dir = self.env['feat_dir'] if data_group == 'source' else self.env['annox_bdir']

        try:
            os.chdir(the_laf_dir)
        except os.error:
            raise LafException("ERROR: could not change to LAF data directory {}".format(the_laf_dir),
                self.stamp, os.error
            )
        try:
            if not os.path.exists(the_bin_dir):
                os.makedirs(the_bin_dir)
        except os.error:
            os.chdir(self.cur_dir)
            raise LafException("ERROR: could not create directory for compiled data {}".format(the_bin_dir),
                self.stamp, os.error,
            )
        
        prim_bin_file = "{}/{}".format(self.env['bin_dir'], self.settings['locations']['primary_data']) if data_group == 'source' else None

        parsed_data_items = xmlparse(the_data_file, prim_bin_file, self.stamp, xmlitems)

        self.temp_data_items = {}

        for parsed_data_item in parsed_data_items:
            (label, data, keep) = parsed_data_item
            if data_group == 'source':
                if keep:
                    self.data_items[label] = data
                else:
                    self.temp_data_items[label] = data
            else:
                use_label = label
                if label.startswith('feature'):
                    use_label = 'x' + label
                    self.data_items[use_label] = data

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
        work_dir = settings['locations']['work_dir']
        laf_dir = settings['locations']['laf_dir']
        annox_file = settings['annox']['header']
        annox_root = settings['locations']['annox_dir']
        bin_subdir = settings['locations']['bin_subdir']
        task_dir = settings['locations']['task_dir']
        feat_subdir = settings['locations']['feat_subdir']
        annox_subdir = settings['locations']['annox_subdir']

        self.env = {
            'source': source,
            'annox': annox,
            'task': task,
            'task_dir': task_dir,
            'laf_dir': laf_dir,
            'data_path': '{}/{}'.format(laf_dir, source),
            'annox_file': annox_file,
            'annox_dir': '{}/{}'.format(annox_root, annox),
            'annox_path': '{}/{}/{}'.format(annox_root, annox, annox_file),
            'bin_dir': '{}/{}/{}'.format(work_dir, source, bin_subdir),
            'feat_dir': '{}/{}/{}/{}'.format(work_dir, source, bin_subdir, feat_subdir),
            'annox_base_bdir': '{}/{}/{}/{}'.format(work_dir, source, bin_subdir, annox_subdir),
            'annox_bdir': '{}/{}/{}/{}/{}'.format(work_dir, source, bin_subdir, annox_subdir, annox),
            'result_dir': '{}/{}/{}'.format(work_dir, source, task),
        }
        try:
            if not os.path.exists(self.env['bin_dir']):
                os.makedirs(self.env['bin_dir'])
        except os.error:
            raise LafException(
                "ERROR: could not create bin directory {}".format(self.env['bin_dir']),
                self.stamp, os.error
            )
        try:
            if not os.path.exists(self.env['result_dir']):
                os.makedirs(self.env['result_dir'])
        except os.error:
            raise LafException(
                "ERROR: could not create result directory {}".format(self.env['result_dir']),
                self.stamp, os.error
            )
        self.env['stat_file'] = "{}/{}{}.{}".format(self.env['bin_dir'], self.STAT_NAME, self.COMPILE_NAME, self.TEXT_EXT)
        '''Instance member holding name and location of the statistics file that describes the compiled data'''
        self.env['annox_check_path'] = "{}/{}{}{}.{}".format(self.env['annox_base_bdir'], self.LOG_NAME, self.COMPILE_NAME, annox, self.TEXT_EXT)

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

