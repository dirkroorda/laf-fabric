import os
import os.path
import shutil
import glob
import collections

import array
import pickle
import gzip

from .timestamp import Timestamp
from .parse import parse as xmlparse
from .model import model as remodel

class GrafException(Exception):
    def __init__(self, message, stamp, Errors):
        Exception.__init__(self, message)
        stamp.progress(message)
        raise

class Graf(object):
    '''Base class for compiling LAF resources and running analytic tasks on them.

    The data of this class represents the compiled data on the basis of which tasks can run.
    This data is created by the method :meth:`compile_all` in this class.

    The :class:`Graf` knows the structure of the data, and how to load it into memory.
    It can also see what it loaded and what not, and it can compute conditions that require compiling and (re)loading.

    There are various kinds of data, by their shape and by their function.
    The instance member *data_items_def* contains their declarations in the
    form of an ordered dictionary, keyed by data_group.

    The instance member *data_items* contains the data itself.

    The types of data are

    ``x_mapping``, group ``xmlids``:
        mappings between xml identifiers as they occur in the original LAF source
        and the node/edge numbers in the compiled data.
        There are two dictionaries: ``xid_int`` (going from xml to integer) and
        ``xid_rep`` (going from integer to xml).
        Both contain two dictionaries, one for nodes and one for edges separately.

    ``string``:
        Just an unicode string. Used for ``data``, the primary data.

    ``array``, group ``common``:
        Simply tables of integer values. 
        Most of the data common to all tasks is in ``array`` s and ``double_array`` s (see below).

        ``edges_from`` and ``edges_to``:
            At position ``i``: the source and the target of edge ``i``.

    ``i_array``, group ``common``:
        As ``array`` plus a generated inverse of the array, giving the array index for each value.

        ``node_sort`` and ``node_sort_inv``:
            All nodes ordered as induced by the region anchors.
            Nodes that start before others, come before them, 
            nodes that have equal start points are ordered such that the one with the later end point
            comes first. If both have equal end points, the order is arbitrary.
            If the nodes correspond to objects in a hierarchy without gaps, then embedding objects come before
            embedded objects.
            The inverse is handy for sorting subsets of nodes: it gives for each node its rank in the sort order.

    ``double_array``, group ``common``: 
        Twin arrays representing a list of records where records may have variable length.
        The primary array is has the name given, and contains at position ``i`` the starting
        point for record ``i`` in the secondary array.
        The record in the second array starts with a cell containing the length of the record,
        and then so many cells of information.
        This array has as its name the name of the primary array plus ``_items``.

        ``node_anchor`` and ``node_anchor_items``:
            For node ``i`` the record ``i`` consists of all anchor ranges that this node is linked to.
            The anchor range for a node is a sequence with even length of numbers that are the start and end anchors
            of primary data ranges that the node is linked to.
            The ranges have been normalized: they are maximal, non-overlapping, ordered by starting position.

        ``node_out`` and ``node_out_items``:
            For node ``i`` the record ``i`` consists of all outgoing edges from this node.

        ``node_in`` and ``node_in_items``:
            For node ``i`` the record ``i`` consists of all incoming edges into this node.

    ``feature_mapping``, group ``feature`` resp group ``annox``:
        Contains all the feature data of source resp annox.
        
        ``feature``:
            Keyed by *annotation space*, then by *annotation label* (both referring to the annotation that 
            contains the feature at hand), then by *feature name*, then by *kind* (``node`` or 
            ``edge``). At this level we have a dictionary, keyed by either the nodes or the edges
            (both as integers), and the value for each key is the value of the feature.
        
        .. note::
            If a feature occurs on both nodes and edges, the feature is split into two features with the same name,
            the one acting on nodes and the other acting on edges. In the compiled version, every feature has a kind,
            and in order to obtain a feature value, you have to specify the feature name and the feature kind (and of course
            the annotation space and annotation label).
        
        So the complete road to a value is::
        
            val = self.data_items['feature``][(annotation_space, annotation_label, feature_name, kind)][node_or_edge_id]
        
        The API will help you to lookup feature values.
        See :mod:`task <graf.task>` for a description of the API, especially
        :meth:`API <graf.task.GrafTask.API>`
    '''

    BIN_EXT = 'bin'
    '''extension for binary files
    '''
    TEXT_EXT = 'txt'
    '''extension for text files
    '''
    LOG_NAME = '__log__'
    '''log file base name for a task
    '''
    STAT_NAME = '__stat__'
    '''statistics file base name for a task
    '''
    COMPILE_NAME = 'compile__'
    '''name of the compile task
    '''

    def __init__(self, settings):
        '''Upon creation, empty datastructures are initialized to hold the binary,
        compiled LAF data and create a directory for their serializations on disk.

        The Graf object holds information that Graf tasks need to perform their operations.
        The most important piece of information is the data itself.
        This data consists of arrays and dictionaries that together hold the information that is compiled from a LAF resource.

        Other things that happen: 

        #. a fresh Timestamp object is created, which records the current time and can issue progress messages containing the amount
           of time that has elapsed since this object has been created.
        #. if the directory that should hold the compiled data does not exist,
           a new directory is created Of course this means that before executing any tasks,
           the LAF resource has to be (re)compiled. 

        Returns:
            object with data structures initialized, ready to load the compiled data from disk.
        '''

        self.stamp = Timestamp()
        '''Instance member holding the :class:`Timestamp <graf.timestamp.Timestamp>` object.
           Useful to deliver progress messages with timing information.
        '''
        self.settings = settings
        '''Instance member to hold config settings etc'''

        self.env = {}
        '''Holds the context information for the current task, such as chosen source, annox and task.
        '''
        self.log = None
        '''handle of a log file, usually open for writing. Used for the log of the compilation process
        and of the task executions.
        '''
        self.prev_tasks = {}
        '''List of tasks executed in this run of LAF-Fabric, with the modification time of the task program file
        at the time it was last run
        '''
        self.status = {
            'env': {
                'source': None,
                'annox': None,
                'task': None,
            },
            'compile': {
                'source': False,
                'annox': False,
            },
            'load' : {
                'common': None,
                'primary': None,
                'xmlids': None,
                'feature': None,
                'annox': None,
            }
        }
        '''Instance member to keep track of the status of the loaded data: does it match the task at hand?
        Three categories:

        **env**:
            The environment is the selected source, annox and task.
            Relevant to maintain is whether these have changed since last task execution.
        *keys*:
            ``source``:
                the chosen source
            ``annox``:
                the chosen annox, i.e. the selected extra annotation package
            ``task``:
                the chosen task
        *values*:
            ``None``:
                there was no previous choice
            ``False``:
                changed since last time
            ``True``:
                no change since last time
        **compile**:
            The source must be compiled before it can be used.
            In addition to the source there is the additional package of annotation, annox.
            This also has to be compiled.
            Relevant is to maintain whether the compiled data is outdated, up to data, or just compiled.
            In the latter case, the data is still in memory and does not have to be loaded.
        *keys*:
            ``source``:
                all data originating from the chosen source, including its feature data
            ``annox``:
                all data originating from the chosen annox, which is *only* feature data
        *values*:
            ``False``:
                compiled data is outdated.
            ``True``:
                compiled data is up to date, but has not recently be compiled.
            ``None``:
                compiled data is freshly compiled.
        **load**:
            Compiled data can only be used if it is loaded.
            Because data gets selectively loaded and unloaded between tasks,
            and because compiling may load data that is not needed for tasks,
            we need to keep track which data has been loaded, and whether
            the loaded data is still actual.
        *keys*:
            ``common``:
                data originating from the chosen source, but not its feature data and not its xml-id data.
            ``primary``:
                the primary data of the chosen source, including the region information
            ``xmlids``:
                the xml-ids originating from the chosen source.
            ``feature``:
                the feature data originating from the chosen source.
            ``annox``:
                the feature data from the chosen annox.
        *values*:
            ``False``:
                Data is no longer correct and must be loaded from scratch.
                All data that is present must be cleared.
            ``True``:
                All data that is present is correct. No data needs to be unloaded or loaded.
            ``None``:
                All data that is present is correct. Some data may need to be unloaded or loaded.
        '''

        self.data_items_def = collections.OrderedDict((
            ('common', collections.OrderedDict([
                    ("node_sort", 'i_array'),
                    ("node_out", 'double_array'),
                    ("node_in", 'double_array'),
                    ("edges_from", 'array'),
                    ("edges_to", 'array'),
                ])),
            ('primary', collections.OrderedDict([
                    ("data", 'string'),
                    ("node_anchor", 'double_array'),
                ])),
            ('xmlids', collections.OrderedDict([
                    ("xid", 'x_mapping'),
                ])),
            ('feature', collections.OrderedDict([ 
                    ("feature", 'feature_mapping'),
                ])),
            ('annox', collections.OrderedDict([ 
                    ("xfeature", 'feature_mapping'),
                ])),
        ))

        self.data_items = {}
        '''Instance member holding the compiled data in the form of a dictionary of arrays and lists.
        
        This dictionary is keyed by the same keys as ``data_items_def`` plus a few additional ones,
        dependent on tnd predictable from he data type and data group.

        See the :mod:`model <graf.model>` modules for the way the compiled data is created.
        '''

        self.temp_data_items = None
        '''Holds some data delivered by the parsed that can be thrown away later.
        The data that we must keep is stored in the object, of course.
        '''

        self.given = {}
        '''List of items given in the load directives of a task, per data group
        '''

        self.loaded = {}
        '''List of items currently loaded in memory, per data group 
        '''

        self.clear_all()

    def format_item(self, data_group, item, asFile=False):
        if data_group == 'common':
            return item
        if data_group == 'xmlids':
            return item
        if data_group == 'primary':
            return item
        if data_group == 'feature' or data_group == 'annox':
            if asFile:
                return '{}_{}_{}_{}'.format(*item)
            else:
                return '{}:{}.{} ({})'.format(*item)

    def check_status(self, source, annox, task):
        '''Updates the complete status information by inspecting the environment and
        detecting the compile status.

        This function is called at the start of each task execution, before any compiling or loading
        has taken place.

        It first detects changes in the selected source, annox and task (env), then it detects whether
        compiled data is outdated with respect to the source.
        data is up to the task.

        The methods for compiling and loading are responsible for updating the
        ``env`` and ``compile`` parts of the status accordingly.
        '''

