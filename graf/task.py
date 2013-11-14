# -*- coding: utf8 -*-

import codecs
import subprocess
import collections

import array

from compiler import GrafCompiler
from task_plain import GrafTaskPlain
from task_mem import GrafTaskMemo
from task_ass import GrafTaskAssembler

class GrafTask(object):
    '''Factory class to produce task processors.

    A task processor must know how to compile, where the source data is and where the result is going to.
    For the actual processing of tasks, the user can choose a *flavour*, and depending on this *flavour* of optimization,
    a different class is used to process tasks.
    When an object of the chosen class is produced (by :meth:`processor_factory`), a reference to it is stored in the producing ``GrafTask`` object.
    '''

    def __init__(self, task=None, source=None, compile=False, data_dir=None, data_file=None, bin_dir=None, result_dir=None):
        '''Upon creation, information is passed and stored about locations.

        Args:
            data_dir (str): the directory of the original LAF resource.
            data_file (str): the GrAF header file by which to consume the LAF resource.
            bin_dir (str): the directory where the compiled data is located, relative to the ``result_dir``.
            result_dir (str): the directory where the task should operate: the compiled data is there, the results go there.
            compile (bool): whether to force (re)compilation of the LAF resource. Normally (re)compilation is only done if the need for it has been detected.
                See :meth:`needs_compiling() <graf.compiler.GrafCompiler.needs_compiling>`.
        '''
        self.task = task
        '''Instance member: Holds the current task'''
        self.source = source
        '''Instance member: Holds the current source selection (the GrAF header file)'''
        self.bin_dir = bin_dir
        '''Instance member: The path to the result directory'''
        self.result_dir = result_dir
        '''Instance member: List of handles to result files created by the task through the method :meth:`add_result`'''

        grafcompiler = GrafCompiler(data_dir, data_file, bin_dir)
        grafcompiler.compiler(force=compile)
        grafcompiler = None

    def processor_factory(self, flavour="plain", flavour_detail="plain", index=False):
        '''Produces a task executing object depending on the chosen *flavour*.

        Task execution may be optimized according to several flavours. Each flavour corresponds to a class with optimized methods.
        All flavoured classes derive from a base class :class:`GrafTaskBase <graf.task_base.GrafTaskBase>`, so they share a lot of methods.
        They only implement the flavoured methods. So this is *duck typing*, we have several flavoured classes with the same method signatures.

        Args:
            flavour (str): currently ``plain``, ``memo``, or ``assemble``.
            flavour_detail (str): the same and also ``assemble_all``, which is a variant of the ``assemble`` flavour.
            index (bool): whether or not to force the (re)creation of indexes, only relevant for the ``assemble`` flavour.

        Returns:
            An object of a specific subclass of
            :class:`GrafTaskBase <graf.task_base.GrafTaskBase>`, one of the following options:

            * :class:`GrafTaskPlain <graf.task_plain.GrafTaskPlain>`
            * :class:`GrafTaskMemo <graf.task_mem.GrafTaskMemo>`
            * :class:`GrafTaskAssembler <graf.task_ass.GrafTaskAssembler>`
        '''
        obj = None
        if flavour == 'plain':
            obj = GrafTaskPlain(self.bin_dir, self.result_dir, self.task, self.source, flavour_detail)
        elif flavour == 'memo':
            obj = GrafTaskMemo(self.bin_dir, self.result_dir, self.task, self.source, flavour_detail)
        elif flavour == 'assemble':
            obj = GrafTaskAssembler(self.bin_dir, self.result_dir, self.task, self.source, flavour_detail, index)
        else:
            return None
        self.processor = obj
        '''Instance member: Holds the current task processor'''
        return obj

