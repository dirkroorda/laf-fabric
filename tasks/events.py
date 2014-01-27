import collections
import sys

load = {
    "xmlids": {
        "node": False,
        "edge": False,
    },
    "features": {
        "shebanq": {
            "node": [
                "db.otype",
            ],
            "edge": [
            ],
        },
    },
}

mode = 1

def task(processor):
    '''Crude visualization of the embedding structure of nodes based on node events.

    '''
    API = processor.API()
    F = API['F']
    NE = API['NE']

    out = processor.add_output("output.txt")

    if mode == 1:

        level = 0
        for (anchor, node, kind) in NE():
            otype = F.shebanq_db_otype.v(node)
            event_rep = ''
            if kind == 0:
                event_rep = "{}({}[{}]\n".format("\t"*level, otype, node)
                level += 1
            elif kind == 3:
                level -= 1
                event_rep = "{}{}[{}])\n".format("\t"*level, otype, node)
            elif kind == 1: 
                event_rep = "{}«{}[{}]\n".format("\t"*level, otype, node)
                level += 1
            elif kind == 2:
                level -= 1
                event_rep = "{}{}[{}]»\n".format("\t"*level, otype, node)
            out.write(event_rep)

    elif mode == 2:

        for (anchor, node, kind) in NE():
            kindr = '(' if kind == 0 else '«' if kind == 1 else '»' if kind == 2 else ')'
            otype = F.shebanq_db_otype.v(node)
            out.write("{} {:>7}: {:<10} {:<7}\n".format(kindr, anchor, otype, node))
