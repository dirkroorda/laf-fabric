LAF/GrAF and data analysis
==========================

What is LAF/GrAF
----------------
LAF/GrAF is a framework for representing linguistic source material plus associated annotations.
LAF, Linguistic Annotation Framework is an ISO standard (`24612:2012 <http://www.iso.org/iso/catalogue_detail.htm?csnumber=37326>`_) that describes the organization of the data.
GrAF, Graph Annotation Framework is a set of `schemas <http://www.xces.org/ns/GrAF/1.0/>`_ for the XML-annotations in a LAF resource.

Despite the L of linguistics, there is nothing particularly linguistic to LAF.
LAF describes data that comes as a linearly ordered *primary data* stream (audio, video, text, or anything that has a one dimensional order), in which *regions* can be defined.
*Annotations* are key=value pairs or *feature structures* in general, which conform to the joint definition with the Text Encoding Initiative (`TEI Feature Structures <http://www.tei-c.org/release/doc/tei-p5-doc/en/html/FS.html>`_ and `ISO version <http://www.iso.org/iso/catalogue_detail.htm?csnumber=37324>`_).
Between the primary data and the annotations is a *graph* of *nodes* and *edges*. Some nodes are linked to regions of primary data. Some nodes are linked to other nodes by means of edges. An annotation may refer to a node or to an edge, but not both. 

So, features target the primary data through annotations. Annotations can be labeled and they can be organized in *annotation spaces*.

Existing tools for LAF/GrAF resources
-------------------------------------
There is an interesting Python module (`POIO, Graf-python <http://media.cidles.eu/poio/graf-python/>`_)
that can read generic GrAF resources.
It exposes an API to work with the graph and annotations of such resources.
However, when feeding it a resource with 430 k words and 2 GB of annotation material, the performance is such that the graph does not fit into memory of a laptop. Clearly, the tool has been defined for bunches of smaller GrAF documents, and not for a single documents of 500 k words and GBs of annotation material.

This workbench
--------------
The present workbench seeks to remedy that situation. Its aim is to provide a framework on top of which users can write small Python scripts that perform analytic tasks on big GrAF resources. It achieves this goal by efficient storage of data, both on disk and in RAM and by precomputing indices.

Limitations
^^^^^^^^^^^
While the POIO-Graf-python module mentioned above is capable to read generic resources, the present Graf tool is less generic.
It does not support the full complexity of the Graf model.
In particular, it does not support annotation spaces, it does not read dependencies, and it cannot handle feature structures in full generality, it only handles key-value pairs.

Future work
^^^^^^^^^^^
My plans for further development are:

#. gain experience with the tool by adding several example tasks
#. improve the API, add extra primitives, make it more user friendly
#. look out for even better performance for various tasks
#. increase the support for more GrAF features, and to make it fully compatible
#. merge the tool with the existing POIO-Graf-python tool, preferably as a user selectable implementation choice 

