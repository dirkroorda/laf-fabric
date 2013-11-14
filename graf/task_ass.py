# -*- coding: utf8 -*-

import os
import codecs
import subprocess
import collections

import cPickle
import array

from task_base import GrafTaskBase

edge_prop = {}
node_prop = {}

class GrafTaskAssembler(GrafTaskBase):
    task = None
    result_dir = None
    result_files = []

    def __init__(self, bin_dir, result_dir, task, source, flavour_detail, force):
        '''An object is created with the parameters for the base class :class:`GrafTaskBase <graf.task_base.GrafTaskBase>`
        plus a flavour related parameter.

        Args:
            flavour_detail (str): there are two options in this flavour: ``assemble`` and ``assemble_all``. This parameter specifies the option.
                This value is used to look up the flavour directives in the task script's ``precompute`` dictionary.
        '''
        GrafTaskBase.__init__(self, bin_dir, result_dir, task, source)
        self.flavour_detail = flavour_detail
        self.force = force

    def loader(self, directives):
        super(GrafTaskAssembler, self).loader(directives)
        self.only_nodes = directives['only_nodes'] if 'only_nodes' in directives else None
        self.only_edges = directives['only_edges'] if 'only_edges' in directives else None
        self.assemble("node", "node_feat", "node_feat_items", node_prop, self.only_nodes)
        self.assemble("edge", "edge_feat", "edge_feat_items", edge_prop, self.only_edges)
        self.progress("END ASSEMBLING")

    def assemble(self, kind, lsource_feat, lsource_feat_items, dest, only):
        if only == None:
            self.progress("ASSEMBLING ALL  {} FEATURES ... ".format(kind))
            global node_prop
            node_prop = collections.defaultdict(lambda:collections.defaultdict(lambda:collections.defaultdict(lambda: None)))
            global edge_prop
            edge_prop = collections.defaultdict(lambda:collections.defaultdict(lambda:collections.defaultdict(lambda: None)))
            self.assemble_all(lsource_feat, lsource_feat_items, dest)
        elif only:
            self.progress("ASSEMBLING SOME {} FEATURES ... ".format(kind))
            self.assemble_only(lsource_feat, lsource_feat_items, dest, only, kind)
        else:
            self.progress("ASSEMBLING NO   {} FEATURES ... ".format(kind))

    def assemble_only(self, lsource_feat, lsource_feat_items, dest, onlystring, kind):
        only = collections.defaultdict(lambda:collections.defaultdict(lambda:None))
        labelitems = onlystring.split(" ")

        do_indexing = self.force
        for labelitem in labelitems:
            (label_rep, namestring) = labelitem.split(":")
            label = self.int_label(label_rep)
            names = namestring.split(",")
            for name_rep in names:
                name = self.int_fname(name_rep)
                if label == None or name == None:
                    self.progress("WARNING: {} feature {}.{} not encountered in this source".format(kind, label_rep, name_rep))
                    continue
                only[label][name] = None
                if self._needs_indexing(kind, label, name):
                    do_indexing = True

        if do_indexing:
            self.progress("PRECOMPUTING FEATURE VALUES ...")
            feat_label = self.data_items["feat_label"][1]
            feat_name = self.data_items["feat_name"][1]
            feat_value = self.data_items["feat_value"][1]
            source = self.data_items[lsource_feat][1]
            source_items = self.data_items[lsource_feat_items][1]
            elem = 0
            for to_items in source:
                elem += 1
                n_items = source_items[to_items]
                for i in range(n_items):
                    feat = source_items[to_items + 1 + i]
                    label = feat_label[feat - 1]
                    if label not in only:
                        continue
                    name = feat_name[feat - 1]
                    if name not in only[label]:
                        continue
                    if label not in dest:
                        dest[label] = {}
                    if name not in dest[label]:
                        dest[label][name] = {}
                    dest[label][name][elem] = feat_value[feat - 1]
            self.progress("SAVING FEATURE VALUES TO DISK ...")
            self._save_index(kind, only, dest)
        else:
            self.progress("LOADING FEATURE VALUES FROM DISK ...")
            self._load_index(kind, only, dest)

    def assemble_all(self, lsource_feat, lsource_feat_items, dest):
        feat_label = self.data_items["feat_label"][1]
        feat_name = self.data_items["feat_name"][1]
        feat_value = self.data_items["feat_value"][1]
        source = self.data_items[lsource_feat][1]
        source_items = self.data_items[lsource_feat_items][1]
        elem = 0
        for to_items in source:
            elem += 1
            n_items = source_items[to_items]
            for i in range(n_items):
                feat = source_items[to_items + 1 + i]
                dest[feat_label[feat - 1]][feat_name[feat - 1]][elem] = feat_value[feat - 1]

    def _save_index(self, kind, only, dest):
        for label in only:
            for name in only[label]:
                index_file = self._index_file(kind, label, name)
                self.progress("saving {}".format(os.path.basename(index_file)))
                p_handle = open(index_file, "wb")
                cPickle.dump(dest[label][name], p_handle, 2)

    def _load_index(self, kind, only, dest):
        for label in only:
            for name in only[label]:
                index_file = self._index_file(kind, label, name)
                self.progress("loading {}".format(os.path.basename(index_file)))
                p_handle = open(index_file, "rb")
                if label not in dest:
                    dest[label] = {}
                dest[label][name] = cPickle.load(p_handle)

    def _index_file(self, kind, label, name):
        return "{}/index_{}_{}_{}.bin".format(self.bin_dir, kind, self.rep_label(label), self.rep_fname(name))

    def _needs_indexing(self, kind, label, name):
        index_file = self._index_file(kind, label, name)
        return not os.path.exists(index_file) or os.path.getmtime(index_file) < os.path.getmtime(self.stat_file)

    def Fi(self, node, label, name):
        '''Feature value lookup returning the value string representation. See the plain method :meth:`Fi() <graf.task_plain.GrafTaskPlain.Fi>`.
        ''' 
        return node_prop[label][name][node]

    def Fr(self, node, label, name):
        '''Feature value lookup returning the value string representation. See the plain method :meth:`Fi() <graf.task_plain.GrafTaskPlain.Fi>`.
        ''' 
        feat_value_list_int = self.data_items["feat_value_list_int"][1]
        return feat_value_list_int[node_prop[label][name][node]]

