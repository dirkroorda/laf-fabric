LAF workbench
=============

What is this workbench?
-----------------------
This workbench is a pure Python tool for running Python scripts with access to the information in a LAF resource.
It has two major components:

#. a LAF compiler for transforming a LAF resource into binary data that loads very fast by Python
#. an execution environment that gives Python scripts access to LAF data and optimalization features

The selling point of the workbench is performance, both in terms of speed and memory usage.
The second goal is to make it really easy for users to write analytic tasks straightforwardly in terms of LAF concepts
without bothering about performance.

The typical workflow is:

#. install a LAF resource somewhere on the filesystem. A LAF resource is a directory with a primary data file, annotation files and header files.
#. install the LAF workbench package somewhere on a computing system.
#. in a configuration file, adapt the locations of the LAF directory and a work/results directory
#. write your own script, and put it in the right directory
#. run the workbench by invoking the calling script

The workbench provides you with a prompt, after which you can select among the available data sources and tasks.
You can run your selection, modify the selection, run it again, ad libitum. During this session loading and unloading of data will be done
only when it is really needed. So I you have to debug a script, you can do so without irritating waits for loading data all the time.

The first time a source is used, the LAF resource will be compiled. This may take considerable time, say 10 minutes for a 2 GB resource on a Macbook Air (2012).
All subsequent times the compiled data will be loaded directly, which takes, in the same setting, 5 to 10 seconds.
But loading will only occur the first time when you execute a task in a session after switching to it.

After loading the data, the workbench invokes your script.
You must declare the LAF-features that you use in your script, and the workbench will load data for them.

How to use the workbench?
-------------------------
Here are detailed instructions for installing, configuring and using the workbench.

Installation
^^^^^^^^^^^^
This package is called *graf* and is a Python package without extension modules.
I did not use the Python distutils to create a distribution that you can incorporate in your local Python installation.
You can just clone it fron github and work with it right away::

	cd «directory of your choice»
	git clone https://github.com/dirkroorda/laf-fabric

You get a directory *laf-fabric* with the following inside:

* *graf*: the workbench itself, a Python package
* *laf-fabric.py*: a script to call the workbench
* *tasks*: a directory with example tasks.

Before running the workbench, the calling script has to be configured.

Configuration
^^^^^^^^^^^^^
The configuration file script is *laf-fabric.cfg*.
In it is a configuration section::

    [locations]                                     ; paths in the file system
    data_root: /Users/dirk/Scratch/shebanq/results  ; working directory
    laf_source: laf                                 ; subdirectory for the LAF data
    compiled_source: db                             ; subdirectory for task results
    bin_dir: bin                                    ; subdirectory of specific tasks

    [source_choices]                                ; several GrAF header files
    tiny: bhs3.txt-tiny.hdr
    test: bhs3.txt-bhstext.hdr
    total: bhs3.txt.hdr

* *data_root*: point to the folder containing your LAF directory.
* *laf_source*: change into the directory name of your LAF directory.
* *compiled source*: this directory will be created.
* *source_choices*: read on ...

Normally, a LAF resource has a *LAF-header file* and a *primary data header file*, aka. *the GrAF header file*. The workbench needs to look at a *GrAF header file*.
This header file has references to all files that make up the resource. You might want to restrict the workbench to only part of the annotation files in the resource, e.g. if there are big annotation files that do not contain features that are relevant for your analysis. In that case, you can copy the original GrAF header file, and leave out all references to files that you do not want to take into consideration. The *source_choices* dictionary must contain all GrAF header files that you want to choose from.

Now you are set to run your tasks. You might want to run an example task from the examples in the *tasks* directory, but they might fail because they refer to features that might not occur in your resource. You can also write a task yourself and add it to the *tasks* directory. See :doc:`Writing Tasks <taskwriting>`.

Usage
^^^^^
The workbench is a Python program that is invoked from the command line.
It prompts you for tasks and source and commands to run tasks or quit.

Go to the directory where *laf-fabric.py* resides::

	cd «path_to_dir_of_laf-fabric.py»

	python laf-fabric.py 

Other options
^^^^^^^^^^^^^
``--force-compile``
	If you have changed the LAF resource, the workbench will detect it and recompile it. The detection is based on the modified dates of the GrAF header file and the compiled files. In cases where the workbench did not detect a change, but you need to recompile, use this flag.

