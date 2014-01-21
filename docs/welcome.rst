Welcome
#######
.. image:: /files/gender_graph.png

The word **fabric** denotes a texture, and a LAF resource can be seen as a texture of annotations to
a primary data source. 

In other languages than English, and possibly in English as well, fabric also denotes a place were 
stuff is made. For etymology, see `faber <http://en.wiktionary.org/wiki/faber>`_.
The location of industry, a factory (but that word derives from the slightly different 
`facere <http://en.wiktionary.org/wiki/facio>`_).

What if you want to study the data that is in the fabric of a LAF resource?
You need tools. And what if you want to add your own tapestry to the fabric?

You need an interactive environment where tools can be developed and data can be combined.

This is the LAF Fabric, and here are some examples of what you can do with it:

* `gender notebook <http://nbviewer.ipython.org/github/dirkroorda/laf-fabric/blob/master/notebooks/gender.ipynb>`_
* `cooccurrences notebook <http://nbviewer.ipython.org/github/dirkroorda/laf-fabric/blob/master/notebooks/cooccurrences.ipynb>`_

What's new
==========
3.2.0
^^^^^
Connectivity in the API. There is an object C by which you can traverse from nodes via annotated edges to other nodes.

Documentation organization: separate section for API reference.

Incompatible changes:

* laf.task.LafTask.API() now returns a 6-tuple instead of a 5-tuple: C has been added.
* nodes or edges annotated by an empty annotation will get a feature based on the annotation label.
  This feature yields value ``''`` (empty string) for all nodes or edges for which it is defined. Was ``1``.
  **Existing LAF resources should be recompiled**.
