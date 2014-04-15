import sys
import codecs

from .mylib import *
from .config import Config
from .etcbc import Etcbc
from .laf import Laf
from .validate import Validate
from .transform import Transform

def init():
    '''Initialize all objects needed for transformation from ETCBC to LAF.
    '''
    global cfg
    cfg = Config()

    global val
    val = Validate(cfg)

    global wv
    wv = Etcbc(cfg)

    global lf
    lf = Laf(cfg, wv, val)

    global tr
    tr = Transform(cfg, wv, lf)

    global prog_start
    prog_start = Timestamp()

    global task_start
    task_start = Timestamp()


def dotask(part):    
    ''' Generate the files corresponding to part
    '''
    print("INFO: Start Task {}".format(part))
    task_start = Timestamp()
    tr.transform(part)
    print("{} - {}".format(prog_start.elapsed(), task_start.elapsed()))
    print("INFO: End Task {}".format(part))

def final():
    ''' Generate the header files, 
    validate the generated files, only if there is a command line flag present that requests it
    and report the outcome
    '''
    task_start = Timestamp()
    lf.makeheaders()
    val.validate()
    val.report()
    lf.report()
    print("{} - {}".format(prog_start.elapsed(), task_start.elapsed()))
 
def processor():
    ''' This is the entry point for the program as a whole.
    It initializes,
    performs those parts that are specified on the command line,
    and then finalizes
    '''
    init()
    print("{} - {}".format(prog_start.elapsed(), task_start.elapsed()))
    print("INFO: Doing parts: {}".format(','.join(cfg.given_parts)))
    for part in cfg.given_parts:
        dotask(part)
    final()