#   env (compare new source, annox, task with old values in environment)
        for (info, lab) in ((source, 'source'), (annox, 'annox'), (task, 'task')):
            self.status['env'][lab] = None if lab not in self.env else self.env[lab] == info

        this_mtime = self.get_task_mtime(task)
        if task in self.prev_tasks:
            prev_mtime = self.prev_tasks[task]
            if prev_mtime < this_mtime:
                self.prev_tasks[task] = this_mtime
                self.status['env']['task'] = True
        else:
            self.prev_tasks[task] = this_mtime

#   now set environment to new source, annox, task

        self.set_environment(source, annox, task)

#   compile
        self.status['compile']['source'] = not os.path.exists(self.env['data_path']) or (
                os.path.exists(self.env['stat_file']) and
                os.path.getmtime(self.env['stat_file']) >= os.path.getmtime(self.env['data_path'])
            )

        up_to_date = True
        for file in glob.glob('{}/*.xml'.format(self.env['annox_dir'])):
            this_up_to_date = self.env['annox'] == self.settings['annox']['empty'] or (
                os.path.exists(self.env['annox_check_path']) and
                os.path.getmtime(self.env['annox_check_path']) >= os.path.getmtime(file)
            )
            if not this_up_to_date:
                up_to_date = False
                break
        self.status['compile']['annox'] = up_to_date
        
        self.given = {
            'common': {},
            'primary': {},
            'xmlids': {},
            'feature': {},
            'annox': {},
        }

    def check_load_status(self):
        '''Computes the ``load`` part of the status from the other parts.

        The rules for the status are not easy to state and it is easy to miss out cases.
        So I have spelled out all cases in a switchboard.
        Given the ``env`` and ``compile`` values, the switchboard gives the ``load`` values.
        
        To be called just before compiling and loading.

        ''' 
        switchboard = {
#          (env           , compile        : load                              )
#          ((S    , A    ), (S    , A    ) : (C    , P,     X    , F    , A    ) 
           ((None , None ), (False, False)): (False, False, False, False, False),
           ((None , False), (False, False)): (False, False, False, False, False),
           ((None , True ), (False, False)): (False, False, False, False, False),
           ((False, None ), (False, False)): (False, False, False, False, False),
           ((False, False), (False, False)): (False, False, False, False, False),
           ((False, True ), (False, False)): (False, False, False, False, False),
           ((True , None ), (False, False)): (False, False, False, False, False),
           ((True , False), (False, False)): (False, False, False, False, False),
           ((True , True ), (False, False)): (False, False, False, False, False),

           ((None , None ), (False, True )): (False, False, False, False, False),
           ((None , False), (False, True )): (False, False, False, False, False),
           ((None , True ), (False, True )): (False, False, False, False, None ),
           ((False, None ), (False, True )): (False, False, False, False, False),
           ((False, False), (False, True )): (False, False, False, False, False),
           ((False, True ), (False, True )): (False, False, False, False, None ),
           ((True , None ), (False, True )): (False, False, False, False, False),
           ((True , False), (False, True )): (False, False, False, False, False),
           ((True , True ), (False, True )): (False, False, False, False, None ),

           ((None , None ), (False, None )): (False, False, False, False, None ),
           ((None , False), (False, None )): (False, False, False, False, None ),
           ((None , True ), (False, None )): (False, False, False, False, None ),
           ((False, None ), (False, None )): (False, False, False, False, None ),
           ((False, False), (False, None )): (False, False, False, False, None ),
           ((False, True ), (False, None )): (False, False, False, False, None ),
           ((True , None ), (False, None )): (False, False, False, False, None ),
           ((True , False), (False, None )): (False, False, False, False, None ),
           ((True , True ), (False, None )): (False, False, False, False, None ),

           ((None , None ), (True , False)): (False, False, False, False, False),
           ((None , False), (True , False)): (False, False, False, False, False),
           ((None , True ), (True , False)): (False, False, False, False, False),
           ((False, None ), (True , False)): (False, False, False, False, False),
           ((False, False), (True , False)): (False, False, False, False, False),
           ((False, True ), (True , False)): (False, False, False, False, False),
           ((True , None ), (True , False)): (True , None , None , None , False),
           ((True , False), (True , False)): (True , None , None , None , False),
           ((True , True ), (True , False)): (True , None , None , None , False),

           ((None , None ), (True , True )): (False, False, False, False, False),
           ((None , False), (True , True )): (False, False, False, False, False),
           ((None , True ), (True , True )): (False, False, False, False, None ),
           ((False, None ), (True , True )): (False, False, False, False, False),
           ((False, False), (True , True )): (False, False, False, False, False),
           ((False, True ), (True , True )): (False, False, False, False, None ),
           ((True , None ), (True , True )): (True , None , None , None , False),
           ((True , False), (True , True )): (True , None , None , None , False),
           ((True , True ), (True , True )): (True , None , None , None , None ),

           ((None , None ), (True , None )): (False, None , None , False, None ),
           ((None , False), (True , None )): (False, None , None , False, None ),
           ((None , True ), (True , None )): (False, None , None , False, None ),
           ((False, None ), (True , None )): (False, None , None , False, None ),
           ((False, False), (True , None )): (False, None , None , False, None ),
           ((False, True ), (True , None )): (False, None , None , False, None ),
           ((True , None ), (True , None )): (True , None , None , None , None ),
           ((True , False), (True , None )): (True , None , None , None , None ),
           ((True , True ), (True , None )): (True , None , None , None , None ),

           ((None , None ), (None , False)): (True , None , None , None , False),
           ((None , False), (None , False)): (True , None , None , None , False),
           ((None , True ), (None , False)): (True , None , None , None , False),
           ((False, None ), (None , False)): (True , None , None , None , False),
           ((False, False), (None , False)): (True , None , None , None , False),
           ((False, True ), (None , False)): (True , None , None , None , False),
           ((True , None ), (None , False)): (True , None , None , None , False),
           ((True , False), (None , False)): (True , None , None , None , False),
           ((True , True ), (None , False)): (True , None , None , None , False),

           ((None , None ), (None , True )): (True , None , None , None , False),
           ((None , False), (None , True )): (True , None , None , None , False),
           ((None , True ), (None , True )): (True , None , None , None , None ),
           ((False, None ), (None , True )): (True , None , None , None , False),
           ((False, False), (None , True )): (True , None , None , None , False),
           ((False, True ), (None , True )): (True , None , None , None , None ),
           ((True , None ), (None , True )): (True , None , None , None , False),
           ((True , False), (None , True )): (True , None , None , None , False),
           ((True , True ), (None , True )): (True , None , None , None , None ),

           ((None , None ), (None , None )): (True , None , None , None , None ),
           ((None , False), (None , None )): (True , None , None , None , None ),
           ((None , True ), (None , None )): (True , None , None , None , None ),
           ((False, None ), (None , None )): (True , None , None , None , None ),
           ((False, False), (None , None )): (True , None , None , None , None ),
           ((False, True ), (None , None )): (True , None , None , None , None ),
           ((True , None ), (None , None )): (True , None , None , None , None ),
           ((True , False), (None , None )): (True , None , None , None , None ),
           ((True , True ), (None , None )): (True , None , None , None , None ),
        }
        (
            self.status['load']['common'],
            self.status['load']['primary'],
            self.status['load']['xmlids'],
            self.status['load']['feature'],
            self.status['load']['annox']
        ) = switchboard[(
            (self.status['env']['source'], self.status['env']['annox']),
            (self.status['compile']['source'], self.status['compile']['annox'])
        )]

        self.loaded = {}
        for data_group in self.data_items_def:
            if data_group == 'common':
                self.loaded[data_group] = 'node_sort' in self.data_items and self.data_items['node_sort'] != None
            elif data_group == 'primary':
                self.loaded[data_group] = {}
                if 'node_anchor' in self.data_items and self.data_items['node_anchor'] != None:
                    self.loaded[data_group]['regions'] = None
                if 'data' in self.data_items and self.data_items['data'] != None:
                    self.loaded[data_group]['data'] = None
            else:
                ref_label = 'xid_int' if data_group == 'xmlids' else 'feature' if data_group == 'feature' else 'xfeature'
                if ref_label not in self.data_items or self.data_items[ref_label] == None:
                    self.loaded[data_group] = {}
                else:
                    self.loaded[data_group] = dict([(key, None) for key in self.data_items[ref_label]])

    def verify_all(self):
        '''After loading, verify whether everything is as desired.

        Loading of features may have failed if the task has declared non-existent features!
        This will be spotted here.

        '''
        self.check_load_status()
        passed = True

        data_group = 'common'
        for label in self.data_items_def[data_group]:
            if self.data_items_def[data_group][label] == 'i_array':
                self.data_items[label + '_inv'] = self.make_array_inverse(self.data_items[label])

        data_group = 'xmlids'
        for item in self.given[data_group]:
            item_rep = self.format_item(data_group, item)
            if item not in self.loaded[data_group]:
                self.progress('ERROR: {}: {} not present'.format(data_group, item_rep))
                passed = False
            else:
                self.progress("present {}: {}".format(data_group, item_rep))
        for item in self.loaded[data_group]:
            item_rep = self.format_item(data_group, item)
            if item not in self.given[data_group]:
                self.progress('ERROR: {}: {} failed to unload'.format(data_group, item_rep))
                passed = False

        loaded_features = collections.defaultdict(lambda: {})
        for item in self.loaded['feature']:
            loaded_features[item]['source {}'.format(self.env['source'])] = None
        for item in self.loaded['annox']:
            loaded_features[item]['annox {}'.format(self.env['annox'])] = None

        for item in self.given['feature']:
            item_rep = self.format_item('feature', item)
            if item not in loaded_features:
                self.progress('WARNING: feature: {} not present from source {} nor annox {}'.format(item_rep, self.env['source'], self.env['annox']))
            else:
                self.progress('present feature: {} from {}'.format(item_rep, ', '.join(loaded_features[item].keys())))

        for item in loaded_features:
            item_rep = self.format_item('feature', item)
            if item not in self.given['feature']:
                self.progress('WARNING: feature: {} failed to unload'.format(item_rep))

        if not passed:
            raise

        labels = list(self.data_items.keys())
        for label in labels:
            if label.endswith('_int'):
                label_rep = label[0:len(label)-4]+'_rep'
                for item in self.data_items[label]:
                    if label_rep not in self.data_items:
                        self.data_items[label_rep] = {}
                    if item not in self.data_items[label_rep]:
                        self.data_items[label_rep][item] = self.make_inverse(self.data_items[label][item])

    def adjust_all(self, directives):
        '''Top level data management function: adjust the data to the task at hand.
        Load what is needed, discard what is no longer need, leave alone what does not to be changed.

        Args:
            directives (dict):
                specification of the needs of the task at hand, in terms of
                which features it uses and whether there is need for the orginal XML ids.
        '''
        self.read_stats()
        self.check_load_status()

        self.given['primary'] = {}
        if 'primary' in directives and directives['primary']:
            self.given['primary'] = {'data': None, 'regions': None}

        self.given['xmlids'] = {}
        for item in [k for k in directives['xmlids'] if directives['xmlids'][k]]:
            self.given['xmlids'][item] = None

        self.given['feature'] = {}
        self.given['annox'] = {}
        for aspace in directives['features']:
            for kind in directives['features'][aspace]:
                for line in directives['features'][aspace][kind]:
                    (alabel, fnamestring) = line.split('.')
                    fnames = fnamestring.split(',')
                    for fname in fnames:
                        self.given['feature'][(aspace, alabel, fname, kind)] = None
                        self.given['annox'][(aspace, alabel, fname, kind)] = None

        for data_group in self.data_items_def:
            self.adjust_data(data_group)

        self.verify_all()

    def adjust_data(self, data_group, items=None):
        '''Top level data management function for adjusting data.
        Now per key in the ``data_items_def`` dictionary.

        Args:
            key (str):
                key in ``data_items_def``, indicating the portion of data that has to be adjusted.
            items (dict):
                If given, will ensure that these items are loaded and the rest unloaded.
                If not given, looks at ``self.given[data_group]``.

        It calls :meth:`check_load_status` to see whether there is a change affecting the data under this ``label``.

        Clearance of data is deferred to :meth:`clear_data`, loading to :meth:`load_data`.
        '''

        load_status = self.status['load'][data_group]

        if data_group == 'common':
            if load_status == False:
                self.clear_data(data_group)
                self.load_data(data_group)

        elif data_group == 'primary':
            if load_status == False:
                self.clear_data(data_group)
                self.load_data(data_group, items=self.given[data_group])
            elif load_status == None:
                unload = []
                load = []
                if 'data' in self.given[data_group] and 'data' not in self.loaded[data_group]:
                    load.append('data')
                if 'regions' in self.given[data_group] and 'regions' not in self.loaded[data_group]:
                    load.append('regions')
                if 'data' not in self.given[data_group] and 'data' in self.loaded[data_group]:
                    unload.append('data')
                if 'regions' not in self.given[data_group] and 'regions' in self.loaded[data_group]:
                    unload.append('regions')
                self.clear_data(data_group, items=unload)
                self.load_data(data_group, items=load)
        else:
            unload = []
            load = []
            the_givens = self.given[data_group] if items == None else items 
            all_items = {}
            for item in the_givens:
                item_rep = self.format_item(data_group, item)
                all_items[item] = item_rep
            for item in self.loaded[data_group]:
                item_rep = self.format_item(data_group, item)
                all_items[item] = item_rep
            for (item, item_rep) in sorted(all_items.items()):
                if item in self.loaded[data_group] and item in the_givens:
                    self.progress("keeping {}: {} ...".format(data_group, item_rep))
                elif item in self.loaded[data_group]:
                    unload.append(item)
                elif item in the_givens:
                    load.append(item)
            if load_status == False:
                self.clear_data(data_group)
            elif load_status == None:
                self.clear_data(data_group, items=unload)
            self.load_data(data_group, items=load) 

    def clear_all(self):
        '''Low level data management function to clear all data.
        '''
        for data_group in self.data_items_def:
            self.clear_data(data_group)

    def clear_data(self, data_group, items=None):
        '''Low level data management function to clear all data.
        Now per key in the ``data_items_def`` dictionary.

        Args:
            data_group:
                the group of data items to be cleared
            items (iterable):
                A list of subitems.
                Optional. If given, only the data for the subitems specified, will be cleared.
                If not given all subitems will be cleared.

        '''
        if data_group == 'common':
            for (label, data_type) in self.data_items_def[data_group].items():
                subs = ('',)
                if data_type == 'double_array':
                    subs = ('', '_items')
                elif data_type == 'i_array':
                    subs = ('', '_inv')
                if label in self.data_items:
                    self.progress("clearing {}: {} ...".format(data_group, label))
                    for sub in subs:
                        lab = label + sub
                        del self.data_items[lab]

        elif data_group == 'primary':
            for (label, data_type) in self.data_items_def[data_group].items():
                if items == None or (label != 'data' and 'regions' in items) or (label == 'data' and 'data' in items):
                    if label in self.data_items:
                        self.progress("clearing {}: {} ...".format(data_group, label))
                        del self.data_items[label]

        else:
            sub_rep = '_rep' if data_group == 'xmlids' else None
            subs = ('_int',) if data_group == 'xmlids' else ('',)
            ref_lab = '_int' if data_group == 'xmlids' else ''
            for label in self.data_items_def[data_group]:
                if items != None:
                    for item in items:
                        item_rep = self.format_item(data_group, item)
                        if item in self.data_items[label + ref_lab]:
                            self.progress("clearing {}: {} - {} ...".format(data_group, label, item_rep))
                            for sub in subs:
                                lab = label + sub
                                if lab in self.data_items and item in self.data_items[lab]:
                                    del self.data_items[lab][item]
                            if sub_rep != None:
                                lab = label + sub_rep
                                if lab in self.data_items and item in self.data_items[lab]:
                                    del self.data_items[lab][item]
                else:
                    if label + ref_lab in self.data_items:
                        self.progress("clearing {}: {} ...".format(data_group, label))
                        for sub in subs:
                            lab = label + sub
                            if lab in self.data_items:
                                del self.data_items[lab]
                        if sub_rep != None:
                            lab = label + sub_rep
                            if lab in self.data_items:
                                del self.data_items[lab]
                    for sub in subs:
                        lab = label + sub
                        self.data_items[lab] = collections.defaultdict(lambda: None)

    def compile_all(self, force):
        '''Manages the complete compilation process.
        '''
        self.compile_data('source', force['source'])
        self.compile_data('annox', force['annox'])

    def compile_data(self, data_group, force):
        '''Manages the compilation process for either the source data or extra annotation files.

        Detects the need for compiling, responds to the *force* argument. Then parses, remodels and writes.

        Args:
            data_group (str):
                whether to parse source data (``source``) or an extra annotation package (``annox``)
            force (bool):
                whether to compile even if the binary data looks up to date.
        '''
        if force or self.status['compile'][data_group] == False:
            xmlitems = None
            if data_group == 'annox':
                self.check_load_status()
                self.adjust_data('xmlids', items=['node', 'edge'])
                xmlitems = self.data_items['xid_int']

            the_what = self.env['source'] if data_group == 'source' else self.env['annox']
            the_log_file = self.COMPILE_NAME + the_what
            the_log_dir = self.env['bin_dir'] if data_group == 'source' else self.env['annox_base_bdir']
            the_data_file = self.env['source'] if data_group == 'source' else self.env['annox_file']

            self.progress("BEGIN COMPILE {}: {}".format(data_group, the_what))
            self.add_logfile(the_log_dir, the_log_file)
            self.parse(data_group, xmlitems)
            self.model(data_group)
            self.write_data(data_group)
            self.progress("END COMPILE {}: {}".format(data_group, the_what))
            self.finish_logfile()
            self.status['compile'][data_group] = None
        else:
            self.progress("COMPILING {}: UP TO DATE".format(data_group))

    def write_data(self, data_group):
        '''Writes compiled data to disk.

        Args:
            data_group (str):
                what to parse: source data (``source``) or an extra annotation package (``annox``)
        '''
        self.progress("WRITING RESULT FILES for {}".format(data_group))
        target_dir = self.env['feat_dir'] if data_group == 'source' else self.env['annox_bdir']
        shutil.rmtree(target_dir)
        os.mkdir(target_dir)

        if data_group == 'source':
            self.write_stats()
        self.store_all(data_group)

        self.progress("FINALIZATION")


    def store_all(self, compile_data_group):
        '''Top level data management function: write data from memory to disk.

        This function is typically invoked at the end of compilation. 
        When in the business of running user tasks, there is no need for this function, 
        since tasks do not modify the data.
        '''
        for data_group in self.data_items_def:
            if (compile_data_group == 'source' and data_group != 'annox') or (compile_data_group == 'annox' and data_group == 'annox'):
                self.store_data(data_group)

    def store_data(self, data_group):
        '''Top level data management function for writing data to disk.
        Now per key in the ``data_items_def`` dictionary.

        Args:
            data_group (str):
                key in ``data_items_def``, indicating the portion of data that has to be adjusted.
        '''

        if data_group == 'common' or data_group == 'primary':
            for (label, data_type) in self.data_items_def[data_group].items():
                self.progress("writing {}: {} ...".format(data_group, label))
                if data_type == 'array' or data_type == 'double_array' or data_type == 'i_array':
                    subs = ('',)
                    if data_type == 'double_array':
                        subs = ('', '_items')
                    for sub in subs:
                        lab = label + sub
                        b_path = "{}/{}.{}".format(self.env['bin_dir'], lab, self.BIN_EXT)
                        b_handle = gzip.open(b_path, "wb")
                        self.data_items[lab].tofile(b_handle)
                        b_handle.close()
        else:
            ref_lab = '_int' if data_group == 'xmlids' else ''
            target_dir = self.env['bin_dir'] if data_group == 'xmlids' else self.env['feat_dir'] if data_group == 'feature' else self.env['annox_bdir']
            for label in self.data_items_def[data_group]:
                self.progress("writing {}: {} ...".format(data_group, label))
                for item in self.data_items[label + ref_lab]:
                    item_rep = self.format_item(data_group, item, asFile=True)
                    b_path = "{}/{}_{}.{}".format(target_dir, label, item_rep, self.BIN_EXT)
                    b_handle = gzip.open(b_path, "wb")
                    pickle.dump(self.data_items[label + ref_lab][item], b_handle)
                    b_handle.close()

    def write_stats(self):
        '''Write compilation statistics to file

        The compile process generates some statistics that must be read by the task that loads the compiled data.
        '''
        handle = open(self.env['stat_file'], "w")
        for data_group in self.data_items_def:
            for (label, data_type) in self.data_items_def[data_group].items():
                if data_type == 'array' or data_type == 'double_array' or data_type == 'i_array':
                    subs = ('',)
                    if data_type == 'double_array':
                        subs = ('', '_items')
                    for sub in subs:
                        lab = label + sub
                        handle.write("{}={}\n".format(lab, len(self.data_items[lab])))
        handle.close()

    def read_stats(self):
        '''Read compilation statistics from file

        The compile process generates some statistics that must be read by the task that loads the compiled data.
        In order to read an :py:mod:`array` by means of its :py:meth:`array.array.fromfile` method,
        we need to know the length of it on beforehand.
        
        And later, when we want to load new feature data on top of the existing data, we need to know
        how many distinct values features have.
        '''
        handle = open(self.env['stat_file'], "r")
        self.stats = {}
        for line in handle:
            (label, count) = line.rstrip("\n").split("=")
            self.stats[label] = int(count)
        handle.close()

    def load_data(self, data_group, items=None):
        '''Low level data management function to load data from disk into memory.

        Args:
            data_group:
                the kind of data to load
            items (iterable):
                A list of subitems in the data group to be loaded.
                Only relevant if ``data_group != common``
        '''
        if data_group == 'common':
            for (label, data_type) in self.data_items_def[data_group].items():
                self.progress("loading {}: {} ... ".format(data_group, label))
                subs = ('',)
                if data_type == 'double_array':
                    subs = ('', '_items')
                for sub in subs:
                    lab = label + sub
                    self.data_items[lab] = array.array('I')
                    b_path = "{}/{}.{}".format(self.env['bin_dir'], lab, self.BIN_EXT)
                    if os.path.exists(b_path):
                        b_handle = gzip.open(b_path, "rb")
                        self.data_items[lab].fromfile(b_handle, self.stats[lab])
                        b_handle.close()
        elif data_group == 'primary':
            for (label, data_type) in self.data_items_def[data_group].items():
                if items == None or (label != 'data' and 'regions' in items) or (label == 'data' and 'data' in items):
                    self.progress("loading {}: {} ... ".format(data_group, label))
                    if data_type == 'string':
                        b_path = "{}/{}".format(self.env['bin_dir'], self.settings['locations']['primary_data'])
                        b_handle = open(b_path, "r")
                        self.data_items[label] = b_handle.read(None)
                        b_handle.close()
                    else:
                        subs = ('',)
                        if data_type == 'double_array':
                            subs = ('', '_items')
                        for sub in subs:
                            lab = label + sub
                            self.data_items[lab] = array.array('I')
                            b_path = "{}/{}.{}".format(self.env['bin_dir'], lab, self.BIN_EXT)
                            if os.path.exists(b_path):
                                b_handle = gzip.open(b_path, "rb")
                                self.data_items[lab].fromfile(b_handle, self.stats[lab])
                                b_handle.close()
        else:
            ref_lab = '_int' if data_group == 'xmlids' else ''
            target_dir = self.env['bin_dir'] if data_group == 'xmlids' else self.env['feat_dir'] if data_group == 'feature' else self.env['annox_bdir']
            for label in self.data_items_def[data_group]:
                if items != None and len(items):
                    for item in items:
                        item_rep = self.format_item(data_group, item, asFile=True)
                        item_repm = self.format_item(data_group, item)
                        b_path = "{}/{}_{}.{}".format(target_dir, label, item_rep, self.BIN_EXT)
                        if os.path.exists(b_path):
                            b_handle = gzip.open(b_path, "rb")
                            lab = label + ref_lab
                            if lab not in self.data_items:
                                self.data_items[lab] = {}
                            self.data_items[lab][item] = collections.defaultdict(lambda: None, pickle.load(b_handle))
                            b_handle.close()

    def parse(self, data_group, xmlitems):
        '''Call the XML parser and collect the parse results.

        Some parse results must be remodelled afterwards.
        After remodelling some parse data can be thrown away.
        Only store data that is needed for task execution in the object.

        The actual parsing is done in the module :mod:`parse <graf.parse>`.

        Args:
            data_group (str):
                whether to parse source data (``source``) or an extra annotation package (``annox``)
        '''
        self.progress("PARSING ANNOTATION FILES")
        self.cur_dir = os.getcwd()

        the_data_file = self.env['source'] if data_group == 'source' else self.env['annox_file']
        the_laf_dir = self.env['laf_dir'] if data_group == 'source' else self.env['annox_dir']
        the_bin_dir = self.env['feat_dir'] if data_group == 'source' else self.env['annox_bdir']

        try:
            os.chdir(the_laf_dir)
        except os.error:
            raise GrafException("ERROR: could not change to LAF data directory {}".format(the_laf_dir),
                self.stamp, os.error
            )
        try:
            if not os.path.exists(the_bin_dir):
                os.makedirs(the_bin_dir)
        except os.error:
            os.chdir(self.cur_dir)
            raise GrafException("ERROR: could not create directory for compiled data {}".format(the_bin_dir),
                self.stamp, os.error,
            )
        
        prim_bin_file = "{}/{}".format(self.env['bin_dir'], self.settings['locations']['primary_data']) if data_group == 'source' else None

        parsed_data_items = xmlparse(the_data_file, prim_bin_file, self.stamp, xmlitems)

        self.temp_data_items = {}

        for parsed_data_item in parsed_data_items:
            (label, data, keep) = parsed_data_item
            if data_group == 'source':
                if keep:
                    self.data_items[label] = data
                else:
                    self.temp_data_items[label] = data
            else:
                use_label = label
                if label.startswith('feature'):
                    use_label = 'x' + label
                    self.data_items[use_label] = data

        os.chdir(self.cur_dir)

    def model(self, data_group):
        '''Call the remodeler and store the remodeled data in the object.

        Args:
            data_group (str):
                whether to parse source data (``source``) or an extra annotation package (``annox``)
        '''
        if data_group == 'source':
            self.progress("MODELING RESULT FILES")
            modeled_data_items = remodel(self.data_items, self.temp_data_items, self.stamp)
            for modeled_data_item in modeled_data_items:
                (label, data) = modeled_data_item
                self.data_items[label] = data
            self.temp_data_items = None

    def set_environment(self, source, annox, task):
        '''Set the source and result locations for a task execution.

        Args:
            source (str):
                key for the source
            annox (str):
                name of the extra annotation package
            task:
                the chosen task

        Sets *self.env*, a dictionary containg:

        * source: *source*
        * annox: *annox*
        * task: *task*
        * compile (bool): whether to force (re)compilation
        * settings (:py:class:`configparser.ConfigParser`): entries corresponding to the main configuration file
        * additional computed settings adapt to the current source and task

        '''
        settings = self.settings
        work_dir = settings['locations']['work_dir']
        laf_dir = settings['locations']['laf_dir']
        annox_file = settings['annox']['header']
        annox_root = settings['locations']['annox_dir']
        bin_subdir = settings['locations']['bin_subdir']
        task_dir = settings['locations']['task_dir']
        feat_subdir = settings['locations']['feat_subdir']
        annox_subdir = settings['locations']['annox_subdir']

        self.env = {
            'source': source,
            'annox': annox,
            'task': task,
            'task_dir': task_dir,
            'laf_dir': laf_dir,
            'data_path': '{}/{}'.format(laf_dir, source),
            'annox_file': annox_file,
            'annox_dir': '{}/{}'.format(annox_root, annox),
            'annox_path': '{}/{}/{}'.format(annox_root, annox, annox_file),
            'bin_dir': '{}/{}/{}'.format(work_dir, source, bin_subdir),
            'feat_dir': '{}/{}/{}/{}'.format(work_dir, source, bin_subdir, feat_subdir),
            'annox_base_bdir': '{}/{}/{}/{}'.format(work_dir, source, bin_subdir, annox_subdir),
            'annox_bdir': '{}/{}/{}/{}/{}'.format(work_dir, source, bin_subdir, annox_subdir, annox),
            'result_dir': '{}/{}/{}'.format(work_dir, source, task),
        }
        try:
            if not os.path.exists(self.env['bin_dir']):
                os.makedirs(self.env['bin_dir'])
        except os.error:
            raise GrafException(
                "ERROR: could not create bin directory {}".format(self.env['bin_dir']),
                self.stamp, os.error
            )
        try:
            if not os.path.exists(self.env['result_dir']):
                os.makedirs(self.env['result_dir'])
        except os.error:
            raise GrafException(
                "ERROR: could not create result directory {}".format(self.env['result_dir']),
                self.stamp, os.error
            )
        self.env['stat_file'] = "{}/{}{}.{}".format(self.env['bin_dir'], self.STAT_NAME, self.COMPILE_NAME, self.TEXT_EXT)
        '''Instance member holding name and location of the statistics file that describes the compiled data'''
        self.env['annox_check_path'] = "{}/{}{}{}.{}".format(self.env['annox_base_bdir'], self.LOG_NAME, self.COMPILE_NAME, annox, self.TEXT_EXT)

    def add_logfile(self, location=None, name=None):
        '''Create and open a log file for a given task.

        When tasks run, they generate progress messages with timing information in them.
        They may issue errors and warnings. All this information also goes into a log file.
        The log file is placed in the result directory of the task at hand.

        Args:
            location (str):
                override default directory for log file
            name (str):
                override default name for log file
        '''
        log_dir = self.env['result_dir'] if not location else location
        log_name = "{}{}.{}".format(self.LOG_NAME, self.env['task'] if not name else name, self.TEXT_EXT)

        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        except os.error:
            raise GrafException(
                "ERROR: could not create log directory {}".format(log_dir),
                self.stamp, os.error
            )

        log_file = "{}/{}".format(log_dir, log_name)
        self.log = open(log_file, "w")
        '''Instance member holding the open log handle'''

        self.stamp.connect_log(self.log)
        self.stamp.progress("LOGFILE={}".format(log_file))

    def finish_logfile(self):
        '''Explicitly close log file.

        Do not rely on the ``__del__`` method and hence on garbage collection.
        The program might terminate without writing the last bits to file.
        '''
        try:
            self.log.close()
        except:
            pass
        self.stamp.disconnect_log()
        self.log = None

    def flush_logfile(self):
        try:
            self.log.flush()
        except:
            pass

    def progress(self, msg, newline=True, withtime=True):
        '''Convenience method to call the progress of the associated stamp directly from the Graf object'''
        self.stamp.progress(msg, newline=newline, withtime=withtime)

    def make_inverse(self, mapping):
        '''Creates the inverse lookup table for a data table given as a dictionary.

        This is a low level function for creating inverse mappings.
        When mappings (such as from xml-ids to integers vv.) are stored to disk, the inverse mapping is not stored.
        Upon loading, the inverse mapping is generated by means of this function.
        '''
        return dict([(y,x) for (x,y) in mapping.items()])

    def make_array_inverse(self, arraylist):
        '''Creates the inverse lookup table for a data table given as a Python array.

        This is a low level function for creating inverse mappings.
        When mappings (such as from xml-ids to integers vv.) are stored to disk, the inverse mapping is not stored.
        Upon loading, the inverse mapping is generated by means of this function.
        '''
        return dict([(x,n) for (n,x) in enumerate(arraylist)])

    def __del__(self):
        '''Clean up

        Close all file handles that are still open.
        But really, this ought to have done explicitly already!
        '''
        self.stamp.progress("END")
        for handle in (
            self.log,
        ):
            if handle and not handle.closed:
                handle.close()

