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
    header_file = None
    temp_data_items = {}

    def __init__(self, graf_dir, graf_header_file, bin_dir):
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
        self.progress("PARSING ANNOTATION FILES")
        parsed_data_items = xmlparse(self.header_file, self.stamp)
        for parsed_data_item in parsed_data_items:
            (label, data, keep) = parsed_data_item
            if keep:
                self.data_items[label][1] = data
            else:
                self.temp_data_items[label] = data

    def model(self):
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
        return not os.path.exists(self.stat_file) or os.path.getmtime(self.stat_file) < os.path.getmtime(self.header_file)

    def compiler(self, force=False):
        if force or self.needs_compiling():
            self.add_logfile(bin_dir, self.COMPILE_TASK)
            self.progress("BEGIN COMPILE {}".format(graf_header_file))
            self.parse()
            self.model()
            self.write_data()
            self.progress("END COMPILE")
        else:
            self.progress("COMPILING: UP TO DATE")

