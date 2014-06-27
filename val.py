import sys
import subprocess
import os

root = '/Users/dirk/laf-fabric-data/bhs4/laf'
decl = '/Users/dirk/laf-fabric-data/bhs4/decl'
schema = '{}/graf-standoff.xsd'.format(decl)
app = '/Users/dirk/Dropbox/DANS/current/demos/github/laf-fabric/emdros2laf/xml'

xmllint_cmd = ''

def runx(cmd):
    return subprocess.call(cmd + ' 2>&1', shell = True)
#def runx(cmd): return subprocess.call(cmd, shell = True)

def validate(xf):
    myfile = '{}/{}'.format(root, xf)
    os.environ['XML_CATALOG_FILES'] = '{}/xmllint_cat.xml'.format(app)
    with open(myfile, 'r') as h:
        for l in h: sys.stdout.write(l)
    return runx('xmllint --noout --nonet --stream --schema {} {}'.format(schema, myfile))

print("code={}".format(validate('bhs4_lingo.xml')))
