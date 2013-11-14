# -*- coding: utf8 -*-

import codecs
import subprocess
import collections

import array

from task_base import GrafTaskBase

class GrafTaskPlain(GrafTaskBase):
    '''Class with optimization flavour ``plain`` for task execution.

    This flavour is in fact the *unoptimized* way of doing things.
    The feature lookup methods are implemented straightforwardly on the basis of the compiled data structures,
    without any precomputing or memoization.
    '''

    def __init__(self, bin_dir, result_dir, task, source, flavour_detail):
        '''An object is created with the parameters for the base class :class:`GrafTaskBase <graf.task_base.GrafTaskBase>`
        plus a flavour related parameter ``flavour_detail`` that is not relevant for this flavour.
        '''
        GrafTaskBase.__init__(self, bin_dir, result_dir, task, source)
        self.flavour_detail = flavour_detail

    def Fi(self, node, label, name):
        '''Feature value lookup returning the value code.

        If a node does not carry the specified feature, the method returns ``None``.

        .. caution:: Multiple features with the same label and name on the same node.
            We consider this a design error in the LAF resource. You should not add features with the same labels and names as existing features.
            In full LAF this can be solved by using annotation spaces, which we have not implemented. But even then, had we implemented it, then the
            situation could arise that we have multiple features with the same annotation space and label and the same name. The that would be a design
            error.
            When the error occurs, we do not signal it, we just return the value of the first feature that we happen to see.

        Args:
            node (int): the integer identifying the node.
            label (int): the integer specifying the annotation label of the feature in question
            name (int): the integer specifying the name of the feature in question

        Returns:
            the integer of the value that the given node carries for the specified feature, or ``None`` if the node does not carry that feature.

        It is messy work to dig out the desired value code from the compiled data.
        First we give the relevant arrays local names. Then we fetch *all* feature items that target the node in question.
        Finally we filter those according to annotation label and feature name. We return the first candidate.
        ''' 
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
        return the_value

    def Fr(self, node, label, name):
        '''Feature value lookup returning the value string representation.

        It calls :meth:`Fi` to do the messy work of digging up the right value code out of the compiled data.
        Then it fetches the representation by looking in the list of value representations. 

        Args:
            node (int): the integer identifying the node.
            label (int): the integer specifying the annotation label of the feature in question
            name (int): the integer specifying the name of the feature in question

        Returns:
            the string representation of the value that the given node carries for the specified feature
        ''' 
        feat_value_list_int = self.data_items["feat_value_list_int"][1]
        intl = self.Fi(node, label, name)
        return feat_value_list_int[intl]

