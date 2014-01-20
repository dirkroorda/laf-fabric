import os
import traceback
import collections

from .settings import Settings
from .task import LafTask

class Notebook(object):
    '''Execute tasks, either in a single run, within a notebook

    See :doc:`Writing Tasks <../taskwriting>` for how to run a task in an iPython notebook.
    '''

    def __init__(self):
        '''Upon creation, create a :class:`LafTask <laf.task.LafTask>` object based on settings.

        '''

        self.settings = Settings(context='nb')
        self.laftask = LafTask(self.settings.settings)

    def init(self, source, annox, task, load, force_compile_source=False, force_compile_annox=False):
        '''Initialize task execution.

        Run this method before executing your task code.

        Args:
            source(str):
                the laf source of which the data will be used.
            annox(str):
                additional annotation packages in addition to the laf source.
            task(str):
                a name for your task. This name will be used for a directory where the log file
                and output files for your tasks can be created.
            load(dict):
                a dictionary specifying what data to load. See :doc:`Writing Tasks <../taskwriting>`.
            force_compile_source(bool):
                Whether to force compilation of the laf source.
                Optional, default False.
            force_compile_annox(bool):
                Whether to force compilation of the additional annotation package.
                Optional, default False.
        '''
        self.laftask.run(
            source, annox, task,
            force_compile={'source': force_compile_source, 'annox': force_compile_annox},
            load=load, function=True, stage='init',
        )

    def final(self):
        '''Finalize task execution.

        Run this method after executing your task code, in order to
        close all open files for output and logging.
        '''
        self.laftask.run(
            self.laftask.env['source'],
            self.laftask.env['annox'],
            self.laftask.env['task'],
            stage='final',
        )

    def API(self):
        '''Insert the names by which you can access the data into your name space.
        '''
        return self.laftask.API()

    def add_output(self, file_name):
        '''Create an output file in the folder for the output of this task
        '''
        return self.laftask.add_output(file_name)

    def add_input(self, file_name):
        '''Create an input file in the folder for the output of this task
        '''
        return self.laftask.add_input(file_name)

    def my_files(self, file_name=None):
        '''The location where the output files of this task can be found

        Args:
            file_name (str):
                the name of the file, without path information.
                Optional. If not present, returns the path to the output directory.

        Returns:
            the path to *file_name* or the directory of the output files.
        '''
        return self.laftask.result(file_name=file_name)
