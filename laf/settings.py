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
        'primary_data': 'primary_data',        # name of the primary data file in the compiled data
        'empty': '--',
        'header': '_header_.xml',
    },
    'data_items_template': ( 
        ('node_anchor',          '{source}/node_anchor'         , 'P', 'arr'),
        ('node_anchor_items',    '{source}/node_anchor_items'   , 'P', 'arr'),
        ('node_anchor_min',      '{source}/node_anchor_min'     , 'c', 'arr'),
        ('node_anchor_max',      '{source}/node_anchor_max'     , 'c', 'arr'),
        ('node_events',          '{source}/node_events'         , 'P', 'arr'),
        ('node_events_items',    '{source}/node_events_items'   , 'P', 'arr'),
        ('node_events_k',        '{source}/node_events_k'       , 'P', 'arr'),
        ('node_events_n',        '{source}/node_events_n'       , 'P', 'arr'),
        ('node_sort',            '{source}/node_sort'           , 'c', 'arr'),
        ('node_sort_inv',        '{source}/node_sort_inv'       , 'c', 'dct'),
        ('node_resorted',        '{source}/node_resorted'       , 'R', 'arr'),
        ('node_resorted_inv',    '{source}/node_resorted_inv'   , 'R', 'arr'),
        ('edges_from',           '{source}/edges_from'          , 'c', 'arr'),
        ('edges_to',             '{source}/edges_to'            , 'c', 'arr'),
        ('primary_data',         '{source}/primary_data'        , 'P', 'str'),
        ('X,',                   '{source}/X,'                  , 'X', 'dct'),
        ('XE,',                  '{source}/XE,'                 , 'X', 'dct'),
        ('RX,',                  '{source}/RX,'                 , 'X', 'dct'),
        ('RXE,',                 '{source}/RXE,'                , 'X', 'dct'),
        ('F,',                   '{source}/F,'                  , 'F', 'dct'),
        ('FE,',                  '{source}/FE,'                 , 'E', 'dct'),
        ('C,',                   '{source}/C,'                  , 'E', 'dct'),
        ('Ci,',                  '{source}/Ci,'                 , 'E', 'dct'),
        ('AF,',                  '{source}/A/{annox}/F,'        , 'AF', 'dct'),
        ('AFE,',                 '{source}/A/{annox}/FE,'       , 'AE', 'dct'),
        ('AC,',                  '{source}/A/{annox}/C,'        , 'AE', 'dct'),
        ('ACi,',                 '{source}/A/{annox}/Ci,'       , 'AE', 'dct'),
    ),
    'env_def': {
        'source':                '{source}',
        'annox':                 '{annox}',
        'empty':                 '{empty}',
        'main_source_dir':       '{main_source_dir}',
        'main_source_path':      '{main_source_dir}/{source}',
        'annox_source_dir':      '{main_source_dir}/{annox_source_base_dir}/{annox}',
        'annox_source_path':     '{main_source_dir}/{annox_source_base_dir}/{annox}/{header}',
        'compiled_file':         '{log_name}{compile_name}.{text_ext}',
        'main_compiled_dir':     '{work_dir}/{bin_subdir}/{source}',
        'main_compiled_path':    '{work_dir}/{bin_subdir}/{source}/{log_name}{compile_name}.{text_ext}',
        'primary_compiled_path': '{work_dir}/{bin_subdir}/{source}/{primary_data}',
        'annox_compiled_dir':    '{work_dir}/{bin_subdir}/{source}/A/{annox}',
        'annox_compiled_path':   '{work_dir}/{bin_subdir}/{source}/A/{annox}/{log_name}{compile_name}.{text_ext}',
        'task_dir':              '{work_dir}/{task_subdir}/{source}/{task}',
        'log_path':              '{work_dir}/{task_subdir}/{source}/{task}/{log_name}{task}.{text_ext}',
    },
}

