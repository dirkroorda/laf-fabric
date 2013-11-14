# -*- coding: utf8 -*-

import os
import os.path
import subprocess
import codecs

import cPickle
import array

from graf import Graf
from parse import parse as xmlparse
from model import model as remodel

class GrafCompiler(Graf):
    '''Takes care of the compilation of LAF xml data into binary data.

    There are two stages in compilation:

    * parsing the XML data by means of a SAX parser (a lengthy process)
    * remodeling the parse results in really tight data structures

    '''
    header_file = None
    '''Holds the chosen source, i.e. the GrAF header file used to draw in the LAF data.'''

    temp_data_items = {}
    '''Holds some data delivered by the parsed that can be thrown away later. The data that we must keep is stored in the object, of course.'''

    def __init__(self, graf_dir, graf_header_file, bin_dir):
        '''Upon creation, the relevant directories are communicated.

        The initialization of the base class is performed, and we change working directory to the location of the LAF source.

        Args:
            graf_dir (str): the directory where the LAF resource resides.
            graf_header_file (str): the GrAF header file from which we read which files are to be considered part of the LAF resource.
            bin_dir (str): the relative name of the directory where the compiled binary data is to be stored.
        '''
        Graf.__init__(self, bin_dir)
        self.header_file = graf_header_file

        try:
            os.chdir(graf_dir)
        except os.error:
            raise GrafException("ERROR: could not create result directory {}".format(bin_dir),
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
        parsed_data_items = xmlparse(self.header_file, self.stamp)
        for parsed_data_item in parsed_data_items:
            (label, data, keep) = parsed_data_item
            if keep:
                self.data_items[label][1] = data
            else:
                self.temp_data_items[label] = data

    def model(self):
        '''Call the remodeler and store the remodeled data in the object.
        '''
        self.progress("MODELING RESULT FILES")
        data_items = {}
        for (label, data_item) in self.data_items.items():
            if len(data_item) > 1:
                data_items[label] = data_item[1] 
        modeled_data_items = remodel(data_items, self.temp_data_items, self.stamp)
        for modeled_data_item in modeled_data_items:
            (label, data) = modeled_data_item
            self.data_items[label][1] = data

    def write_data(self):
        '''Writes compiled data to disk.

        Compiled data is either in array shape, and written fast with the :py:meth:`array.tofile` method, or it is
        a list of strings, in which case it is dumped with the :py:meth:`cPickle.dump` method.
        '''
        self.progress("WRITING RESULT FILES")
        self.write_stats()

        for (label, info) in sorted(self.data_items.items()):
            (is_binary, data) = info 
            absolute_path = "{}/{}.{}".format(self.bin_dir, label, self.BIN_EXT)
            r_handle = open(absolute_path, "wb")
            self.progress("writing ({} ... ".format(label))
            if is_binary:
                data.tofile(r_handle)
            else:
                cPickle.dump(data, r_handle, 2)
            r_handle.close()

        self.progress("FINALIZATION")

        msg = subprocess.check_output("ls -lh {}".format(self.bin_dir), shell=True)
        self.progress("\n" + msg)

        msg = subprocess.check_output("du -h {}".format(self.bin_dir), shell=True)
        self.progress("\n" + msg)

    def needs_compiling(self):
        '''Checks whether the compiled binary data is still up to date.

        The criterion is whether the generated statistics file at the binary side is newer than the chosen GrAF header file.
        '''
        return not os.path.exists(self.stat_file) or os.path.getmtime(self.stat_file) < os.path.getmtime(self.header_file)

    def compiler(self, force=False):
        '''Manages the complete compilation process.

        Detects the need for compiling, responds to the ``force`` argument. Then parses, remodels and writes.

        Args:
            force (bool): whether to compile even if the binary data looks up to date.
        '''
        if force or self.needs_compiling():
            self.add_logfile(bin_dir, self.COMPILE_TASK)
            self.progress("BEGIN COMPILE {}".format(graf_header_file))
            self.parse()
            self.model()
            self.write_data()
            self.progress("END COMPILE")
        else:
            self.progress("COMPILING: UP TO DATE")

