# -*- coding: utf8 -*-

import codecs
import subprocess
import collections

import cPickle
import array

from graf import Graf

class GrafTaskBase(Graf):
    task = None
    source = None
    result_dir = None
    result_files = []

    def __init__(self, bin_dir, result_dir, task, source):
        Graf.__init__(self, bin_dir)
        self.task = task
        self.source = source
        self.result_dir = result_dir
        self.add_logfile(result_dir, task)
        self.progress("INITIALIZATION TASK={} SOURCE={}".format(task, source))

    def __del__(self):
        for handle in self.result_files:
            if handle and not handle.closed:
                handle.close()
        Graf.__del__(self)

    def setup(self, directives):
        self.loader(directives[self.flavour_detail])
        self.init_task()

    def loader(self, directives):
        self.progress("BEGIN LOADING")
        self.read_stats()
        for (label, info) in sorted(self.data_items.items()):
            (is_binary, data) = info 
            b_path = "{}/{}.{}".format(self.bin_dir, label, self.BIN_EXT)
            msg = "loaded {:<30} ... ".format(label)
            b_handle = open(b_path, "rb")
            if is_binary:
                data.fromfile(b_handle, self.stats[label])
            else:
                self.data_items[label][1] = collections.defaultdict(lambda: None,cPickle.load(b_handle))
            msg += u"{:>10}".format(len(self.data_items[label][1]))
            b_handle.close()
            self.progress(msg)
        self.progress("END LOADING")

    def add_result(self, file_name):
        result_file = "{}/{}".format(
            self.result_dir, file_name
        )
        handle = codecs.open(result_file, "w", encoding = 'utf-8')
        self.result_files.append(handle)
        return handle

    def init_task(self):
        self.progress("BEGIN TASK {}".format(self.task))

    def finish_task(self):
        self.progress("END TASK {}".format(self.task))

        msg = subprocess.check_output("ls -lh {}".format(self.result_dir), shell=True)
        self.progress("\n" + msg)

        msg = subprocess.check_output("du -h {}".format(self.result_dir), shell=True)
        self.progress("\n" + msg)

    def next_node(self):
        for node in self.data_items["node_sort"][1]:
            yield node

    def next_node_with_fval(self, label, name, value):
        for node in self.data_items["node_sort"][1]:
            if value == self.Fi(node, label, name):
                yield node

    def int_label(self, rep):
        return self.data_items["annot_label_list_rep"][1][rep]

    def int_fname(self, rep):
        return self.data_items["feat_name_list_rep"][1][rep]

    def int_fval(self, rep):
        return self.data_items["feat_value_list_rep"][1][rep]

    def rep_label(self, intl):
        return self.data_items["annot_label_list_int"][1][intl]

    def rep_fname(self, intl):
        return self.data_items["feat_name_list_int"][1][intl]

    def rep_fval(self, intl):
        return self.data_items["feat_value_list_int"][1][intl]

    def get_mappings(self):
        return (
            self.progress,
            self.data_items["annot_label_list_rep"][1],
            self.data_items["annot_label_list_int"][1],
            self.data_items["feat_name_list_rep"][1],
            self.data_items["feat_name_list_int"][1],
            self.data_items["feat_value_list_rep"][1],
            self.data_items["feat_value_list_int"][1],
            self.next_node,
            self.next_node_with_fval,
            self.Fi,
            self.Fr,
        )

    def getitems(self, data, data_items, elem):
        data_items_index = data[elem - 1]
        n_items = data_items[data_items_index]
        items = {}
        for i in range(n_items):
            items[data_items[data_items_index + 1 + i]] = None
        return items

    def hasitem(self, data, data_items, elem, item):
        return item in self.getitems(data, data_items, elem) 

    def hasitems(self, data, data_items, elem, items):
        these_items = self.getitems(data, data_items, elem) 
        found = None
        for item in items:
            if item in these_items:
                found = item
                break
        return found

