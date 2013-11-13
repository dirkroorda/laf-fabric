# -*- coding: utf8 -*-
import os
import glob
import sys
import argparse
from graf import GrafTask

## USAGE

# python do_graf_task --source=name --task=name --optim=name --force-compile --force-index

# Executes a task on source material, using a certain method of optimization.
# Optionally recompiles the source and indexes.
# Normally, the program detects when recompilation of sources is needed anda recreation of indexes.

## CONFIG START

# directory structure:
#
# data_root => { laf_source, compiled_source }
# compiled_source => { specific_source* }
# specific_source => { bin_dir, task* }
# task => { __log_task.txt, output_file* }
# bin_dir => { laf_file*.bin, laf_file*.txt, index*.bin }
#

# directory under which the uncompiled laf source resides and the directory with compiled laf resources.
data_root = '/Users/dirk/Scratch/shebanq/results'

# subdirectory of root where the uncompiled laf resource is found 
laf_source = 'laf'

#subdirectory of root where the compiled laf resource is found
compiled_source = 'db'

# sources are subsets of the given laf resource. 
# A subset is specified by a GrAF header file that selects some of the files with regions, nodes, edges and annotations
# that are present in the LAF resource.
source_choices = {
    "tiny": 'bhs3.txt-tiny.hdr',
    "test": 'bhs3.txt-bhstext.hdr',
    "total": 'bhs3.txt.hdr',
}

## CONFIG END

# subdirectory of specific tasks where the compiled data is found
bin_dir = 'bin'

cur_dir = os.getcwd()

# tasks are the python scripts in the tasks directory, below the current directory which must be
# the directory of this script.
# The chosen task is imported by the graf module.

task_dir = 'tasks'
task_choices = [os.path.splitext(os.path.basename(f))[0] for f in glob.glob("tasks/*.py")]

# The action of feature lookup for nodes and edges is costly, because of the compact nature of the compiled data.
# So we study means of improving the efficiency of feature lookups.
#
# Process flavours are optimizations of the ways in tasks are executed.
# The assemble flavours build indexes (and save and load them) for looking up features.
# The assemble_all flavour builds an index for all features. This drives memory usage close to unacceptable levels.
# Assemble_all does not save and reload indexes between runs. It takes one to two minutes.
# Assemble (without all) selectively indexes the features that have been declared in the task. It usually takes 40 seconds to 2 minutes.
# The computed indexes are saved, and loaded the next time. Loading takes 10 to 15 seconds.
# Currently, this is the most efficient way of running tasks. 
#
# The memo flavour stores results of feature lookups to be used instead of subsequent lookups.
# The results are not promising. Probably in many tasks the majority of features needs to be computed only once.
# Moreover, there is overhead in deciding whether a value has to be facthed from cache or to be computed fresh.
#
# The plain flavour does not do optimizations.
# Typically, a task that takes 3 minutes under the plain flavour, takes a few seconds under the assemble flavour.
# The plain flavour does not have to compute/load indexes, so the task is started 10 to 15 seconds earlier.
# When debugging, this can be handy.
 
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
