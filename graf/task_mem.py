# -*- coding: utf8 -*-

import codecs
import subprocess
import collections

import array

from task_base import GrafTaskBase

class GrafTaskMemo(GrafTaskBase):
    '''Class with optimization flavour ``memo`` for task execution.

    This flavour implements memoization for feature lookup. A cache is being used to store the values for looked up features.

    Evaluation: so far memoization turns out to be not useful, even harmful. The reason is that a lot of features only have to be looked up once. So:

    * we incur the processing overhead of the logic of caching
    * we incur a huge memory overhead of cached results that will never be used

    Anyway, I keep the flavour alive:
    
    * just to be able to show the negative effects
    * for the case that some future task does benefit from it

    '''

    def __init__(self, bin_dir, result_dir, task, source, flavour_detail):
        '''An object is created with the parameters for the base class :class:`GrafTaskBase <graf.task_base.GrafTaskBase>`
        plus a flavour related parameter ``flavour_detail`` that is not relevant for this flavour.
        '''
        GrafTaskBase.__init__(self, bin_dir, result_dir, task, source)
        self.flavour_detail = flavour_detail
        self.cache_fi = {}
        self.cache_fr = {}

    def Fi(self, node, label, name):
        '''Feature value lookup returning the value code. See the plain method :meth:`Fi() <graf.task_plain.GrafTaskPlain.Fi>`.

        .. caution:: Code duplication.

            Part of the code for this method is identical to the code in :meth:`Fi() <graf.task_plain.GrafTaskPlain.Fi>`.
            However, we do not call that method, because method calls are expensive. We just copy the code.
        ''' 
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
        '''Feature value lookup returning the value string representation. See the plain method :meth:`Fi() <graf.task_plain.GrafTaskPlain.Fi>`.
        ''' 
        cache = self.cache_fr
        if (node, label, name) in cache:
            return cache[(node, label, name)]

        feat_value_list_int = self.data_items["feat_value_list_int"][1]
        intl = self.Fi(node, label, name)
        the_value = feat_value_list_int[intl]

        cache[(node, label, name)] = the_value
        return the_value

