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

Designed for Performance
------------------------
Since there is a generic LAF tool for smaller resources, this tool has been designed with performance in mind. 
In fact, performance has been the most important design criterion of all.

GrAF feature coverage
---------------------
