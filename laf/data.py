import os
import glob
import time
import array
import pickle
import gzip
from .names import Names
from .parse import parse
from .model import model

GZIP_LEVEL = 2

class LafException(Exception):
    def __init__(self, message, stamp, Errors):
        Exception.__init__(self, message)
        stamp.Emsg(message)
        raise

class LafData(object):
    '''Manage the compiling and loading of LAF/GraF data.'''

    def __init__(self):
        self.log = None
        self.data_items = {}

    def adjust_all(self, source, annox, task, req_items, force):
        '''Load manager.

        Load and clear data so that the current task has all it needs and no more.
        Compile outdated binary data just before loading.
        '''
        self.names.setenv(source, annox, task)
        env = self.names.env
        try:
            if not os.path.exists(env['m_compiled_dir']): os.makedirs(env['m_compiled_dir'])
        except os.error:
            raise LafException("could not create bin directory {}".format(env['m_compiled_dir']), self.stamp, os.error)
        if annox != env['empty']:
            try:
                if not os.path.exists(env['a_compiled_dir']): os.makedirs(env['a_compiled_dir'])
            except os.error:
                raise LafException("could not create bin directory {}".format(env['a_compiled_dir']), self.stamp, os.error)
        try:
            if not os.path.exists(env['task_dir']): os.makedirs(env['task_dir'])
        except os.error:
            raise LafException("could not create result directory {}".format(env['task_dir']), self.stamp, os.error)
        correct = True
        if not self._compile_all(force): correct = False
        if not self._load_all(req_items): correct = False
        self._add_logfile()
        return correct

    def finish_task(self, show=True):
        '''Close all open files that have been opened by the API'''
        task_dir = self.names.env['task_dir']
        for handle in self.result_files:
            if handle and not handle.closed: handle.close()
        self.result_files = []
        self._flush_logfile()
        mg = []
        if show:
            self.stamp.Nmsg("Results directory:\n{}".format(task_dir))
            for name in sorted(os.listdir(path=task_dir)):
                path = "{}/{}".format(task_dir, name) 
                size = os.path.getsize(path)
                mtime = time.ctime(os.path.getmtime(path))
                mg.append("{:<30} {:>12} {}".format(name, size, mtime))
            self.stamp.Nmsg("\n" + "\n".join(mg), withtime=False)
        self._finish_logfile()

    def _finish_logfile(self):
        try: self.log.close()
        except: pass
        self.stamp.disconnect_log()
        self.log = None

    def _flush_logfile(self):
        try: self.log.flush()
        except: pass

    def _add_logfile(self, compile=None):
        env = self.names.env
        log_dir = env['task_dir'] if compile == None else env["{}_compiled_dir".format(compile)]
        log_path = env['log_path'] if compile == None else env["{}_compiled_path".format(compile)]
        try:
            if not os.path.exists(log_dir): os.makedirs(log_dir)
        except os.error:
            raise LafException("could not create log directory {}".format(log_dir), self.stamp, os.error)
        self.log = open(log_path, "w", encoding="utf-8")
        self.stamp.connect_log(self.log)
        self.stamp.Nmsg("LOGFILE={}".format(log_path))

    def _compile_all(self, force):
        env = self.names.env
        compile_uptodate = {}
        compile_uptodate['m'] = not os.path.exists(env['m_source_path']) or (
                os.path.exists(env['m_compiled_path']) and
                os.path.getmtime(env['m_compiled_path']) >= os.path.getmtime(env['m_source_path'])
            )

        uptodate = True
        for afile in glob.glob('{}/*.xml'.format(env['a_source_dir'])):
            this_uptodate = env['annox'] == env['empty'] or (
                os.path.exists(env['a_compiled_path']) and
                os.path.getmtime(env['a_compiled_path']) >= os.path.getmtime(afile)
            )
            if not this_uptodate:
                uptodate = False
                break
        compile_uptodate['a'] = uptodate
        has_compiled = False
        for origin in ['m', 'a']:
            if not compile_uptodate[origin] or force[origin] or (has_compiled and env['annox'] != env['empty']):
                self.stamp.Nmsg("BEGIN COMPILE {}: {}".format(origin, env['source'] if origin == 'm' else env['annox']))
                self._clear_origin(origin)
                if origin == 'a': self._load_extra(['mXnf ', 'mXef '])
                self._compile_origin(origin)
                has_compiled = True
                self.stamp.Nmsg("END   COMPILE {}: {}".format(origin, env['source'] if origin == 'm' else env['annox']))
            else: self.stamp.Dmsg("COMPILING {}: UP TO DATE".format(origin))
        if has_compiled:
            for origin in ['m', 'a']:
                self._clear_origin(origin)
            self.names.setenv(env['source'], env['annox'], env['task'])

    def _compile_origin(self, origin):
        env = self.names.env
        the_log_file = env['compiled_file']
        the_log_dir = env['{}_compiled_dir'.format(origin)]
        self._add_logfile(compile=origin)
        self._parse(origin)
        self._model(origin)
        self._store_origin(origin)
        self._finish_logfile()

    def _clear_origin(self, origin):
        for dkey in self.data_items:
            (dorigin, dgroup, dkind, ddir, dcomps) = Names.decomp_full(dkey)
            if dorigin == origin: self._clear_file(dkey)

    def _clear_file(self, dkey):
        if dkey in self.data_items: del self.data_items[dkey]

    def _load_all(self, req_items):
        correct = True
        dkeys = self.names.request_files(req_items)
        self.prep_items = []
        for dkey in dkeys['keep']: self.stamp.Dmsg("keep {}".format(Names.dmsg(dkey))) 
        for dkey in dkeys['clear']:
            self.stamp.Dmsg("clear {}".format(Names.dmsg(dkey))) 
            self._clear_file(dkey)
        for dkey in dkeys['load']:
            self.stamp.Dmsg("load {}".format(Names.dmsg(dkey))) 
            ism = self.names.dinfo(dkey)[0]
            this_correct = self._load_file(dkey, accept_missing=not ism)
            if not this_correct: correct = False
        for dkey in dkeys['prep']: self.prep_items.append(dkey)
        return correct

    def _load_extra(self, dkeys):
        correct = True
        for dkey in dkeys:
            self.stamp.Dmsg("load {}".format(Names.dmsg(dkey))) 
            ism = self.names.dinfo(dkey)[0]
            this_correct = self._load_file(dkey, accept_missing=not ism)
            if not this_correct: correct = False
        return correct

    def prepare_all(self, api, prepare_dict):
        correct = True
        self.api = api
        self.prepare_dict = prepare_dict
        for dkey in self.prep_items:
            self.stamp.Dmsg("prep {}".format(Names.dmsg(dkey))) 
            this_correct = self._load_file(dkey, accept_missing=False)
            if not this_correct: correct = False
        return correct

    def _load_file(self, dkey, accept_missing=False):
        self.stamp.Dmsg("load {}".format(Names.dmsg(dkey))) 
        (ism, dloc, dfile, dtype, dprep) = self.names.dinfo(dkey)
        dpath = "{}/{}".format(dloc, dfile)
        if dprep:
            if dkey not in self.prepare_dict:
                self.stamp.Wmsg("Cannot prepare data for {}. No preparation method available.".format(Names.dmsg(dkey)))
                return False
            (method, method_source) = self.prepare_dict[dkey]
            up_to_date = os.path.exists(dpath) and os.path.getmtime(dpath) >= os.path.getmtime(method_source)
            if not up_to_date:
                self.stamp.Dmsg("PREPARING {}".format(Names.dmsg(dkey)))
                newdata = method(self.api)
                self.stamp.Dmsg("WRITING {}".format(Names.dmsg(dkey)))
                self.data_items[dkey] = newdata
                self._store_file(dkey)
                return True
        if not os.path.exists(dpath):
            if not accept_missing:
                self.stamp.Emsg("Cannot load data for {}: File does not exist: {}.".format(Names.dmsg(dkey), dpath))
            return accept_missing
        newdata = None
        if dtype == 'arr':
            newdata = array.array('I')
            handle = gzip.open(dpath, "rb")
            contents = handle.read()
            handle.close
            newdata.frombytes(contents)
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

    def _store_origin(self, origin):
        self.stamp.Nmsg("WRITING RESULT FILES for {}".format(origin))
        data_items = self.data_items
        for dkey in data_items:
            (dorigin, dgroup, dkind, ddir, dcomps) = Names.decomp_full(dkey)
            if dorigin == origin: self._store_file(dkey)

    def _store_file(self, dkey):
        (ism, dloc, dfile, dtype, dprep) = self.names.dinfo(dkey)
        dpath = "{}/{}".format(dloc, dfile)
        if dpath == None: return
        thedata = self.data_items[dkey]
        self.stamp.Dmsg("write {}".format(Names.dmsg(dkey))) 
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

    def _parse(self, origin):
        self.stamp.Nmsg("PARSING ANNOTATION FILES")
        env = self.names.env
        source_dir = env['{}_source_dir'.format(origin)]
        source_path = env['{}_source_path'.format(origin)]
        compiled_dir = env['{}_compiled_dir'.format(origin)]
        self.cur_dir = os.getcwd()
        if not os.path.exists(source_path):
            raise LafException("LAF header does not exists {}".format(source_path), self.stamp, os.error)
        try:
            os.chdir(source_dir)
        except os.error:
            raise LafException("could not change to LAF source directory {}".format(source_dir), self.stamp, os.error)
        try:
            if not os.path.exists(compiled_dir): os.makedirs(compiled_dir)
        except os.error:
            os.chdir(self.cur_dir)
            raise LafException("could not create directory for compiled source {}".format(compiled_dir), self.stamp, os.error)
        parse(
            origin,
            env['{}_source_path'.format(origin)],
            self.stamp,
            self.data_items,
        )
        os.chdir(self.cur_dir)

    def _model(self, origin):
        self.stamp.Nmsg("MODELING RESULT FILES")
        model(origin, self.data_items, self.stamp)

    def __del__(self):
        self.stamp.Nmsg("END")
        for handle in (self.log,):
            if handle and not handle.closed: handle.close()

