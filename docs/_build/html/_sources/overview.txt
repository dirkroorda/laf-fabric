LAF/GrAF and data analysis
==========================

What is LAF/GrAF
----------------
LAF/GrAF is a framework for representing linguistic source material plus associated annotations.
LAF, Linguistic Annotation Framework is an
ISO standard (`24612:2012 <http://www.iso.org/iso/catalogue_detail.htm?csnumber=37326>`_)
that describes the organization of the data.
GrAF, Graph Annotation Framework, is a set of
`schemas <http://www.xces.org/ns/GrAF/1.0/>`_ for the XML-annotations in a LAF resource.

Despite the L of linguistics, there is nothing particularly linguistic to LAF.
LAF describes data that comes as a linearly ordered *primary data* stream
(audio, video, text, or anything that has a one dimensional order), in which *regions* can be defined.
*Annotations* are key=value pairs or *feature structures* in general,
which conform to the joint definition with the Text Encoding Initiative
(`TEI Feature Structures <http://www.tei-c.org/release/doc/tei-p5-doc/en/html/FS.html>`_
and `ISO version <http://www.iso.org/iso/catalogue_detail.htm?csnumber=37324>`_).
Between the primary data and the annotations is a *graph* of *nodes* and *edges*.
Some nodes are linked to regions of primary data.
Some nodes are linked to other nodes by means of edges.
An annotation may refer to a node or to an edge, but not both. 

So, features target the primary data through annotations.
Annotations can be labeled and they can be organized in *annotation spaces*.

.. _data:

Data
----
Although this tool is written to deal with LAF resources in general, it has been developed with a particular
LAF resource in mind:
the `WIVU text database of the Hebrew Bible <http://www.dans.knaw.nl/en/content/categorieen/projecten/text-database-hebrew-old-testament>`_.
This data set is available (by request) from the national research data archive in the Netherlands, DANS,
by following this persistent identifier:
`urn:nbn:nl:ui:13-ukhm-eb <http://www.persistent-identifier.nl/?identifier=urn%3Anbn%3Anl%3Aui%3A13-ukhm-eb>`_.
This data is not yet in LAF format.
The `SHEBANQ <http://www.slideshare.net/dirkroorda/shebanq-gniezno>`_ project has
converted the database into LAF (the conversion code is in `GitHub project wivu2laf <https://github.com/dirkroorda/wivu2laf>`_),
and the resulting LAF resource is a file set of 2.27 GB, being predominantly linguistic annotations.
It is this LAF resource that is the reference context for this workbench.
It is to be deposited into the DANS archive shortly, under an Open Access licence, with the
restriction that it may not be used commercially. 

Existing tools for LAF/GrAF resources
-------------------------------------
There is an interesting Python module (`POIO, Graf-python <http://media.cidles.eu/poio/graf-python/>`_)
that can read generic GrAF resources.
It exposes an API to work with the graph and annotations of such resources.
However, when feeding it a resource with 430 k words and 2 GB of annotation material,
the performance is such that the graph does not fit into memory of a laptop.
Clearly, the tool has been defined for bunches of smaller GrAF documents,
and not for a single documents of 500 k words and GBs of annotation material.

This workbench
--------------
The present workbench seeks to remedy that situation.
Its aim is to provide a framework on top of which users can write small Python scripts that
perform analytic tasks on big GrAF resources.
It achieves this goal by efficient storage of data, both on disk and in RAM and by precomputing indices.

Limitations
^^^^^^^^^^^
While the `POIO, Graf-python <http://media.cidles.eu/poio/graf-python/>`_ module
mentioned above is capable to read generic resources, the present Graf tool is less generic.
It does not support the full complexity of the Graf model.
In particular, it does not support annotation spaces, it does not read dependencies,
and it cannot handle feature structures in full generality, it only handles key-value pairs.
Currently, there is very little API support for dealing with *edges* and their features.

Future work
^^^^^^^^^^^
The current workbench has proven to function well for a small set of tasks.
This proves that the methodology works and that we can try more challenging tasks.
The direction of the future work should be determined by the experiences coming out of that.
That said, it is not difficult to spot immediate areas for improvement:

#. gain experience with the tool by adding more example tasks
#. improve the API, add extra primitives, especially for edges
#. make the workbench more programmer friendly
#. look out for even better performance for various tasks
#. increase the support for more GrAF features, and to make the workbench fully compatible with GrAF/LAF
#. merge the tool with the existing `POIO, Graf-python <http://media.cidles.eu/poio/graf-python/>`_,
   preferably as a user selectable implementation choice 

Rationale
---------
The paradigms for biblical research are becoming *data-driven*.
Researchers need increasingly sophisticated ways to get qualitative and quantitative data out of their resources.
They are in the best position to define what they need and ... to fulfill those needs.
To that end they need the freedom to access the data and tools relevant to them and to adapt them to their needs.

This workbench is a stepping stone for humanities researchers with limited time for programming
to the wonderful world of computing. With it they can extract data from their resources of interest and
feed it into other tools.

See for example the task :mod:`esther`, which codes in less than a page an extraction of **data tables** relevant to the
study of linguistic variation in the Hebrew Bible. These tables are suitable for subsequent data analysis
by means of the open source `statistics toolkit R <http://www.r-project.org>`_.

An other example is the task :mod:`proper`, which outputs a **vizualization** of the text of the Hebrew Bible in which
the syntactic structure is visible and the proper nouns and their gender.
With this visualization it becomes possible to discern genealogies from other genres with the unaided eye,
even without being able to read a letter of Hebrew.

All this code is on Github, workbench and example tasks.
Researchers are invited to develop their own tasks and share them, either through data archives or directly through 
Github. In doing so, they will create a truly state of the art research tool, adapted to
the scholarly needs of analysis, review and publication.

.. _author:

Author
------
This work has been undertaken first in November 2013 by Dirk Roorda, working for
`Data Archiving and Networked Services (DANS) <http://www.dans.knaw.nl/en>`_ and
`The Language Archive (TLA) <http://tla.mpi.nl>`_.
The work has been triggered by the execution of the
`SHEBANQ <http://www.slideshare.net/dirkroorda/shebanq-gniezno>`_ project
together with the researchers at the
`Eep Talstra Centre for Bible and Computing (ETCBC), VU University
<http://www.godgeleerdheid.vu.nl/nl/onderzoek/instituten-en-centra/eep-talstra-centre-for-bible-and-computer/index.asp>`_.

See also a description on the `DANS-lab site <http://demo.datanetworkservice.nl/mediawiki/index.php/LAF_Fabric>`_.

Thanks to Martijn Naaijer and Gino Kalkman for first experiments with the workbench.



