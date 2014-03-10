import laf
import array
from laf.notebook import Notebook
from laf.laf import LafFiles

def testlaf():
    processor = Notebook()
    files = LafFiles(processor.laftask)
    files.print_file_list(files.requested_files(
        'bhs3.txt.hdr',
        'testannot',
        True,
        ('node', 'edge'),
        (
            ('shebanq', 'db', 'otype', 'node'),
            ('shebanq', 'parents', '', 'edge'),
        ),
    ))

dkeypath = ('a', 'b', 'c')
dkeyname = ('d')

for comp in dkeypath + (dkeyname,):
    print(comp)
