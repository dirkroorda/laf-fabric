from distutils.core import setup
setup(
    name='laf-fabric',
    version='4.3.3',
    author='Dirk Roorda',
    author_email='dirk.roorda@dans.knaw.nl',
    description='''Tools to read LAF resources (Linguistic Annotation Framework ISO 24612:2012) and analyse them efficiently.
    With additions for the Hebrew Text Database of the ETCBC (Eep Talstra Centre for Bible and Computing''',
    packages=['laf', 'etcbc', 'emdros2laf'],
    url='http://laf-fabric.readthedocs.org',
    package_data = {
        'emdros2laf': ['templates/*', 'xml/*'],
    },
)
