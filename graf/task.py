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
    def __init__(self, task=None, source=None, compile=False, data_dir=None, data_file=None, bin_dir=None, result_dir=None):
        self.task = task
        self.source = source
        self.bin_dir = bin_dir
        self.result_dir = result_dir
        grafcompiler = GrafCompiler(data_dir, data_file, bin_dir)
        grafcompiler.compiler(force=compile)
        grafcompiler = None

    def processor_factory(self, flavour="plain", flavour_detail="plain", index=False):
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
        return obj

