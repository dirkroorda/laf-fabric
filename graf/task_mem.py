# -*- coding: utf8 -*-

import codecs
import subprocess
import collections

import array

from task_base import GrafTaskBase

class GrafTaskMemo(GrafTaskBase):

    def __init__(self, bin_dir, result_dir, task, source, flavour_detail):
        GrafTaskBase.__init__(self, bin_dir, result_dir, task, source)
        self.flavour_detail = flavour_detail
        self.cache_fi = {}
        self.cache_fr = {}

    def Fi(self, node, label, name):
        cache = self.cache_fi
        if (node, label, name) in cache:
            return cache[(node, label, name)]

        feat_label = self.data_items["feat_label"][1]
        feat_name = self.data_items["feat_name"][1]
        feat_value = self.data_items["feat_value"][1]
        node_feat = self.data_items["node_feat"][1]
        node_feat_items = self.data_items["node_feat_items"][1]

        features = self.getitems(node_feat, node_feat_items, node)
        relevant_features = [i for i in features if feat_label[i - 1] == label and feat_name[i - 1] == name]
        the_value = None
        if relevant_features:
            the_value = feat_value[relevant_features[0] - 1]

        cache[(node, label, name)] = the_value
        return the_value

    def Fr(self, node, label, name):
        cache = self.cache_fr
        if (node, label, name) in cache:
            return cache[(node, label, name)]

        feat_value_list_int = self.data_items["feat_value_list_int"][1]
        intl = self.Fi(node, label, name)
        the_value = feat_value_list_int[intl]

        cache[(node, label, name)] = the_value
        return the_value

