# -*- coding: utf8 -*-

import os
import os.path
import subprocess
import codecs

from .graf import Graf
from .parse import parse as xmlparse
from .model import model as remodel

class GrafCompiler(Graf):
    '''Takes care of the compilation of LAF xml data into binary data.

    There are two stages in compilation:

    * parsing the XML data by means of a SAX parser (a lengthy process)
    * remodeling the parse results in really tight data structures

    '''

    temp_data_items = {}
    '''Holds some data delivered by the parsed that can be thrown away later.
    The data that we must keep is stored in the object, of course.
    '''

    def __init__(self, env, settings):
        '''Upon creation, the relevant directories are communicated.

        The initialization of the base class is performed, and we change working directory to the location of the LAF source.

        Args:
            env (str):
                path information
        '''
        Graf.__init__(self, settings)

        self.env = env
        '''Holds the context information for the current task, such as chosen source and task.
        '''

        self.has_compiled = {'common': False, 'annox': False}
        '''Instance member to tell whether compilation has actually taken place'''

    def __del__(self):
        Graf.__del__(self)

    def parse(self, what):
        '''Call the XML parser and collect the parse results.

        Some parse results must be remodelled afterwards.
        After remodelling some parse data can be thrown away.
        Only store data that is needed for task execution in the object.

        The actual parsing is done in the module :mod:`parse <graf.parse>`.

        Args:
            what (str):
                whether to parse common data (``common``) or an extra annotation package (``annox``)
        '''
        self.progress("PARSING ANNOTATION FILES")
        self.cur_dir = os.getcwd()

        the_data_file = self.env['data_file'] if what == 'common' else self.env['annox_file']
        the_data_dir = self.env['data_dir'] if what == 'common' else self.env['annox_dir']
        the_bin_dir = self.env['feat_dir'] if what == 'common' else self.env['annox_bdir']

        try:
            os.chdir(the_data_dir)
        except os.error:
            raise GrafException("ERROR: could not change to LAF data directory {}".format(the_data_dir),
                self.stamp, os.error
            )
        try:
            if not os.path.exists(the_bin_dir):
                os.makedirs(the_bin_dir)
        except os.error:
            raise GrafException("ERROR: could not create directory for compiled data {}".format(the_bin_dir),
                self.stamp, os.error,
            )
        
        xmlitems = None
        if what != 'common':
            self.adjust_data('xid', {'xmlids': {'node': True, 'edge': True}})
            xmlitems = self.data_items['xid_int']

        parsed_data_items = xmlparse(the_data_file, self.stamp, xml=xmlitems)
        for parsed_data_item in parsed_data_items:
            (label, data, keep) = parsed_data_item
            if keep:
                self.data_items[label] = data
            else:
                self.temp_data_items[label] = data

        os.chdir(self.cur_dir)

    def model(self, what):
        '''Call the remodeler and store the remodeled data in the object.
        Args:
            what (str):
                whether to parse common data (``common``) or an extra annotation package (``annox``)
        '''
        self.progress("MODELING RESULT FILES")
        data_items = {}
        modeled_data_items = remodel(self.data_items, self.temp_data_items, self.stamp)
        for modeled_data_item in modeled_data_items:
            (label, data) = modeled_data_item
            self.data_items[label] = data

    def write_data(self, what):
        '''Writes compiled data to disk.

        Args:
            what (str):
                whether to parse common data (``common``) or an extra annotation package (``annox``)
        '''
        if what == 'annox':
            return
        self.progress("WRITING RESULT FILES")
        if what == 'common':
            self.write_stats()
        self.store_all(what)
        self.progress("FINALIZATION")

        the_bin_dir = self.env['bin_dir'] if what == 'common' else self.env['annox_bdir']

        msg = subprocess.check_output("ls -lh {}".format(the_bin_dir), shell=True)
        self.progress("\n" + msg.decode('utf-8'))

        msg = subprocess.check_output("du -h {}".format(the_bin_dir), shell=True)
        self.progress("\n" + msg.decode('utf-8'))

    def needs_compiling(self, what):
        '''Checks whether the compiled binary data is still up to date.

        The criterion is whether the generated statistics file at the binary side is newer than the chosen GrAF header file.
        If there is no GrAF header file, then it is assumed that no LAF source is present on the system, and the answer will 
        be no.

        Args:
            what (str):
                whether to parse common data (``common``) or an extra annotation package (``annox``)

        Returns:
            bool:
                whether the criterion for compiling holds.
        '''
        if what == 'common':
            needs_compiling = os.path.exists(self.env['data_path']) and (
                not os.path.exists(self.env['stat_file']) or
                os.path.getmtime(self.env['stat_file']) < os.path.getmtime(self.env['data_path'])
            )
        else:
            needs_compiling = self.env['annox'] != self.settings['annox']['empty'] and os.path.exists(self.env['annox_path']) and (
                not os.path.exists(self.env['annox_check_path']) or
                os.path.getmtime(self.env['annox_check_path']) < os.path.getmtime(self.env['annox_path'])
            )
        return needs_compiling

    def compiler_data(self, what, force):
        '''Manages the compilation process for either the common data or extra annotation files.

        Detects the need for compiling, responds to the *force* argument. Then parses, remodels and writes.

        Args:
            what (str):
                whether to parse common data (``common``) or an extra annotation package (``annox``)
            force (bool):
                whether to compile even if the binary data looks up to date.
        '''
        if force or self.needs_compiling(what):
            the_log_file = self.COMPILE_TASK if what == 'common' else self.env['annox']
            the_log_dir = self.env['bin_dir'] if what == 'common' else self.env['annox_base_bdir']
            the_data_file = self.env['data_file'] if what == 'common' else self.env['annox_file']

            self.add_logfile(the_log_dir, the_log_file)
            self.progress("BEGIN COMPILE {}".format(the_data_file))
            self.parse(what)
            if what == 'common':
                self.model(what)
            self.write_data(what)
            self.progress("END COMPILE")
            self.finish_logfile()
        else:
            self.progress("COMPILING {}: UP TO DATE".format(what))

    def compiler(self, force=False):
        '''Manages the complete compilation process.
        '''
        self.compiler_data('common', force)
        self.compiler_data('annox', force)

