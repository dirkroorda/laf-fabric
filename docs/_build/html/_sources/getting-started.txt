Getting Started
###############

About
=====
*LAF-Fabric* is a `github project <https://github.com/dirkroorda/laf-fabric>`_
in which there is a Python package called :mod:`graf`.
It is a package without extension modules,
so it will run without installation from anywhere in your system.
In order to run it in notebook mode (recommended), you must
install it as a package in your current python installation.
This can be done in the standard pythonic way,
and the precise instructions will be spelled out below.

Platforms
=========
LAF-Fabric is being developed on **Mac OSX** Mavericks on a Macbook Air with 8 GB RAM.
It is being used on a **Linux** virtual machine running on a laptop of respectable age,
and it runs straight under **Windows** as well.

Your python setup
=================
First of all, make sure that you have the right Python installation.
You need a python3 installation with numerous scientific packages.
Below is the easiest way to get up and running with python.
You can also use it if you have already a python, but in the wrong versions and without some
necessary modules.
The following setup ensures that it will not interfere with existing python installations
and it will get you all modules in one go.

Getting to know interactive python
----------------------------------
The following step may take a while, so in the meantime you can familiarize yourself with
ipython, if you like. The `website <http://ipython.org>`_ is a good entry point.

Download Anaconda
-----------------
`Anaconda <https://store.continuum.io/cshop/anaconda/>`_ is our distribution of choice.
We want, however, base it on python3, so we have to take a detour.

#. Download a *miniconda* installer from `here <http://repo.continuum.io/miniconda/index.html>`_.
   Pick the one starting with *Miniconda3* that fits your operating system.
   Install it. If asked to install for single user or all users, choose single user.
#. Start up a new command prompt, and say::

       conda install anaconda
    
   This will install all anaconda packages in your fresh python3 installation.
   Now you have *ipython*, *networkx*, *mathplotlib*, *numpy* to name but a few popular
   python packages for scientific computing.
 
Get LAF-Fabric
==============
If you have git you can just clone it from github on the command line::

    cd «directory of your choice»
    git clone https://github.com/dirkroorda/laf-fabric

If you do not have git, consider getting it from `github <https://github.com>`_.
It makes updating your LAF-Fabric easier later on.

Nevertheless, you can also download the latest version from
`github/laf-fabric <https://github.com/dirkroorda/laf-fabric>`_.
Unpack this somewhere on your file system. Change the name from *laf-fabric-master* to *laf-fabric*.
In a command prompt, navigate to this directory.

Install LAF-Fabric
==================
Here are the steps, assuming you are in the command line, at the top level directory in *laf-fabric*::

    cd dist
    tar xvf graf-*
    cd graf-*
    python setup.py install

Configure LAF-Fabric
====================
The configuration file script is *laf-fabric.cfg* in the directory *notebooks*.
In it there is just one setting, and you have to adapt it to your local situation::

    [locations]
    work_dir  = /Users/dirk/Scratch/shebanq/results
    
.. _work_dir:

*work_dir*
    folder where all the data is, input, intermediate, output.

Get the data
============
If you have a LAF resource, create a subdirectory *laf* inside the *work_dir*, and put 
the files of the LAF resource there.

If you only have a compiled LAF resource, e.g. *bhs3.txt.hdr*, put it also
inside *work_dir*.

Run LAF-Fabric
==============
In the command prompt, go to the directory where *laf-fabric.py* resides::

    cd «path_to_dir_of_laf-fabric.py»

*notebook mode*, example notebooks::

    cd notebooks
    ipython notebook

This starts a python process that communicates with a browser tab, which will pop up in fron of you.
This is your dashboard of notebooks.
You can pick an existing notebook to work with, or create a new one.

*notebook mode*, your own notebooks

#. Create a notebook directory somewhere in your system and navigate there in a command prompt.
#. Copy your version of *laf-fabric.cfg* in the example notebooks directory to your own notebook directory.
#. Then::

    ipython notebook

.. note::
    If you create a notebook that you are proud of, it would be nice to include it in the example
    notebooks.
    If you want to share your notebook this way, mail it to `me <mailto:dirk.roorda@dans.knaw.nl>`_.

*workbench single use mode*::

    python laf-fabric.py --source=«source» --annox=«annox» --task=«task» [--force-compile-source] [--force-compile-annox]

If all of the ``«source»``, ``«annox»`` and ``«task»`` arguments are present and if the ``--menu`` argument is absent
LAF-fabric runs the specified task without asking and quits.

*workbench re-use mode*::

    python laf-fabric.py [--source=«source» ] [--annox=«annox»] [--task=«task» ] [--force-compile-source] [--force-compile-annox]

If some of the ``«source»``, ``«annox»`` and ``«task»`` arguments are missing or if the ``--menu`` argument is present
it starts in interactive mode prompting you for sources and commands to run tasks.
The ``«source»``, ``«annox»`` and ``«task»`` arguments that are given are used for initial values.
In interactive mode you can change your ``«source»``, ``«annox»`` and ``«task»`` selection, and run tasks.
There is a help command and the prompt is self explanatory.

Other options
-------------
``--force-compile-source`` and ``--force-compile-annox``
    If you have changed the LAF resource or the selected annotation package, LAF-fabric will detect it and recompile it.
    The detection is based on the modified dates of the GrAF header file and the compiled files.
    In cases where LAF-fabric did not detect a change, but you need to recompile, use this flag.
    In interactive mode, there is a command to force recompilation of the current source.

