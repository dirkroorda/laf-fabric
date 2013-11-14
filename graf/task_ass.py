# -*- coding: utf8 -*-

import os
import codecs
import subprocess
import collections

import cPickle
import array

from task_base import GrafTaskBase

# I wonder whether there is still reason to have these as globals instead of class or instance variables.
# Probably a performance thing.

edge_prop = {}
node_prop = {}

class GrafTaskAssembler(GrafTaskBase):
    '''Class with optimization flavour ``assemble`` or ``assemble_all`` for task execution.

    This flavour uses indexes to speed up feature lookup. The ``plain`` implementations of the methods ``Fi`` and ``Fr``
    first fetch the set of all features that belong to a node and then filter by iterating over them. This implementation
    builds indexes for the features, so that given label and name of a feature its value for a certain node or edge can be
    looked up from a dictionary.

    To this end this class has an extended data loader: it first executes the base class loader :meth:`loader() <graf.task_base.GrafTaskBase.loader>`,
    and continues with index building, saving and/or loading.

    There are two modes of indexing: 

    ``assemble_all``
        index absolutely every feature
    ``assemble``
        index only the features that the task declares as being used (in its ``precompute`` dictionary)

    The latter method is recommended. Although the indexing of all features does not cost much more time than the indexing of a single feature,
    the space requirement can be huge. The reason for the speed behaviour is that even if you index just one feature, the indexer has to
    iterate through all features.

    Features are separated into edge features and node features. They will be indexed separately.

    '''

    def __init__(self, bin_dir, result_dir, task, source, flavour_detail, force):
        '''An object is created with the parameters for the base class :class:`GrafTaskBase <graf.task_base.GrafTaskBase>`
        plus a flavour related parameter.

        Args:
            flavour_detail (str): there are two options in this flavour: ``assemble`` and ``assemble_all``. This parameter specifies the option.
                This value is used to look up the flavour directives in the task script's ``precompute`` dictionary.
        '''

        GrafTaskBase.__init__(self, bin_dir, result_dir, task, source)

        self.flavour_detail = flavour_detail
        '''instance member storing the current flavour'''

        self.force = force
        '''instance member storing whether index building should be forced'''

    def loader(self, directives):
        '''Loads compiled LAF data and assembles indexes.

        See the base method :meth:`loader() <graf.task_base.GrafTaskBase.loader>` for how the compiled LAF data loads.

        After this loading, the index assembling stage method (:meth:`assemble`) is executed. 

        Args: directives (dict): a dictionary of information relevant to loader and assembler.

        .. note:: directives are only used by the assembler.
            Currently the loader does not have any need for directives. Yet they are passed to it, in case the need will arise in the near future.

        '''

        super(GrafTaskAssembler, self).loader(directives)
        self.only_nodes = directives['only_nodes'] if 'only_nodes' in directives else None
        self.only_edges = directives['only_edges'] if 'only_edges' in directives else None
        self.assemble("node", "node_feat", "node_feat_items", node_prop, self.only_nodes)
        self.assemble("edge", "edge_feat", "edge_feat_items", edge_prop, self.only_edges)
        self.progress("END ASSEMBLING")

    def assemble(self, kind, lsource_feat, lsource_feat_items, dest, only):
        '''Assemble an index out of a data source, the data source being either the node features or the edge features.
        
        The case for indexing all features is handled a bit differently from the case for indexing selected features. 

        .. caution:: The result is either a plain hash or a :py:class:`collections.defaultdict`.
            If we index selected features, we write the result to disk eventually, by means of :py:mod:`cPickle`. 
            But a :py:class:`collections.defaultdict` cannot be pickled, so we fall back on a plain dictionary there.

        Args:
            kind (str): indication whether nodes or edges are considered. Only used for progress and log messages.
            lsource_feat (array): see below
            lsource_feat_items (array): together with ``lsource_feat`` the array data for the feature set to be indexed
            dest (dict): the destination dictionary for the index
            only (str): string specifying the features selected for indexing
        '''
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
        '''Assemble indexes for sleected features only.

        The specification of which features are selected is still a string.
        Here we compile it into a dictionary ``only``, keyed with the feature label and then the feature name.
        While doing so we check whether the indexes exist and are all up to date (:meth:`_needs_indexing`).
        If even one index needs to be (re)built, we (re)build all indexes needed and save them.
        Otherwise we load all indexes instead of building and saving them.

        The resulting overall index is a dictionary, keyed with the label and then name.
        The values are dictionaries keyed by the element, with as values the feature values.
        These dictionaries will be pickeled and written to disk as individual indexes.

        Args:
            lsource_feat (array): see below
            lsource_feat_items (array): together with ``lsource_feat`` the array data for the feature set to be indexed
            dest (dict): the destination dictionary for the overall index
            onlystring (str): string specifying the features selected for indexing

        '''
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
        '''Assemble indexes for all features.

        Args:
            lsource_feat (array): see below
            lsource_feat_items (array): together with ``lsource_feat`` the array data for the feature set to be indexed
            dest (dict): the destination dictionary for the index
        '''

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
        '''Save all computed indexes to disk

        Args:
            kind (str): indication whether nodes or edges are considered. Only used for progress and log messages.
            only (dict): dictionary specifying the index selection
            dest (dict): the index material
        '''
        for label in only:
            for name in only[label]:
                index_file = self._index_file(kind, label, name)
                self.progress("saving {}".format(os.path.basename(index_file)))
                p_handle = open(index_file, "wb")
                cPickle.dump(dest[label][name], p_handle, 2)

    def _load_index(self, kind, only, dest):
        '''Load all computed indexes from disk

        Args:
            kind (str): indication whether nodes or edges are considered. Only used for progress and log messages.
            only (dict): dictionary specifying the index selection
            dest (dict): the index material
        '''
        for label in only:
            for name in only[label]:
                index_file = self._index_file(kind, label, name)
                self.progress("loading {}".format(os.path.basename(index_file)))
                p_handle = open(index_file, "rb")
                if label not in dest:
                    dest[label] = {}
                dest[label][name] = cPickle.load(p_handle)

    def _index_file(self, kind, label, name):
        '''Compute the file path of the index for the feature with ``name`` and ``label``.
        '''
        return "{}/index_{}_{}_{}.bin".format(self.bin_dir, kind, self.rep_label(label), self.rep_fname(name))

    def _needs_indexing(self, kind, label, name):
        '''Determine whether the index for the feature with ``name`` and ``label`` exists and is up to date.

        Up to date means that the index is newer than the compiled LAF resource.
        Every compiled LAF resource has a statistics file, and its modification time is used as reference.
        So if you ``touch`` that file, all indexes will be recomputed. But you can also pass the ``--force-index`` flag.

        .. note:: Rebuilding the index.
            There is a difference however. If you say ``--force-index`` when issuing a task, only indexes used by that task 
            will be rebuilt.

            If you ``touch`` the compiled statistics file, every task will recompute its indexes until all indexes have been rebuilt.
        '''

        index_file = self._index_file(kind, label, name)
        return not os.path.exists(index_file) or os.path.getmtime(index_file) < os.path.getmtime(self.stat_file)

    def Fi(self, node, label, name):
        '''Feature value lookup returning the value string representation.
        
        Very different from the plain method :meth:`Fi() <graf.task_plain.GrafTaskPlain.Fi>`.
        In the presence of an index, it is just a dictionary lookup.
        ''' 
        return node_prop[label][name][node]

    def Fr(self, node, label, name):
        '''Feature value lookup returning the value string representation.
        See method :meth:`Fi`.
        ''' 
        feat_value_list_int = self.data_items["feat_value_list_int"][1]
        return feat_value_list_int[node_prop[label][name][node]]

