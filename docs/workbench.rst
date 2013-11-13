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
#. configure a calling script with the locations of the LAF directory and a work/results directory
#. write your own script, and put it where the workbench can see it
#. run the workbench by invoking the calling script

The first time the workbench is used, the LAF resource will be compiled. This may take considerable time, say 10 minutes for a 2 GB resource on a Macbook Air (2012).
All subsequent times the compiled data will be loaded directly, which takes, in the same setting, 5 to 10 seconds.

After loading the data, the workbench invokes your script. If your script runs too slow, there are various options to make it run quicker. You can declare the LAF-features that you use in your script, and the workbench will construct indexes for them, if they do not already exist. Indexing costs 30 to 60 seconds (still in the same setting), and the performance gain is typically 20 to 60 fold. There are several *optimization flavours*, but the one that builds indexes is the only one that actually manages to increase the performance.

How to use the workbench?
-------------------------
Here are detailed instructions for installing, configuring and using the workbench.

Installation
^^^^^^^^^^^^
This package is called *graf* and is a pure Python package. A recommended way of installing it is to download *graf-version.tar.gz* from the distribution directory on  `Github <https://github.com/dirkroorda/laf-fabric/tree/master/dist>`_ and unpack it in a directory of your choice. You get a directory with documentation, the package *graf*, a calling script *laf-fabric.py* and a directory *tasks* with example tasks. Either you run *setup.py* to install this package in your local Python tree, or you leave the package where you unpacked it. Here are the directions if you do the latter.

Configuration
^^^^^^^^^^^^^
The calling script is *laf-fabric.py*. In it is a configuration section between::

	## CONFIG START

and::

	## CONFIG END.

The things to change here are:

``data_root``
	Path to the directory containing the LAF resource. 

``laf_source``
	The directory name of the LAF resource.

``compiled source``
	The directory name of the compiled resource. This directory will be created next to the ``laf_source`` directory.

``source_choices``
	A dictionaries with abbreviations for the names of the header files within the LAF resource that the workbench can refer to.

Normally, a LAF resource has a *LAF-header file* and a *primary data header file*, aka. *the GrAF header file*. The workbench needs to look at a GrAF header file.
This header file has references to all files that make up the resource. You might want to restrict the workbench to only part of the annotation files in the resource, e.g. if there are big annotation files that do not contain features that are relevant for your analysis. In that case, you can copy the original GrAF header file, and leave out all references to files that you do not want to take into consideration. The ``source_choices`` dictionary must contain all GrAF header files that you want to choose from on the command line. There will be an option ``--source=key`` to select the header file that you want to point the workbench to.

Now you are set to run your tasks. You might want to run an example task from the examples in the *tasks* directory, but they might fail because they refer to features that might not occur in your resource. You can also write a task yourself and add it to the *tasks* directory.

Usage
^^^^^
The workbench is a Python program that is invoked from the command line. It loads data, runs a task script, and then exits. Between invocations the workbench is not loaded in memory and does not eat CPU cycles.

For every single task execution you invoke the workbench by its calling script *laf-fabric.py*, supplying parameters for selecting the LAF source, the task and the optimization flavour. And there are miscellaneous options, of course. 

Go to the directory where *laf-fabric.py* resides::

	cd «path_to_dir_of_laf-fabric.py»

Then issue the following command, where ``«string»`` stands for variable text that you should provide, and material within ``[ ]`` is optional::

	python laf-fabric.py --source=«source» --optim=«flavour» --task=«task» [--force-compile] [--force-index]

Explanation

``«source»``
	the key for the GrAF header file that you use to point to your LAF resource
``«task»``
	the task that you want to execute. Must be a python script in the *tasks* directory
``«flavour»``
	the flavour of the optimization that you want to apply. Choices are:

	``plain``
		no optimization at all. Due to the extreme packing of feature information in very simple, C-like datastructures, feature lookup is expensive. By not optimizing you pay for that.
	``assemble``
		read the feature declarations of the task at hand, and ensure that indexes exist for those features. Create and save them if they do not exist, load them when they do exist.
	``assemble-all``
		create all possible indexes. This takes a few minutes, but takes a fair amount of space, both on disk and in memory. At present there is no provision to save the index. It is recommended to use ``assemble-all``. The index is shared between tasks on the same «source», so the indexes will be built gradually on demand and not exceed what is really needed. After a while there will be little need for new tasks to create new indexes.
	``memo``
		feature values will be cached. Before feature lookup a value will be retrieved from the cache if possible. Otherwise the feature value will be looked up and stored in the cache. It turns out not to be very efficient, because in many tasks feature values are only needed once. So there is overhead for caching and no gain. Moreover, they cache may easily take up an enormous amount of space. 

``--force-compile``
	If you have changed the LAF resource, the workbench will detect it and recompile it. The detection is based on the modified dates of the GrAF header file and the compiled files. In cases where the workbench did not detect a change, but you need to recompile, use this flag.

``--force-index``
	Only relevant for the ``assemble`` flavour. If indexes are outdated without the system detecting it, you can force re-indexing by giving this flag.


Designed for Performance
------------------------
Since there is a generic LAF tool for smaller resources, this tool has been designed with performance in mind. 
In fact, performance has been the most important design criterion of all. In this section the decision and particulars are listed.

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
Many reasonable candidates for an API have not yet been implemented. Basically we have only:

*node iterator*
	iterator that produces nodes in the order by which they are anchored to the primary data (which are linearly ordered)

*feature lookup*
	a function that gives the value of a feature attached by some annotation to some edge or node

Now Python does not have strict encapsulation of data structures, so by just inspecting the classes and objects you can reach out for all aspects of the LAF data that went into the compiled data. See the GrAF feature coverage for a specification of what data ends up in the compilation.
