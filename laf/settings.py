import sys
import os
import configparser

MAIN_CFG = 'laf-fabric.cfg'
VERSION = '3.7.0'

class Settings(object):
    '''Manage the configuration.

    The directory structure is built as a set of names in an environment dictionary. 
    The method ``setenv`` builds a new structure based on user choices.
    Local settings can be passed as arguments to object creation, or in a config file in the current directory,
    or in a config file in the user's home directory.
    It is possible to save these settings in the latter config file.
    '''
    _myconfig = {
        'work_dir': None,                  # working directory (containing compiled laf, task results)
        'm_source_dir': None,              # directory containing original, uncompiled laf resource
        'm_source_subdir': 'laf',          # subdirectory of main laf resource
        'a_source_subdir': 'annotations',  # subdirectory of annotation add-ons
        'bin_subdir': 'bin',               # subdirectory of compiled data
        'task_subdir': 'tasks',            # subdirectory of task results
        'bin_ext': 'bin',                  # file extension for binary files
        'text_ext': 'txt',                 # file extension for text files
        'log_name': '__log__',             # base name for log files
        'compile_name': 'compile__',       # extension name for log files of compile process
        'primary_data': 'primary_data',    # name of the primary data file in the compiled data
        'empty': '--',                     # name of empty annox
        'header': '_header_.xml',          # name of laf header file in annox
    }
    _env_def = {
        'source':                '{source}',
        'annox':                 '{annox}',
        'task':                  '{task}',
        'zspace':                '{zspace}',
        'empty':                 '{empty}',
        'work_dir':              '{work_dir}',
        'bin_dir':               '{work_dir}/{bin_subdir}',
        'm_source_dir':          '{m_source_dir}',
        'm_source_path':         '{m_source_dir}/{source}',
        'a_source_dir':          '{m_source_dir}/{a_source_subdir}/{annox}',
        'a_source_path':         '{m_source_dir}/{a_source_subdir}/{annox}/{header}',
        'compiled_file':         '{log_name}{compile_name}.{text_ext}',
        'm_compiled_dir':        '{work_dir}/{bin_subdir}/{source}',
        'm_compiled_path':       '{work_dir}/{bin_subdir}/{source}/{log_name}{compile_name}.{text_ext}',
        'primary_compiled_path': '{work_dir}/{bin_subdir}/{source}/{primary_data}',
        'a_compiled_dir':        '{work_dir}/{bin_subdir}/{source}/A/{annox}',
        'a_compiled_path':       '{work_dir}/{bin_subdir}/{source}/A/{annox}/{log_name}{compile_name}.{text_ext}',
        'z_compiled_dir':        '{work_dir}/{bin_subdir}/{source}/Z/{zspace}',
        'task_dir':              '{work_dir}/{task_subdir}/{source}/{task}',
        'log_path':              '{work_dir}/{task_subdir}/{source}/{task}/{log_name}{task}.{text_ext}',
    }

    def __init__(self, work_dir, laf_dir, save):
        sys.stderr.write('This is LAF-Fabric {}\n'.format(VERSION))
        config_path = None
        home_config_path = "{}/{}".format(os.path.expanduser('~'), MAIN_CFG)
        cwd_path = os.getcwd()
        if os.path.exists(MAIN_CFG): config_path = MAIN_CFG
        else:
            if os.path.exists(home_config_path): config_path = home_config_path
        strings = configparser.ConfigParser(inline_comment_prefixes=('#'))
        strings.read_file(open(config_path, "r", encoding="utf-8"))
        config_work_dir = None
        config_laf_dir = None
        if 'locations' in strings:
            if 'work_dir' in strings['locations']: config_work_dir = strings['locations']['work_dir']
            if 'laf_dir' in strings['locations']: config_laf_dir = strings['locations']['laf_dir']
        if work_dir == None: work_dir = config_work_dir
        if laf_dir == None: laf_dir = config_laf_dir
        if work_dir == None:
            print("ERROR: No data directory given (looked for arguments, {}, and {}.".format(MAIN_CFG, home_config_dir))
            sys.exit(1)
        work_dir = work_dir.replace('.', cwd_path, 1) if work_dir.startswith('.') else work_dir
        laf_dir = laf_dir.replace('.', cwd_path, 1) if laf_dir.startswith('.') else laf_dir
        if not os.path.exists(work_dir):
            print("ERROR: Given data directory {} does not exist.".format(work_dir))
            work_dir = None
        if work_dir == None: sys.exit(1)
        if laf_dir == None:
            print("WARNING: No original laf directory given (looked for arguments, {}, and {}.".format(MAIN_CFG, home_config_dir))
        elif not os.path.exists(laf_dir):
            print("WARNING: Given original laf directory {} does not exist.".format(laf_dir))
            laf_dir = None
        self._myconfig['work_dir'] = work_dir
        self._myconfig['m_source_dir'] = laf_dir
        if save and work_dir != None:
            strings['locations'] = {
                'work_dir': work_dir,
                'laf_dir': laf_dir,
            }
            config_path = home_config_path
            strings.write(open(home_config_path, 'w', encoding= 'utf-8'))
        self.env = {}
        self.zspace = ''

    def setenv(self, source=None, annox=None, task=None, zspace=None):
        if source == None: source = self.env.get('source')
        if annox == None: annox = self.env.get('annox')
        if task == None: task = self.env.get('task')
        if zspace == None: zspace = self.env.get('zspace')
        for e in self._env_def: self.env[e] = self._env_def[e].format(source=source, annox=annox, task=task, zspace=zspace, **self._myconfig)


