import sys
import collections

from laf.fabric import LafFabric
fabric = LafFabric()

fabric.load('calap', '--', 'plain', {
    "xmlids": {"node": False, "edge": False},
    "features": ('''
        otype
        surface_consonants
        psp
        book chapter verse verse_label
    ''',''),
    "primary": True,
})
exec(fabric.localnames.format(var='fabric'))
