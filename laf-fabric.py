# -*- coding: utf8 -*-
import os
import codecs
import glob
import sys
import traceback
import collections
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
sys.path.append("{}/tasks".format(cur_dir))

task_dir = 'tasks'
task_choices = [os.path.splitext(os.path.basename(f))[0] for f in glob.glob("tasks/*.py")]

process_flavours = {
    "plain": "plain",
    "memo": "memo",
    "assemble": "assemble",
    "assemble_all": "assemble",
}

def weave(data):
    n_rows = max([len(col) for col in data])
    woven = []
    for i in range(n_rows):
        woven.append([col[i] if len(col) > i else None for col in data])

    index = collections.defaultdict(lambda: {}) 

    n_row = -1
    for row in woven:
        n_row += 1
        n_col = -1
        for item in row:
            n_col += 1
            if item:
                index[n_col][n_row] = item

    return (woven, index)



def prompt(prompt_data, cur):
    os.system("clear")
    sys.stderr.write(u''' ┌─SOURCE───────────────────────────┬─TASK─────────────────────────────┬─FLAVOUR──────────────────────────┐
''')
    sepchar = u'│'
    sepchar_cur = u'█'
    fillchar = u' '
    fillchar_cur = u'█'

    n_row = -1
    for row in prompt_data:
        n_row += 1
        this = [None for i in range(len(row))]
        this_n = [None for i in range(len(row))]
        for i in range(len(row)):
            this[i] = row[i] if row[i] else ''
            this_n[i] = str(n_row + 1) if row[i] else ''
        
        fill = [fillchar for i in range(len(row))]
        sep = [sepchar for i in range(len(row) + 1)]

        for i in range(len(row)):
            if n_row == cur[i]:
                fill[i] = fillchar_cur
                sep[i] = sepchar_cur
                sep[i+1] = sepchar_cur

        this_f = [None for i in range(len(row))]
        this_nf = [None for i in range(len(row))]
        for i in range(len(row)):
            this_f[i] = this[i] + (fill[i] * (30 - len(this[i])))
            this_nf[i] = (fill[i] * (3 - len(this_n[i]))) + this_n[i]

        line = u' '
        for i in range(len(row)):
            line += sep[i] + this_nf[i] + fill[i] + this_f[i]
        sys.stderr.write(line + sep[3] + "\n")

    sys.stderr.write(u''' └──────────────────────────────────┴──────────────────────────────────┴──────────────────────────────────┘
''')

def command_loop():
    quitcommands = [
        'q',
        'quit',
        'x',
        'exit',
        'bye',
        'stop',
    ]

    runcommands = [
        'e',
        'exec',
        'execute',
        'r',
        'run',
    ]

    kinds = {}

    kindrep = [
        'source',
        'task',
        'flavour',
    ]

    default = [
        2, # source
        0, # task
        0, # flavour
    ]

    for i in range(len(kindrep)):
        krlong = kindrep[i]
        krshort = krlong[0]
        kinds[krlong] = i
        kinds[krshort] = i

    (prompt_data, index) = weave((sorted(source_choices.keys()), sorted(task_choices), sorted(process_flavours)))
    cur = [default[i] for i in range(len(index))]

    goodcommand = True
    message = ''
    while True:
        prompt(prompt_data, cur)
        if not goodcommand:
            sys.stderr.write("XXX wrong command\n")
        sys.stderr.write(message)
        message = ''
        command = raw_input("laf-fabric $ ")
        goodcommand = False
        if '=' in command:
            components = command.split('=')
            if len(components) == 2:
                kind = components[0].strip(" ").lower()
                if kind not in kinds:
                    message += "what do you mean by {}? [{}]\n".format(components[0], ",".join(kindrep))
                    continue
                kind = kinds[kind]
                number = components[1].strip(" ")
                if not number.isdigit():
                    message += "which {} do you mean by {}? [{} - {}]\n".format(kindrep[kind], components[1], 1, len(index[kind]))
                    continue
                number = int(number) - 1
                if number < 0:
                    message += "{} {} does not exist. [{} - {}]\n".format(kindrep[kind], components[1], 1, len(index[kind]))
                    continue
                if number >= len(index[kind]):
                    message += "{} {} does not exist. [{} - {}]\n".format(kindrep[kind], components[1], 1, len(index[kind]))
                    continue
                goodcommand = True
                cur[kind] = number
            else:
                message += "Too many '=' in command\n"
                continue
        else:
            command = command.replace(' ','').lower()
            if command in quitcommands:
                goodcommand = True
                break
            elif command in runcommands:
                run = True
                for i in range(len(index)):
                    if cur[i] == None:
                        message += "Cannot run if {} is unspecified\n".format(kindrep[i])
                        run = False
                if not run:
                    continue
                goodcommand = True
                good = True
                try:
                    runtask(*[index[col][cur[col]] for col in range(len(index))])
                except:
                    good = False
                    print traceback.format_exc()
                raw_input("Task execution {}. Press any key to continue ...".format('completed' if good else 'failed')) 
            else:
                continue


graftask = None

def runtask(source, task, flavour):
    '''Runs a single task in a given setting.

    Depending on the parameters it loads and unloads data.
    It takes care not to reload things that are already in memory.
    However, it will unload everything that is not needed for this task in this setting, in order not to burden tasks with unnecessary memory consumption.

    Even if none of *source*, *task*, and *flavour* have changed since the last run, it might be needed to unload and load indexes, because
    the code for the task itself may have changed.

    If *source* has changed, we really do have to start a new

    Args:
        source (str): the name of the source that provides the data for this task.
        task (str): the name of the task.
        flavour (str): the optimization flavour to be used when executing the task.
    '''
    print "Running task(source={}, task={}, flavour={})".format(source, task, flavour)
    global graftask
    if not graftask or graftask.source != source:
        if graftask:
            graftask = None # take care that there are no other pointers to this object
        graftask = GrafTask(
            task=task,
            source=source,
            data_dir='{}/{}'.format(data_root, laf_source),
            data_file=source_choices[source],
            bin_dir='{}/{}/{}/{}'.format(data_root, compiled_source, source, bin_dir),
            result_dir='{}/{}/{}/{}'.format(data_root, compiled_source, source, task),
            compile=False,
        ).processor_factory(
            flavour=process_flavours[flavour],
            flavour_detail=flavour,
            index=False
        )

        exec("from {} import precompute".format(task))
        exec("from {} import task".format(task))

        graftask.setup(precompute)
        task(graftask) 
        graftask.finish_task()
    else:
        if graftask.source == source and graftask.task == task and graftask.flavour_detail == flavour:
            exec("from {} import precompute".format(task))
            exec("from {} import task".format(task))

            graftask.stamp.reset()
            task(graftask) 
            graftask.finish_task()
        else:
            print "Rerun with different context not yet implemented"

command_loop()
