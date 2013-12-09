LAF Fabric
##########

.. image:: files/logo.png

(for provenance of this image, see [#laffabric]_)

The word **fabric** denotes a texture, and a LAF resource can be seen as a texture of annotations to
a primary data source. 

In other languages than English, and possibly in English as well, fabric also denotes a place were 
stuff is made. For etymology, see `faber <http://en.wiktionary.org/wiki/faber>`_.
The location of industry, a factory (but that word derives from the slightly different 
`facere <http://en.wiktionary.org/wiki/facio>`_).

What if you want to study the data that is in the fabric of a LAF resource?
You need tools. And what if you want to add your own tapestry to the fabric?

You need an environment where tools can be developed and data can be combined.

This is the LAF Fabric.

What is LAF/GrAF
================
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
which conform to the joint definition of
`TEI Feature Structures <http://www.tei-c.org/release/doc/tei-p5-doc/en/html/FS.html>`_
and `ISO 24610 <http://www.iso.org/iso/catalogue_detail.htm?csnumber=37324>`_).
Between the primary data and the annotations is a *graph* of *nodes* and *edges*.
Some nodes are linked to regions of primary data.
Some nodes are linked to other nodes by means of edges.
An annotation may refer to a node or to an edge, but not both. 

So, features target the primary data through annotations.
Annotations can be labeled and they can be organized in *annotation spaces*.

.. _data:

Data
====
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
=====================================
There is an interesting Python module (`POIO, Graf-python <http://media.cidles.eu/poio/graf-python/>`_)
that can read generic GrAF resources.
It exposes an API to work with the graph and annotations of such resources.
However, when feeding it a resource with 430 k words and 2 GB of annotation material,
the performance is such that the graph does not fit into memory of a laptop.
Clearly, the tool has been developed for bunches of smaller GrAF documents,
and not for single documents with a half million words words and gigabytes of annotation material.

This workbench
==============
The present workbench seeks to remedy that situation.
Its aim is to provide a framework on top of which you can write small Python scripts that
perform analytic tasks on big GrAF resources.
It achieves this goal by compiling xml into compact binary data, both on disk and in RAM and by
selective loading of features. The binary data loads very fast. Only selected features will be loaded,
and after loading they will be blown up into data structures that facilitate fast lookup of values.

With this workbench you can add an additional annotation package to the basic resource.
You can also switch easily between additional packages without any need for recompiling the basic resource.
The annotations in the extra package may define new annotation spaces, but they can
also declare themselves in the spaces that exist in the basic source.
Features in the extra annotation package that coincide with existent features, override the existent ones,
in the sense that for targets where they define a different value,
the one of the added annotation package is taken. Where the additional package does not provide values,
the original values are used.

With this device it becomes possible for you to include a set of corrections to the original features.
Or alternatively, you can include the results of your own work, whether manual or algorithmic or both,
with the original data. You can then do *what-if* research on the combination.

Limitations
-----------
While the `POIO, Graf-python <http://media.cidles.eu/poio/graf-python/>`_ module
mentioned above is capable to read generic resources, the present Graf tool is less generic.
It does not support the full complexity of the Graf model.
In particular, it does not read dependencies,
and it cannot handle feature structures in full generality.
It only handles features in so far as they consist of key-value pairs, coded as::

    <f name="..." value="..."/>

Currently, there is very little API support for dealing with *edges*.

Future work
-----------
The current workbench has proven to function well for a small set of tasks.
This proves that the methodology works and that we can try more challenging things.
The direction of the future work should be determined by your research needs.

While the workbench supports adding an extra annotation package to the existing LAF resource,
it does not contain a ready made workflow to create such packages.
All ingredients are available though. The workbench API exposes the original XML identifiers to 
your tasks. So you can write a workbench task that emits a spreadsheet with text plus
node and edge identifiers, where you can put new annotations in an interlinear way.
An other workbench task could read that spreadsheet and compute the right XML identifiers and transform
it into a new annotation file that can be properly combined with the original resource.

I hope to find time to provide example tasks that exemplify this workflow.

That said, it is not difficult to spot other areas for improvement:

#. gain experience with the tool by adding more example tasks
#. improve the API, add extra primitives, especially for (ordered) node sets and edges
#. merge the tool with the existing `POIO, Graf-python <http://media.cidles.eu/poio/graf-python/>`_,
   preferably as a user-selectable implementation choice.
#. Investigate whether NEO4J could serve as a tool to implement feature structures in 
   full generality. 

Rationale
=========
The paradigms for biblical research are becoming *data-driven*.
If you work in that field, you need increasingly sophisticated ways
to get qualitative and quantitative data out of your texts.
You are in the best position to define what you need and ... to fulfill those needs,
provided you have some people in your group that have basic programming experience.

This workbench is a stepping stone for teams in digital humanities to the wonderful world of computing.
With it they you extract data from your resources of interest and feed it into your other tools.

See for example the task :mod:`esther`,
which codes in less than a page an extraction of **data tables** relevant to the
study of linguistic variation in the Hebrew Bible.
These tables are suitable for subsequent data analysis
by means of the open source `statistics toolkit R <http://www.r-project.org>`_.

An other example is the task :mod:`proper`, which outputs a **visualization** of the text of the Hebrew Bible
in which the syntactic structure of the text is visible plus the the genders of all the proper nouns.
With this visualization it becomes possible to discern genealogies from other genres with the unaided eye,
even without being able to read a letter of Hebrew.

The code of this LAF workbench is on Github, including example tasks and a example extra annotation packages.
You are invited to develop your own tasks and share them,
either through data archives or directly through Github.
In doing so, you (together) will create a truly state of the art research tool,
adapted to your scholarly needs of analysis, review and publication.

.. _author:

Author
======
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

Links
=====
**2013-12-09**
Abstract sent to `CLIN <http://clin24.inl.nl>`_ (Computational Linguistics In the Netherlands) accepted.
To be deliverd 2014-01-17. 

**2013-11-26**
`Vitamin Talk to the TLA team Nijmegen <http://www.slideshare.net/dirkroorda/work-28611072>`_.

.. rubric:: Footnotes

.. [#laffabric] Image found by an internet search on fabric and some other term that I forgot.
   By a google search on the image itself, I managed to find the
   `original context <http://www.hobbycraft.co.uk/hobbycraft-textured-fabric-reel-cream-2-metre/584337-1000>`_.

