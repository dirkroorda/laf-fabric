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

After loading the data, the workbench invokes your script. If your script runs too slow, there are various options to make it run quicker. You can declare the LAF-features that you use in your script, and the workbench will construct indexes for them, if they do not already exist. Indexing costs 30 to 60 seconds (still in the same setting), and the performance gain is typically 20 to 60 fold.

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

Designed for Performance
------------------------
Since there is a generic LAF tool for smaller resources, this tool has been designed with performance in mind. 
In fact, performance has been the most important design criterion of all.

GrAF feature coverage
---------------------
