# -*- coding: utf8 -*-

import codecs
import subprocess
import collections

import cPickle
import array

from graf import Graf

class GrafTaskBase(Graf):
    '''Base class for task execution.

    All classes that implement flavours of optimizations are derived from this class.
    The methods in this class are either low level methods or methods common to all derived classes.
    The methods in the derived classes that are implemented differently are not defined in this class.

    .. note:: The methods ``Fi`` and ``Fr`` must be defined in all derived classes.

        The base class method :meth:`get_mappings` returns a set of code references, so that the task can give those methods
        convenient, local names. It also returns references to ``Fi`` and ``Fr``, despite the fact that these are only defined in
        derived classes.

    '''

    task = None
    source = None
    result_dir = None
    result_files = []

    def __init__(self, bin_dir, result_dir, task, source):
        '''Upon creation, an object is passes the locations for his source and destination data.
        
        Args:
            bin_dir (str): piece of the file path between the ``result_dir`` and the compiled LAF binary files
            result_dir (str): path to the result directory
            source (str): name of the selected source (a *GrAF header file*), usually specified by the user on the command line
        '''
        Graf.__init__(self, bin_dir)
        self.task = task
        self.source = source
        self.result_dir = result_dir
        self.add_logfile(result_dir, task)
        self.progress("INITIALIZATION TASK={} SOURCE={}".format(task, source))

    def __del__(self):
        '''Upon destruction, all file handles used by the task will be closed.
        '''

        for handle in self.result_files:
            if handle and not handle.closed:
                handle.close()
        Graf.__del__(self)

    def setup(self, directives):
        '''Set up everything that is needed to run a task.
        That is: load the compiled data, follow the directives of the chosen flavour of optimization, and initialize the task itself.

        Args:
            directives (dict): a dictionary of information items relevant to the chosen optimization flavour. This information is read from the chosen task (the ``precompute`` dictionary).
        '''
        self.loader(directives[self.flavour_detail])
        self.init_task()

    def loader(self, directives):
        '''Loads the compiled LAF data.

        This is the standard loader.
        In order to succesfully load the arrays with compiled data, the loader has to know how many items the arrays have on before hand.
        That is why the compilation process has gathered statistics and written them to a statistics file.
        
        Args:
            directives (dict): Not yet used.
        '''
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
        '''Opens a file for writing and stores the handle.

        Every task is advised to use this method for opening files for its output.
        The file will be closed by the workbench when the task terminates.

        Args:
            file_name (str): name of the output file. Its location is the result directory for this task and this source.
        '''
        result_file = "{}/{}".format(
            self.result_dir, file_name
        )
        handle = codecs.open(result_file, "w", encoding = 'utf-8')
        self.result_files.append(handle)
        return handle

    def init_task(self):
        '''Initializes the current task.

        Very trivial initialization: just issue a progress message.
        '''
        self.progress("BEGIN TASK {}".format(self.task))

    def finish_task(self):
        '''Finalizes the current task.

        There will be a progress message, and a directory listing of the result directory, for the convenience of the user.
        '''

        self.progress("END TASK {}".format(self.task))

        msg = subprocess.check_output("ls -lh {}".format(self.result_dir), shell=True)
        self.progress("\n" + msg)

        msg = subprocess.check_output("du -h {}".format(self.result_dir), shell=True)
        self.progress("\n" + msg)

    def next_node(self):
        '''API: iterator of all nodes in primary data order.

        Each call returns the next node. The iterator walks through all nodes.
        The order is implied by the attachment of nodes to the primary data, which is itself linearly ordered.
        This order is explained in the :ref:`guidelines for task writing <node-order>`.
        '''
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
        '''Return references to methods of :class:`GrafTaskBase` or its derived classes.

        The caller can give convenient, local names to these methods. It also saves method lookup,
        at least, I think so.
        ''' 
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

