import sys
import os
import glob
import configparser

from .timestamp import Timestamp

MAIN_CFG = 'laf-fabric.cfg'
VERSION = '3.7.0'

system_settings = {
    'locations': {
        'main_source_subdir': 'laf',           # subdirectory of main laf resource
        'annox_source_subdir': 'annotations',  # subdirectory of annotation add-ons
        'bin_subdir': 'bin',                   # subdirectory of compiled data
        'task_subdir': 'tasks',                # subdirectory of task results
        'bin_ext': 'bin'                       # file extension for binary files
        'text_ext': 'txt'                      # file extension for text files
        'log_name': '__log__'                  # base name for log files
        'compile_name': 'compile__'            # extension name for log files of compile process
        'primary_data': 'primary_data',        # name of the primary data file in the context of the compiled data
        'empty': '--',
        'header': '_header_.xml',
    },
    'data_items_def': ( 
        ('node_anchor',       '{source}/node_anchor'         , 'P', 'arr'),
        ('node_anchor_items', '{source}/node_anchor_items'   , 'P', 'arr'),
        ('node_anchor_min',   '{source}/node_anchor_min'     , 'c', 'arr'),
        ('node_anchor_max',   '{source}/node_anchor_max'     , 'c', 'arr'),
        ('node_events',       '{source}/node_events'         , 'P', 'arr'),
        ('node_events_items', '{source}/node_events_items'   , 'P', 'arr'),
        ('node_events_k',     '{source}/node_events_k'       , 'P', 'arr'),
        ('node_events_n',     '{source}/node_events_n'       , 'P', 'arr'),
        ('node_sort',         '{source}/node_sort'           , 'c', 'arr'),
        ('node_sort_inv',     '{source}/node_sort_inv'       , 'c', 'dct'),
        ('node_resorted',     '{source}/node_resorted'       , 'R', 'arr'),
        ('node_resorted_inv', '{source}/node_resorted_inv'   , 'R', 'arr'),
        ('edges_from',        '{source}/edges_from'          , 'c', 'arr'),
        ('edges_to',          '{source}/edges_to'            , 'c', 'arr'),
        ('primary_data',      '{source}/primary_data'        , 'P', 'str'),
        ('X_int',             '{source}/X_int_'              , 'X', 'dct'),
        ('X_rep',             '{source}/X_rep_'              , 'X', 'dct'),
        ('F_',                '{source}/F_'                  , 'F', 'dct'),
        ('C_',                '{source}/C_'                  , 'C', 'dct'),
        ('AF_',               '{source}/A/{annox}/F_'        , 'AF', 'dct'),
        ('AC_',               '{source}/A/{annox}/C_'        , 'AC', 'dct'),
    ),
    'env_def': {
        'source': '{source}',
        'annox': '{annox}',
        'empty': '{empty}',
        'main_source_dir':     '{main_source_dir}',
        'main_source_file':    '{main_source_dir}/{source}',
        'annox_source_dir':    '{main_source_dir}/{annox_source_base_dir}/{annox}',
        'annox_source_file':   '{main_source_dir}/{annox_source_base_dir}/{annox}/{header}',
        'main_compiled_dir':   '{work_dir}/{bin_subdir}/{source}',
        'main_compiled_file':  '{work_dir}/{bin_subdir}/{source}/{log_name}{compile_name}.{text_ext}',
        'annox_compiled_dir':  '{work_dir}/{bin_subdir}/{source}/A/{annox}',
        'annox_compiled_file': '{work_dir}/{bin_subdir}/{source}/A/{annox}/{log_name}{compile_name}.{text_ext}',
        'task_dir':            '{work_dir}/{task_subdir}/{source}',
    },
}

class Settings(object):
    '''Reads and maintains program settings.

    '''

    def __init__(self, context=None):
        '''Upon creation, create a :class:`LafTask <laf.task.LafTask>` object based on settings.

        Args:
            context (str): either ``wb`` (workbench) or ``nb`` (notebook).
            The only difference is the path to the config file.
        '''

        sys.stderr.write('This is LAF-Fabric {}\n'.format(VERSION))

        self.settings = configparser.ConfigParser(inline_comment_prefixes=('#'))
        self.settings.update(system_settings)
        self.settings.read_file(open(MAIN_CFG, "r", encoding="utf-8"))
        locs = self.settings['locations']
        work_dir = self.settings['work_dir']
        locs['main_source_dir'] = locs['laf_dir'] if 'laf_dir' in locs else "{}/{}".format(work_dir, locs['main_source_subdir']
        self.prep_list = []
        self.data_items_list = []
        self.old_prep_list = []
        self.old_data_items_list = []

    def set_env(self, source, annox, task):
        locs = self.settings['locations']

        env = {}
        env_def = self.settings['env_def']
        for e in env_def:
            env[e] = env_def[e].format(**locs)
        self.env = env

        data_items_def = {}
        data_items_template = self.settings['data_items_template']
        for d in data_items_template:
            template = data_items_template[d]
            data_items_def[d] = (template[0].format(**env), template[1], template[2], template[3])
        self.data_items_def = data_items_def
        
    def request_files(self, req_items):
        self.old_prep_list = self.prep_list
        self.old_data_items_list = self.data_items_list

        env = self.settings.env
        data_items_def = self.settings.data_items_def
        self.data_items_list = []
        self.prep_list = []
        for (dkey, dpath, docc, dtype) in data_items_def:
            if docc == 'R':
                self.prep_list.extend(self.multiply_req(dkey, dpath, dtype, docc, req_items))
            else:
                self.data_items_list.extend(self.multiply_req(dkey, dpath, dtype, docc, req_items))

    def multiply_req(self, dkey, dpath, dtype, docc, req_items):
        if docc not in req_items:
            return []
        result = []
        for item in req_items[docc]:
            result.append((dkey + item, dpath + item, dtype))
        return result
