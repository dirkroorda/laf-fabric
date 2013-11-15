# -*- coding: utf8 -*-
import os
import codecs
import glob
import sys
import argparse
import ConfigParser
from graf import GrafTask

### USAGE

# python laf-fabric.py

### CONFIG

MAIN_CFG = 'laf-fabric.cfg'

settings = ConfigParser.ConfigParser()
settings.readfp(codecs.open(MAIN_CFG, encoding = 'utf-8'))

source_choices = {}
for (key, value) in settings.items('source_choices'):
    source_choices[key] = value

data_root = settings.get('locations', 'data_root')
laf_source = settings.get('locations', 'laf_source')
compiled_source = settings.get('locations', 'compiled_source')
bin_dir = settings.get('locations', 'bin_dir')

cur_dir = os.getcwd()

task_dir = 'tasks'
task_choices = [os.path.splitext(os.path.basename(f))[0] for f in glob.glob("tasks/*.py")]

process_flavours = {
    "plain": "plain",
    "memo": "memo",
    "assemble": "assemble",
    "assemble_all": "assemble",
}

### COMMAND LINE ARGS AND OPTIONS
argsparser = argparse.ArgumentParser(description = 'Conversion of LAF to Binary')
argsparser.add_argument(
    "--source",
    dest = 'source',
    type = str,
    choices = source_choices.keys(),
    default = 'total',
    metavar = 'Source',
    help = "which source to take",
)
argsparser.add_argument(
    "--task",
    dest = 'task',
    type = str,
    choices = task_choices,
    default = 'plain',
    metavar = 'Task',
    help = "which task to perform",
)
argsparser.add_argument(
    "--force-compile",
    dest = 'forcecompile',
    action = "store_true",
    help = "Force new compilation of LAF XML to binary representation",
)
argsparser.add_argument(
    "--force-index",
    dest = 'forceindex',
    action = "store_true",
    help = "Force new indexing of selected features",
)
argsparser.add_argument(
    "--optim",
    dest = 'flavour',
    type = str,
    choices = process_flavours.keys(),
    default = 'plain',
    metavar = 'Optimization',
    help = "The kind of optimizations employed in processing the task",
)
args = argsparser.parse_args()

### TASK EXECUTION

# Setting up a task involves
# (A) creating a GrafTask object
# (B) creating a processor of the desired flavour by means of the processor_factory method of GrafTask.
#
# In (A) the laf source and compiled source are identified. If needed, the source will be recompiled, which takes 10 minutes.
# In (B) a task execution object is created, where each flavour corresponds to a subclass of the superclass GrafTask_Base.
# Depending on the flavour there will be additional directives, which are specified in the code for the task itself.

# After setting up the GrafTask object given by the factory, the task, chosen by the user on the command line, is loaded.
# This tasks specifies directives for processing and contains a method task, which performs the task itself.

graftask = GrafTask(
    task=args.task,
    source=args.source,
    data_dir='{}/{}'.format(data_root, laf_source),
    data_file=source_choices[args.source],
    bin_dir='{}/{}/{}/{}'.format(data_root, compiled_source, args.source, bin_dir),
    result_dir='{}/{}/{}/{}'.format(data_root, compiled_source, args.source, args.task),
    compile=args.forcecompile,
).processor_factory(
    flavour=process_flavours[args.flavour],
    flavour_detail=args.flavour,
    index=args.forceindex
)
sys.path.append("{}/tasks".format(cur_dir))

exec("from {} import precompute".format(args.task))
exec("from {} import task".format(args.task))

graftask.setup(precompute)
task(graftask) 
graftask.finish_task()
