import sys
from etcbc.emdros import patch

modes = {
    'test': (2, '/Users/dirk/Downloads', '/Users/dirk/Downloads', 'bhs4_test', 'etcbc4_test'),
    'full': (1000000, '/Users/dirk/Downloads', '/Users/dirk/Downloads', 'bhs4', 'etcbc4'),
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
patch(chunk, '{}/{}.mql'.format(rooti, fnamei), '{}/{}.mql'.format(rooto, fnameo))