class Names(object):
    trans = {
        'X': ('X', 'int', 'node'),
        'XE': ('X', 'int', 'edge'),
        'RX': ('X', 'rep', 'node'),
        'RXE': ('X', 'rep', 'edge'),
        'F': ('F', 'main', 'node'),
        'FE': ('F', 'main', 'edge'),
        'AF': ('F', 'annox', 'node'),
        'AFE': ('F', 'annox', 'edge'),
        'C': ('C', 'main', False),
        'Ci': ('C', 'main', True),
        'AC': ('C', 'annox', False),
        'ACi': ('C', 'annox', True),
    }
    transback = dict([(i[1], i[0]) for i in trans.items()]) 

    def comp(d, things):
        return ",".join([self.transback[d]] + things)

    def decomp(s):
        if ',' not in s: return (s, None, None, ())
        comps = s.split(',')
        return self.trans(comps[0]) + (tuple(comps[1:]),)

    def msg(s):
        (d, start, end, comps) = Names.decomp(s) 
        return "{}{}{}{}".format(
            "{}:".format(start) if start else '',
            d,
            "({})".format(end) if end else '',
            '_'.join(comps),
        )

    def apiname(feature): return "_".join(*feature)

    def id2p(inv, data): return "{}C{}".format('A' if data == 'annox' else '', 'i' if inv else '')
    def kd2p(kind, data): return "{}F{}".format('A' if data == 'annox' else '', 'E' if kind == 'edge' else '')
    def k2p(kind): return "F{}".format('E' if kind == 'edge' else '')
    def p2kd(pref): return ('edge' if pref.endswith('E') else 'node', 'annox' if pref.startswith('A') else 'main')
    def p2kc(pref): return ('edge' if pref.endswith('E') else 'node', 'annox' if pref.startswith('A') else 'main')
    def p2k(pref): return 'edge' if pref.endswith('E') else 'node' 
    def f2con(feature, kind, data): return "{}: {} ({})".format(data, "_".join(*feature), kind)
    def f2file(feature, kind): return "{}{}".format(Names.k2p(kind), ','.join(*feature))
    def f2key(feature, kind, data): return "{}{}".format(Names.kd2p(kind, data), ','.join(*feature))
    def c2key(feature, inv, data): return "{}{}".format(Names.id2p(inv, data), ','.join(*feature))
    def x2key(code, kind): return "X_{}_{}".format(code, key)
    def key2f(s): return _decomp(s, Names.isf, Names.p2kd)
    def key2x(s): return _decomp(s, Names.isx, Names.p2kc)
    def file2f(s): return _decomp(s, Names.isf, Names.p2k)

class Settings(object):
    '''Reads and maintains program settings.

    '''

    def __init__(self):
        sys.stderr.write('This is LAF-Fabric {}\n'.format(VERSION))

        self.settings = configparser.ConfigParser(inline_comment_prefixes=('#'))
        self.settings.update(system_settings)
        self.settings.read_file(open(MAIN_CFG, "r", encoding="utf-8"))
        locs = self.settings['locations']
        work_dir = self.settings['work_dir']
        locs['main_source_dir'] = locs['laf_dir'] if 'laf_dir' in locs else "{}/{}".format(work_dir, locs['main_source_subdir']
        self.data_items = {}
        self.old_data_items = {}

    def set_env(self, source, annox, task):
        locs = self.settings['locations']

        env = {}
        env_def = self.settings['env_def']
        for e in env_def:
            env[e] = env_def[e].format(**locs)
        self.env = env

        data_items_def = {}
        data_items_template = self.settings['data_items_template']
        for t in data_items_template:
            data_items_def[t[0]] = (t[1].format(**env), t[2], t[3]))
        self.data_items_def = data_items_def
        
    def request_files(self, req_items, extra=False):
        self.old_data_items = self.data_items

        env = self.settings.env
        data_items_def = self.settings.data_items_def
        self.data_items = {}
        if extra:
            self.data_items.update(self.old_data_items)
        for dkey in data_items_def:
            (dpath, docc, dtype) = data_items_def[dkey]
            self.data_items.update(self.multiply_req(dkey, dpath, dtype, docc, req_items))

    def multiply_req(self, dkey, dpath, dtype, docc, req_items):
        if docc not in req_items:
            return {}
        result = {}
        for item in req_items[docc]:
            result["{}{}".format(dkey, item)] = ("{}{}".format(dpath, item), dtype, docc == 'R')
        return result

    def print_all(self):
        data_items = self.data_items
        for dkey in data_items:
            print(Names.f2con(dkey))

