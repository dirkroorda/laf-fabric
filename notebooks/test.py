import laf
from laf.notebook import Notebook
from laf.laf import LafFiles

processor = Notebook()
files = LafFiles(processor.laftask)

print(files.requested_files(
    'bhs3.txt.hdr',
    'testannot',
    True,
    ('node', 'edge'),
    (
        ('shebanq', 'db', 'otype', 'node'),
        ('shebanq', 'parents', '', 'edge'),
    ),
))
