LAF workbench
#############

Description
===========
This workbench is a pure Python tool for running Python scripts with access to the information in a LAF resource.
It has two major components:

#. a LAF compiler for transforming a LAF resource into binary data that can be loaded very into Python data structures;
#. an execution environment that gives Python scripts access to LAF data and is optimized for feature lookup.

The selling point of the workbench is performance, both in terms of speed and memory usage.
The second goal is to make it really easy for users to write analytic tasks straightforwardly in terms of LAF concepts
without bothering about performance.

Workflow
========
The typical workflow is:

#. install a LAF resource somewhere on the filesystem.
   A LAF resource is a directory with a primary data file, annotation files and header files.
   In testing the workbench, I used a the :ref:`LAF version of the Hebrew Bible <data>`
#. install the LAF workbench package somewhere on a computing system.
#. in a configuration file, adapt the locations of the LAF directory and provide a work/results directory.
#. write your own script, and put it in the right directory.
#. run the workbench by invoking the calling script.

The workbench behaves in the same pattern as the ``mysql>`` prompt for a database. You can use it as in interactive
command interpreter that lets you select and run tasks.
You can also invoke it to run a single task without interaction.

During a prompt session you can make a selection of source and *annox* and task.
*Annox* is shorthand for *extra annotation package*.

You can run your selection, modify the selection, run it again, ad libitum.
While this session is alive, loading and unloading of data will be done only when it is really needed.
Data that is needed for one task, will be reused for the next task.

So I you have to debug a script, you can do so without repeatedly waiting for the loading of the data.

The first time a source or annox is used, the LAF resource will be compiled.
Compiling of the full source may take considerable time, say 10 minutes for a 2 GB XML annotations on a Macbook Air (2012).
The compiled source will be saved to disk across runs of the workbench.
Loading the compiled data takes, in the same setting with the Hebrew Bible, less than a second,
but then the feature data is not yet loaded, only the regions, nodes and edges.
If you need the original XML identifiers for your task, there will be 2 to 5 seconds of extra load time.

And you can even cut out this loading time by running multiple tasks in a single session.

After loading the data, the workbench invokes your task script(s).
You must declare the LAF-features that you use in your script, and the workbench will load data for them.
Loading a handful of features typically adds 0.5 seconds to the load time.
It will also unload the data for features that the script has not declared.
This is in order not to burden the RAM with data that does not pertain to the task.

License
=======

The intention is to make this work freely available, without any restrictions.
It is free for commerical use and non-commercial use.
The only limitation is that applications that include this work may not in anyway restrict the freedom
of others to use it.

How to use the workbench?
=========================
Here are detailed instructions for installing, configuring and using the workbench.

Installation
------------
In this Github project *LAF-Fabric* there is a Python package called :mod:`graf`.
It is a package without extension modules, so it will run from anywhere in your system.
I did not use the Python distutils to create a distribution that you can incorporate in your local Python installation.
You can just clone it from github and work with it right away::

    cd «directory of your choice»
    git clone https://github.com/dirkroorda/laf-fabric

You get a directory *laf-fabric* with the following inside:

* *graf*: the workbench itself, a Python package
* *laf-fabric.py*: a script to call the workbench
* *docs*: this documentation
* *tasks*: a directory with example tasks.

.. caution::

   If you develop your own tasks, put them in a separate directory, otherwise you
   may loose your work in them when you pull updates from Github.
   See *Configuration* below.

Before running the workbench, the calling script has to be configured.

