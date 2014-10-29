import sys
from etcbc.emdros import patch

workdir = '/Users/dirk/Scratch/etcbc'

modes = {
    'test': (2, workdir, workdir, 'bhs4_test', 'etcbc4s_test'),
    'full': (1000000, workdir, workdir, 'bhs4', 'etcbc4s'),
}

if len(sys.argv) < 2:
    print("Usage\nlf-patch mode\nwhere mode in {}".format(modes.keys()))
    sys.exit(1)
mode = sys.argv[1]
if mode not in modes:
    print("Wrong mode [{}]".format(mode))
    print("Usage\nlf-patch mode\nwhere mode in {}".format(modes.keys()))
    sys.exit(1)

(chunk, rooti, rooto, fnamei, fnameo) = modes[mode]
patch(chunk, '{}/{}.mql'.format(rooti, fnamei), '{}/{}.mql'.format(rooto, fnameo), fnamei, fnameo)