Designed for Performance
------------------------
Since there is a generic LAF tool for smaller resources, this tool has been designed with performance in mind. 
In fact, performance has been the most important design criterion of all. In this section the decision and particulars are listed. There are also a few simplifications involved, see the section of *GrAF feature coverage* below.

There are several ideas involved in compiling a LAF resource into something that is compact, fast loadable, and amenable to efficient computing.

#. Replace everything by integers (nearly everything)
#. Store relationships between integers in *arrays*, that is, Python arrays
#. Store relationships between integers and sets of integers also in *arrays*.

Explanation of these ideas
^^^^^^^^^^^^^^^^^^^^^^^^^^
**Everything is integer**
In LAF the pieces of data are heavily connected, and the expression of the connections are XML identifiers.
Besides that, absolutely everything gets an identifier, whether or not those identifiers are targeted or not.
In the compiled version we get rid of all identifiers.
Everything: regions, nodes, edges, features, feature names, feature values, annotation labels will end up in an array,
and hence can be identified by its numerical index in that array.
For the only things that are essentially not integers (feature names, feature values, annotation labels) we will create mapping tables.

**Relationships between integers as Python arrays**
In Python, an array is a C-like structure of memory slots of fixed size. You do not have arrays of arrays, nor arrays with mixed types. This makes array handling very efficient, especially loading data from disk and saving it to disk. Moreover, the amount of space in memory needed is like in C, without the overhead a scripting language usually adds to its data types.

There is an other advantage:
a mapping normally consists of two columns of numbers, and numbers in the left column map to numbers in the right column.
In the case of arrays of integers, we can leave out the left column: it is the array index, and does not have to be stored.

**Relationships between integers as Python arrays**
If we want to map numbers to sets of numbers, we need to be more tricky, because we cannot store sets of numbers as integers. What we do instead is: we build two arrays, the first array points to data records in the second array. A data record in the second array consists of a number giving the length of the record, followed by that number of integers. The function :func:`arrayify() <graf.model.arrayify>` takes a list of items and turns it in a double array. 

Consequences
^^^^^^^^^^^^
The concrete XML identifiers present in the LAF resource get lost. Whoever designs a LAF resource to be worked on by this workbench, should not rely on the values of the XML identifiers to derive implicit meanings from. I did that in initial stages, producing identifiers ``n_1, n_2, e_1, e_2`` etcetera for node 1, 2 and edge 1, 2. Don't do that!

GrAF feature coverage
---------------------
This tool cannot deal with LAF resources in their full generality.

In LAF, annotations have labels, and annotations are organized in annotation spaces. So an annotation space and a label uniquely define a kind of annotation. The content of an annotation can be a feature structure. A feature structure is a set of features and sub features, ordered again as a graph.
These are the main simplifications:
	
*annotation spaces*
	The workbench ignores annotation spaces altogether. So annotations are only grouped by annotation labels.

*feature structures*
	This workbench can deal with feature structures that are merely sets of key-value pairs. The graph-like model of features and subfeatures is not supported.

*annotations*
	Even annotations get lost. The workbench is primarily interested in features and values. It forgets the annotations in which they have been packaged except for: 
	* the annotation label,
	* the target of the annotation (node or edge)
	So in order to retrieve a feature value, one must specify an annotation label, a feature name, and a node or edge to which the annotation containing the feature had been attached.

*dependencies*
	In LAF one can specify the dependencies of the files containing regions, nodes, edges and/or annotations. The workbench assumes that all dependent files are present in the resource. Hence the workbench reads all files mentioned in the GrAF header, in no particular order.
 

Development
-----------

API completion
^^^^^^^^^^^^^^
Many reasonable candidates for an API have not yet been implemented. Basically we have only:

*node iterator*
	iterator that produces nodes in the order by which they are anchored to the primary data (which are linearly ordered)

*feature lookup*
	a function that gives the value of a feature attached by some annotation to some edge or node

Now Python does not have strict encapsulation of data structures, so by just inspecting the classes and objects you can reach out for all aspects of the LAF data that went into the compiled data. See the GrAF feature coverage for a specification of what data ends up in the compilation.

