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
    BIN_EXT = 'bin'
    TEXT_EXT = 'txt'
    LOG_NAME = '__log__'
    STAT_NAME = '__stat__'
    COMPILE_TASK = 'compile'

    bin_dir = None
    stamp = None
    log = None
    stat_file = None
    clog_file = None
    stats = None
    data_items = None

    def __init__(self, bin_dir):
        self.stamp = Timestamp()
        self.data_items = {
            "annot_label_list_rep": [False, {}],
            "annot_label_list_int": [False, {}],
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

        self.bin_dir = bin_dir
        try:
            if not os.path.exists(bin_dir):
                os.makedirs(bin_dir)
        except os.error:
            raise GrafException(
                "ERROR: could not create bin directory {}".format(bin_dir),
                self.stamp, os.error
            )
        self.stat_file = "{}/{}{}.{}".format(
            bin_dir, self.STAT_NAME, self.COMPILE_TASK, self.TEXT_EXT
        )

    def __del__(self):
        self.stamp.progress("END")
        for handle in (
            self.log,
        ):
            if handle and not handle.closed:
                handle.close()

    def add_logfile(self, log_dir, task):
        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        except os.error:
            raise GrafException(
                "ERROR: could not create log directory {}".format(log_dir),
                self.stamp, os.error
            )

        log_file = "{}/{}{}.{}".format(
            log_dir, self.LOG_NAME, task, self.TEXT_EXT
        )
        self.log = codecs.open(log_file, "w", encoding = 'utf-8')
        self.stamp.connect_log(self.log)
        self.stamp.progress("LOGFILE={}".format(log_file))

    def progress(self, msg):
        self.stamp.progress(msg)

    def write_stats(self):
        stat = codecs.open(self.stat_file, "w", encoding = 'utf-8')
        for (label, info) in self.data_items.items():
            (is_binary, data) = info 
            stat.write(u"{}={}\n".format(label, len(data)))
        stat.close()

    def read_stats(self):
        stat = codecs.open(self.stat_file, "r", encoding = 'utf-8')
        self.stats = {}
        for line in stat:
            (label, count) = line.rstrip("\n").split("=")
            self.stats[label] = int(count)
        stat.close()

