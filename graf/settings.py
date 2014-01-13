import os
import glob
import configparser

MAIN_CFG = 'laf-fabric.cfg'

system_settings = {
    'locations': {
        'laf_source': 'laf',                   # subdirectory for the LAF data
        'base_bdir': 'db',                     # subdirectory for task results
        'bin_subdir': 'bin',                   # subdirectory of compiled data
        'feat_subdir': 'feat',                 # subdirectory within bin_subdir for feature data
        'annox_subdir': 'annox',               # subdirectory within bin_subdir for annox feature data
        'primary_data': 'primary_data.txt',    # name of the primary data file in the context of the compiled data
    },
    'annox': {
        'empty': '--',
        'header': '_header_.xml',
    },
}

class Settings(object):
    '''Reads and maintains program settings.

    '''

    def __init__(self):
        '''Upon creation, create a :class:`GrafTask <graf.task.GrafTask>` object based on settings.

        '''

        self.settings = configparser.ConfigParser(inline_comment_prefixes=('#'))
        for group in system_settings:
            for var in system_settings[group]:
                if group not in self.settings:
                    self.settings[group] = {}
                self.settings[group][var] = system_settings[group][var]
        self.settings.read_file(open(MAIN_CFG))

        self.get_sources()
        self.annox_choices = [self.settings['annox']['empty']] + [
            os.path.splitext(os.path.basename(f))[0]
            for f in glob.glob("{}/*".format(self.settings['locations']['annox_dir']))
            if os.path.exists("{}/{}".format(f, self.settings['annox']['header']))
        ]
        if 'task_dir' in self.settings['locations']:
            self.task_choices = [os.path.splitext(os.path.basename(f))[0] for f in glob.glob("{}/*.py".format(self.settings['locations']['task_dir']))]
        else:
            self.settings['locations']['task_dir'] = '<'
            self.task_choices = []

    def get_sources(self):
        self.source_choices = []
        for f in glob.glob("{}/*.*".format(self.settings['locations']['laf_dir'])):
            f_handle = open(f, "r")
            f_handle.readline()
            if 'documentHeader' in f_handle.readline():
                self.source_choices.append(os.path.basename(f))

        

