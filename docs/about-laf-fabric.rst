About
#####

Description
===========
LAF-fabric is a Python tool for running Python scripts with access to the information in a LAF resource.
It has two major components:

#. a LAF compiler for transforming a LAF resource into binary data that can be loaded very into Python data structures;
#. an execution environment that gives Python scripts access to LAF data and is optimized for feature lookup.

The selling point of LAF-fabric is performance, both in terms of speed and memory usage.
The second goal is to make it really easy for you to write analytic tasks straightforwardly in terms of LAF concepts
without bothering about performance.

Both points go hand in hand, because if LAF-fabric needs too much time to execute your tasks,
it becomes very tedious to experiment with them.
I wrote LAF-fabric to make the cycle of trial and error with your tasks as smooth as possible.

Workflow
========
The typical workflow is:

#. download a LAF resource [#laf]_ to your computer
   (or work with a compiled version [#nolaf]_).
#. install LAF-fabric on your computer.
#. adapt a config file to change the location of the work directory.
#. write your own task in an `iPython notebook <http://ipython.org>`_, or
   write your task as script and put it into LAF-Fabric.
#. run the code cells in an `iPython notebook <http://ipython.org>`_, or run LAF-fabric from the command line.

Notebook mode
-------------
You can write a task as a stand-alone script, importing LAF-fabric as a module, called *graf*.
You can then break such a script up into chunks of code, and paste them in the code cells of an 
`iPython notebook <http://ipython.org>`_.
See the *notebooks* directory for executable examples.

Workbench mode
--------------
LAF-fabric behaves in the same pattern as the ``mysql>`` prompt for a database. You can use it as in interactive
command interpreter that lets you select and run tasks.
You can also invoke it to run a single task without interaction.

During a prompt session you can make a selection of source and *annox* and task.
*Annox* is shorthand for *extra annotation package*.

You can run your selection, modify the selection, run it again, ad libitum.
While this session is alive, loading and unloading of data will be done only when it is really needed.
Data that is needed for one task, will be reused for the next task.

So if you have to debug a script, you can do so without repeatedly waiting for the loading of the data.

The first time a source or annox is used, the LAF resource will be compiled.
Compiling of the full Hebrew Bible source may take considerable time,
say 10 minutes for a 2 GB XML annotations on a Macbook Air (2012).
The compiled source will be saved to disk across runs of LAF-fabric.
Loading the compiled data takes, in the same setting with the Hebrew Bible, less than a second,
but then the feature data is not yet loaded, only the regions, nodes and edges.
If you need the original XML identifiers for your task, there will be 2 to 5 seconds of extra load time.

And you can even cut out this loading time by running multiple tasks in a single session.

After loading the data, LAF-fabric invokes your task script(s).

Both modes
----------
You must declare the LAF-features that you use in your task, and LAF-fabric will load data for them.
Loading a feature typically adds 0.1 to 1 second to the load time.
It will also unload the left-over data from previous tasks for features
that the current task has not declared.
In this way we can give each task the maximal amount of RAM.

License
=======

This work is freely available, without any restrictions.
It is free for commerical use and non-commercial use.
The only limitation is that parties that include this work may not in anyway restrict the freedom
of others to use it.

Designed for Performance
========================
Since there is a generic LAF tool for smaller resources,
(`POIO, Graf-python <http://media.cidles.eu/poio/graf-python/>`_)
this tool has been designed with performance in mind. 
In fact, performance has been the most important design criterion of all.
In this section the design decisions and particulars are listed.
There are also a few simplifications involved, see the section of GrAF :ref:`feature coverage` below.

There are several ideas involved in compiling a LAF resource into something that is compact, fast loadable, and amenable to efficient computing.

#. Replace nodes and edges and regions by integers.
#. Store relationships between integers in *arrays*, that is, Python arrays.
#. Store relationships between integers and sets of integers also in *arrays*.
#. Keep individual features separate.
#. Compress data when writing it to disk.

Explanation of these ideas
--------------------------
**Everything is integer**
In LAF the pieces of data are heavily connected, and the expression of the connections are XML identifiers.
Besides that, absolutely everything gets an identifier, whether or not those identifiers are targeted or not.
In the compiled version we get rid of all XML identifiers.
We will represent everything that comes in great quantities by integers: regions, nodes, edges, feature values.
But feature names, annotation labels and annotation spaces will be kept as is.

**Relationships between integers as Python arrays**
In Python, an array is a C-like structure of memory slots of fixed size.
You do not have arrays of arrays, nor arrays with mixed types.
This makes array handling very efficient, especially loading data from disk and saving it to disk.
Moreover, the amount of space in memory needed is like in C, without the overhead a scripting language usually adds to its data types.

There is an other advantage:
a mapping normally consists of two columns of numbers, and numbers in the left column map to numbers in the right column.
In the case of arrays of integers, we can leave out the left column: it is the array index, and does not have to be stored.

**Relationships between integers as Python arrays**
If we want to map numbers to sets of numbers,
we need to be more tricky, because we cannot store sets of numbers as integers.
What we do instead is: we build two arrays, the first array points to data records in the second array.
A data record in the second array consists of a number giving the length of the record,
followed by that number of integers.
The function :func:`arrayify() <graf.model.arrayify>` takes a list of items and turns it in a double array. 

**Keep individual features separate**
A feature is a mapping from either nodes or edges to string values. Features are organized by the annotations
they occur in, since these annotations have a *label* and occur in an *annotation space*. 
We let features inherit the label and the space of their annotations. Within space and label, features are distinguished by name.
And the part of a feature that addresses edges is kept separate from the part that addresses nodes.

So an individual feature is identified by *annotation space*, *annotation label*, *feature name*, and *kind* (node or edge).
For example, in the Hebrew Bible data, we have the feature::

    shebanq:ft.suffix (node)

with annotation space ``shebanq``, annotation label ``ft``, feature name ``suffix``, and kind ``node``.
The data of this feature is a mapping that assigns a string value to each of more than 400,000 nodes.
So this individual feature represents a significant chunk of data.

The individual features together take up the bulk of the space.
In our example, they take 145 MB on disk, and the rest takes only 55 MB.
Most tasks require only a limited set of individual features.
So when we run tasks and switch between them, we want to swap feature data in
and out.
The design of LAF-fabric is such that feature data is neatly chunked per individual feature.

.. note::
    Here is the reason that we do not have an overall table for feature values, identified by integers.
    We miss some compression here, but with a global feature value mapping, we would burden every task with a significant
    amount of memory.
    Moreover, the functionality of extra annotation packages is easier to implement
    when individual features are cleanly separable.

.. note::
    Features coming from the source and features coming from the extra annotation package will be merged
    before the you can touch them in tasks.
    This merging occurs late in the process, even after the loading of features by LAF-fabric.
    Only at the point in time when a task declares the names of the API methods
    (see :meth:`API <graf.task.GrafTask.API>`)
    the features will be assembled into objects.
    At this point the source features and annox features finally get merged.
    When a task no longer uses a merged feature, or want to merge with a different package,
    the feature data involved will be cleared, so that a fresh merger can take place.

Consequences
------------
The concrete XML identifiers present in the LAF resource are moved to the background. 
Only if your task asks for them explicitly, they can be loaded.
In that case you get mappings between the xml-identifiers and the internal integer codes
for nodes and for edges. This requires considerable overhead.
     
Whoever designs a LAF resource to be worked on by LAF-fabric,
should not rely on the values of the XML identifiers to derive implicit meanings from.
I did that in initial stages, producing identifiers ``n_1, n_2, e_1, e_2`` etcetera for node 1, 2 and edge 1, 2.
There is nothing wrong with such identifiers, but do not expect to determine in your tasks whether
something is a node or edge by looking at an identifier.

.. note::
    There are cases where a task really needs the original identifiers. 
    Tasks that create new annotations for existing nodes or edges,
    need to know the xml-identifiers used in the source.

.. _feature coverage:

GrAF feature coverage
=====================
This tool cannot deal with LAF resources in their full generality.

In LAF, annotations have labels, and annotations are organized in annotation spaces.
In a previous version, LAF-fabric ignored annotation spaces altogether.
Now annotation spaces are fully functional.

*primary data*
    LAF-fabric deals with primary data in the form of text.
    It is not designed for other media such as audio and video.
    Further, it is assumed that the text is represented in UNICODE, in an
    encoding supported by python, such as utf-8.
    LAF-fabric assumes that the basic unit is the UNICODE character.
    It does not deal with alternative units such as bytes or words. 

*feature structures*
    The content of an annotation can be a feature structure.
    A feature structure is a set of features and sub features, ordered again as a graph.
    LAF-fabric can deal with feature structures that are merely sets of key-value pairs.
    The graph-like model of features and subfeatures is not supported.

*annotations*
    Even annotations get lost. LAF-fabric is primarily interested in features and values.
    It forgets the annotations in which they have been packaged except for: 

    * the annotation space,
    * the annotation label,
    * the target kind of the annotation (node or edge)

*dependencies*
    In LAF one can specify the dependencies of the files containing regions, nodes, edges and/or annotations.
    LAF-fabric assumes that all dependent files are present in the resource.
    Hence LAF-fabric reads all files mentioned in the GrAF header, in the order stated in the GrAF header file.
    This should be an order in which regions appear before the nodes that link to them,
    nodes before the edges that connect them, and nodes and edges before the annotations that target them.

Future directions
=================
LAF-Fabric has proven to function well for a small set of tasks.
This proves that the methodology works and that we can try more challenging things.
The direction of the future work should be determined by your research needs.

Adding new annotations
----------------------
While LAF-Fabric supports adding an extra annotation package to the existing LAF resource,
and contains an example workflow to create such packages, this process has not been
honed by practice yet.

We are working on concrete tasks with real data as of January 2014.

Visualization
-------------
If you develop tasks in notebook mode, you can invoke additional packages for
data analysis and visualization right after your task has been completed in the notebook.

The division of labour is that LAF-Fabric helps you to extract the relevant data from the resource,
and outside LAF-Fabric, but still inside your notebook, you continue to play with that data.

When we get more experience with visualization, we might need new ways of data extraction, which
would drive a new wave of changes in LAF-Fabric.

Graph methodology and full feature structures
---------------------------------------------
LAF-Fabric has not been implemented as a graph database.
We might adopt more techniques from graph databases to make it more compatible with
current graph technology.
We could use the python `networkx <http://networkx.github.io/#>`_ module for that.
That would also help to implement feature structures in full generality.

API completion
--------------
Many reasonable candidates for an API have not yet been implemented. Basically we have only:

*node iterator*
    iterator that produces nodes in the order by which they are anchored to the primary data (which are linearly ordered).
*feature lookup*
    a class that gives easy access to feature data and has methods for feature value lookup and mapping of
    feature values.
*xml identifier mapping*
    a mapping from orginal xml identifiers to integers.
*primary data access*
    The primary data can be accessed through nodes that are linked to regions of primary data.

Probably it is also handy to make custom node sets so that we can use python's set methods
to manipulate with node sets.

.. note:: Python does not have strict encapsulation of data structures,
    so by just inspecting the classes and objects you can reach out
    for all aspects of the LAF data that went into the compiled data.
    See the GrAF :ref:`feature coverage` for a specification of what data ends up in the compilation.

.. rubric:: Footnotes

.. [#laf] A LAF resource is a directory with a primary data file, annotation files and header files.
   This program has been tested with :ref:`LAF version of the Hebrew Bible <data>`.

.. [#nolaf] It is perfectly possible to run the workflow without the original LAF resource.
   If somebody has compiled a LAF resource for you, he only need to give you the compiled data,
   and let the LAF source in the configuration point to something non-existent.
   In that case LAF-fabric will not complain, and never attempt to recompile the original resource.
   You can still add extra annotation packages, which still can be compiled against the original LAF source,
   since the original XML identifiers are part of the compiled data.
   In case of the Hebrew Bible LAF resource: the original resource is over 2 GB on disk,
   while the compiled binary data is less than 200 MB.