Configuration
-------------
The configuration file script is *laf-fabric.cfg*.
In it is a configuration section::

    [locations]                                      # paths in the file system
    data_root = /Users/dirk/Scratch/shebanq/results  # working directory
    laf_source = laf                                 # subdirectory for the LAF data
    task_dir = tasks                                 # absolute or relative path to the directory with the tasks
    annox_dir = annotations                          # absolute or relative path to the directory with annotation add-ons
    base_bdir = db                                   # subdirectory for task results
    bin_subdir = bin                                 # subdirectory of compiled data
    feat_subdir = feat                               # subdirectory within bin_subdir for feature data
    annox_subdir = annox                             # subdirectory within bin_subdir for annox feature data

    [source_choices]                                 # several GrAF header files
    edge = bhs3.txt-edge.hdr
    tiny = bhs3.txt-tiny.hdr
    test = bhs3.txt-bhstext.hdr
    total = bhs3.txt.hdr

    [annox]
    empty = --
    header = _header_.xml
    
You are likely to want to change the following entries:

*data_root*
    point to the folder containing your LAF directory.
*laf_source*
    change into the directory name of your LAF directory.
*source_choices*
    Normally, a LAF resource has a *LAF-header file* and a *primary data header file*, aka. *the GrAF header file*.
    The workbench needs to look at a *GrAF header file*.
    This header file has references to all files that make up the resource.
    You might want to restrict the workbench to only part of the annotation files in the resource,
    e.g. if there are big annotation files that do not contain features that are relevant for your analysis.
    In that case, you can copy the original GrAF header file,
    and leave out all references to files that you do not want to take into consideration.
    The *source_choices* dictionary must contain all GrAF header files that you want to choose from.

.. _task_dir:

*task_dir*
    The directory in which your tasks can be found. If you have your own tasks outside this distribution,
    adapt *task_dir* to point to that. By default, *task_dir* points to the directory with example tasks
    that come with the distribution of the workbench.

.. _annox_dir:

*annox_dir*
    The directory in which your own extra annotation packages can be found.
    If you have your own annotations outside this distribution,
    adapt *annox_dir* to point to that. By default, *annox_dir* points to the directory with example annotation packages
    that come with the distribution of the workbench.

You probably do not need to change the other settings, since they are used for generating subdirectories under control of
the workbench.

Now you are set to run your tasks.
You might want to run an example task from the examples in the *tasks* directory
but they might fail because they refer to features that might not occur in your resource.
You can also write a task yourself and add it to the *tasks* directory. See :doc:`Writing Tasks <taskwriting>`.

Usage
-----
Go to the directory where *laf-fabric.py* resides::

    cd «path_to_dir_of_laf-fabric.py»

*single use mode*::

    python laf-fabric.py --source=«source» --annox=«annox» --task=«task» [--force-compile-source] [--force-compile-annox]

*to start the command interpreter mode*::

    python laf-fabric.py [--source=«source» ] [--annox=«annox»] [--task=«task» ] [--force-compile-source] [--force-compile-annox]

The workbench is a Python program that is invoked from the command line.

*interactive use mode*
    If some of the ``«source»``, ``«annox»`` and ``«task»`` arguments are missing or if the ``--menu`` argument is present
    it starts in interactive mode prompting you for sources and commands to run tasks.
    The ``«source»``, ``«annox»`` and ``«task»`` arguments are given are used for initial values.
    In interactive mode you can change your ``«source»``, ``«annox»`` and ``«task»`` selection, and run tasks.
    There is a help command and the prompt is self explanatory.

*single use mode*
    If both the ``«source»`` and ``«task»`` arguments are present and if the ``--menu`` argument is absent
    the workbench runs the specified task without asking and quits.

Other options
-------------
``--force-compile-source`` and ``--force-compile-annox``
    If you have changed the LAF resource or the selected annotation package, the workbench will detect it and recompile it.
    The detection is based on the modified dates of the GrAF header file and the compiled files.
    In cases where the workbench did not detect a change, but you need to recompile, use this flag.
    In interactive mode, there is a command to force recompilation of the current source.

Designed for Performance
========================
Since there is a generic LAF tool for smaller resources, this tool has been designed with performance in mind. 
In fact, performance has been the most important design criterion of all.
In this section the design decisions and particulars are listed.
There are also a few simplifications involved, see the section of GrAF :ref:`feature coverage` below.

