import os
import glob
import configparser

MAIN_CFG = 'laf-fabric.cfg'

system_settings = {
    'locations': {
        'bin_subdir': 'bin',                   # subdirectory of compiled data
        'annox_subdir': 'annotations',         # subdirectory of annotation add-ons
        'laf_subdir': 'laf',                   # subdirectory of laf resource
        'feat_subdir': 'feat',                 # subdirectory within bin_subdir for feature data
        'annox_subdir': 'annox',               # subdirectory within bin_subdir for annox feature data
        'primary_data': 'primary_data.txt',    # name of the primary data file in the context of the compiled data
        'task_dir': 'tasks',                   # name of the directory with tasks (relative to the top-level dir of laf-fabric)
    },
    'annox': {
        'empty': '--',
        'header': '_header_.xml',
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

        self.settings = configparser.ConfigParser(inline_comment_prefixes=('#'))
        for group in system_settings:
            for var in system_settings[group]:
                if group not in self.settings:
                    self.settings[group] = {}
                self.settings[group][var] = system_settings[group][var]
        main_cfg = MAIN_CFG if context == 'nb' else 'notebooks/{}'.format(MAIN_CFG) if context == 'wb' else 'None'
        self.settings.read_file(open(main_cfg))
        self.settings['locations']['annox_dir'] = "{}/{}".format(self.settings['locations']['work_dir'], self.settings['locations']['annox_subdir'])
        self.settings['locations']['laf_dir'] = "{}/{}".format(self.settings['locations']['work_dir'], self.settings['locations']['laf_subdir'])

        self.get_sources()
        self.annox_choices = [self.settings['annox']['empty']] + [
            os.path.splitext(os.path.basename(f))[0]
            for f in glob.glob("{}/*".format(self.settings['locations']['annox_dir']))
            if os.path.exists("{}/{}".format(f, self.settings['annox']['header']))
        ]
        if context == 'wb':
            self.task_choices = [os.path.splitext(os.path.basename(f))[0] for f in glob.glob("{}/*.py".format(self.settings['locations']['task_dir']))]
        elif context == 'nb':
            self.settings['locations']['task_dir'] = '<'
            self.task_choices = []

    def get_sources(self):
        self.source_choices = []
        for f in glob.glob("{}/*.*".format(self.settings['locations']['laf_dir'])):
            f_handle = open(f, "r")
            f_handle.readline()
            if 'documentHeader' in f_handle.readline():
                self.source_choices.append(os.path.basename(f))

        

