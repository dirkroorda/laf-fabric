# -*- coding: utf8 -*-

import os
import os.path
import subprocess
import codecs

import pickle
import array

from graf.graf import Graf
from graf.parse import parse as xmlparse
from graf.model import model as remodel

class GrafCompiler(Graf):
    '''Takes care of the compilation of LAF xml data into binary data.

    There are two stages in compilation:

    * parsing the XML data by means of a SAX parser (a lengthy process)
    * remodeling the parse results in really tight data structures

    '''

    temp_data_items = {}
    '''Holds some data delivered by the parsed that can be thrown away later. The data that we must keep is stored in the object, of course.'''

    def __init__(self, env):
        '''Upon creation, the relevant directories are communicated.

        The initialization of the base class is performed, and we change working directory to the location of the LAF source.

        Args:
            env (str): path information
        '''
        Graf.__init__(self)
        self.env = env
        '''Instance member to hold config settings etc'''
        self.has_compiled = False
        '''Instance member to tell whether compilation has actually taken place'''

        try:
            os.chdir(self.env['data_dir'])
        except os.error:
            raise GrafException("ERROR: could not change to LAF data directory {}".format(self.env['data_dir']),
                self.stamp, os.error
            )
        try:
            if not os.path.exists(self.env['bin_dir']):
                os.makedirs(self.env['bin_dir'])
            if not os.path.exists(self.env['feat_dir']):
                os.makedirs(self.env['feat_dir'])
        except os.error:
            raise GrafException("ERROR: could not create directories for compiled data {}, {}".format(self.env['bin_dir'], format(self.env['feat_dir'])),
                self.stamp, os.error
            )

    def __del__(self):
        Graf.__del__(self)
        
    def parse(self):
        '''Call the XML parser and collect the parse results.

        Some parse results must be remodelled afterwards.
        After remodelling some parse data can be thrown away.
        Only store data that is needed for task execution in the object.

        The actual parsing is done in the module :mod:`parse <graf.parse>`.
        '''
        self.progress("PARSING ANNOTATION FILES")
        parsed_data_items = xmlparse(self.env['data_file'], self.stamp)
        for parsed_data_item in parsed_data_items:
            (label, data, keep) = parsed_data_item
            if keep:
                self.data_items[label] = data
            else:
                self.temp_data_items[label] = data

    def model(self):
        '''Call the remodeler and store the remodeled data in the object.
        '''
        self.progress("MODELING RESULT FILES")
        data_items = {}
        for (label, is_binary) in self.data_items_def.items():
            data_items[label] = self.data_items[label]
        modeled_data_items = remodel(data_items, self.temp_data_items, self.stamp)
        for modeled_data_item in modeled_data_items:
            (label, data) = modeled_data_item
            self.data_items[label] = data

    def write_data(self):
        '''Writes compiled data to disk.

        Compiled data has three possible types:
        
        *0: plain array*
            can be written fast with the :py:meth:`array.tofile` method

        *1: array valued dict*
            a dictionary, keyed by a feature name and with arrays as values

        *2: list of trings*
            can be dumped with the :py:meth:`pickle.dump` method.
        '''
        self.progress("WRITING RESULT FILES")
        self.write_stats()

        for (label, is_binary) in sorted(self.data_items_def.items()):
            data = self.data_items[label]
            self.progress("writing {} ... ".format(label))
            if not is_binary:
                absolute_path = "{}/{}.{}".format(self.env['bin_dir'], label, self.BIN_EXT)
                r_handle = open(absolute_path, "wb")
                pickle.dump(data, r_handle, 2)
                r_handle.close()
            elif is_binary == 1:
                absolute_path = "{}/{}.{}".format(self.env['bin_dir'], label, self.BIN_EXT)
                r_handle = open(absolute_path, "wb")
                data.tofile(r_handle)
                r_handle.close()
            elif is_binary == 2:
                for kind in data:
                    for fname in data[kind]:
                        fname_rep = self.data_items["feat_name_list_{}_int".format(kind)][fname]
                        absolute_feat_path = "{}/{}_{}_{}.{}".format(self.env['feat_dir'], label, kind, fname_rep, self.BIN_EXT)
                        r_handle = open(absolute_feat_path, "wb")
                        data[kind][fname].tofile(r_handle)
                        r_handle.close()

        self.progress("FINALIZATION")

        msg = subprocess.check_output("ls -lh {}".format(self.env['bin_dir']), shell=True)
        self.progress("\n" + msg.decode('utf-8'))

        msg = subprocess.check_output("du -h {}".format(self.env['bin_dir']), shell=True)
        self.progress("\n" + msg.decode('utf-8'))

    def needs_compiling(self):
        '''Checks whether the compiled binary data is still up to date.

        The criterion is whether the generated statistics file at the binary side is newer than the chosen GrAF header file.

        Returns:
            bool: whether the criterion for compiling holds.
        '''
        return not os.path.exists(self.env['stat_file']) or os.path.getmtime(self.env['stat_file']) < os.path.getmtime(self.env['data_file'])

    def compiler(self, force=False):
        '''Manages the complete compilation process.

        Detects the need for compiling, responds to the *force* argument. Then parses, remodels and writes.

        Args:
            force (bool): whether to compile even if the binary data looks up to date.
        '''
        if force or self.needs_compiling():
            self.add_logfile(location=self.env['bin_dir'], name=self.COMPILE_TASK)
            self.progress("BEGIN COMPILE {}".format(self.env['data_file']))
            self.parse()
            self.model()
            self.write_data()
            self.has_compiled = True
            self.progress("END COMPILE")
        else:
            self.progress("COMPILING: UP TO DATE")

