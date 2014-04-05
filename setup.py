from distutils.core import setup
setup(name='laf',
      version='4.1.1',
      author='Dirk Roorda',
      author_email='dirk.roorda@dans.knaw.nl',
      description='''Tools to read LAF resources (Linguistic Annotation Framework ISO 24612:2012) and analyse them efficiently.
With additions for the Hebrew Text Database of the ETCBC (Eep Talstra Centre for Bible and Computing''',
      packages=['laf', 'etcbc'],
      url='http://laf-fabric.readthedocs.org',
)