There are several ideas involved in compiling a LAF resource into something that is compact, fast loadable, and amenable to efficient computing.

#. Replace everything by integers (nearly everything).
#. Store relationships between integers in *arrays*, that is, Python arrays.
#. Store relationships between integers and sets of integers also in *arrays*.
#. Keep individual features separate.

Explanation of these ideas
--------------------------
**Everything is integer**
In LAF the pieces of data are heavily connected, and the expression of the connections are XML identifiers.
Besides that, absolutely everything gets an identifier, whether or not those identifiers are targeted or not.
In the compiled version we get rid of all XML identifiers.
Everything that comes in great quantities will be represented by integers: regions, nodes, edges, feature values.
But feature names, annotation labels and annotation spaces will be kept as is.
For feature values we will create mapping tables and the end user will not see the codes but only the original values.

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
For example, in the WIVU data, we have the feature::

    shebanq:ft.suffix (node)

with annotation space ``shebanq``, annotation label ``ft``, feature name ``suffix``, and kind ``node``.
The data of this feature is a mapping of that assigns a string value to each of more than 400,000 nodes.
So this individual feature represents a significant chunk of data.

In order to reduce this chunk, the string values are kept in a table of unique values, and the mapping from node to value yields
the number of the value in the list of distinct values of that feature.

So every feature needs as its data a lookup table and a translation table for its values, and when a feature is active,
the inverse mapping is also needed.

The individual features together take up the bulk of the space.
In our example, they take 333 MB on disk, and the rest takes only 152 MB.
Most tasks require only a limited set of individual features.
So when we run tasks and switch between them, we want to swap feature data in
and out.
The design of the workbench is such that feature data is neatly chunked per individual feature.

.. note::
    Here is the reason that we do not have an overall table for feature values.
    We miss some compression here, but with a global feature value mapping, we would burden every task with a significant
    amount of memory. Moreover, when we are going to add the functionality of extra annotation packages, it would become 
    a nightmare to maintain the values of features.

.. note::
    Features coming from the source and features coming from the extra annotation package will be merged
    before the user can touch them in his tasks.
    This merging occurs late in the process, even after the loading of features by the workbench.
    Only when the tasks calls the API mappings, the features will be assembled into objects, where the source features
    and annox features finally get merged.
    When the task exits, the merged features get lost. 

Consequences
------------
The concrete XML identifiers present in the LAF resource are moved to the background. 
Only if your tasks ask for them explicitly, they can be loaded.
In that case you get mappings between the xml-identifiers and the internal integer codes
for nodes and for edges.
This requires considerable overhead.
     
Whoever designs a LAF resource to be worked on by this workbench,
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
So an annotation space and a label uniquely define a kind of annotation.
In a previous version, this workbench ignored annotation spaces altogether.
Now annotation spaces are fully functional.

*feature structures*
    The content of an annotation can be a feature structure.
    A feature structure is a set of features and sub features, ordered again as a graph.
    This workbench can deal with feature structures that are merely sets of key-value pairs.
    The graph-like model of features and subfeatures is not supported.
*annotations*
    Even annotations get lost. The workbench is primarily interested in features and values.
    It forgets the annotations in which they have been packaged except for: 
    * the annotation space,
    * the annotation label,
    * the target of the annotation (node or edge)
*dependencies*
    In LAF one can specify the dependencies of the files containing regions, nodes, edges and/or annotations.
    The workbench assumes that all dependent files are present in the resource.
    Hence the workbench reads all files mentioned in the GrAF header, in the order stated in the GrAF header file.
    This should be an order in which regions appear before the nodes that link to them,
    nodes before the edges that connect them, and nodes and edges before the annotations that target them.

Development
===========

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

Now Python does not have strict encapsulation of data structures,
so by just inspecting the classes and objects you can reach out
for all aspects of the LAF data that went into the compiled data.
See the GrAF :ref:`feature coverage` for a specification of what data ends up in the compilation.

