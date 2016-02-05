Getting Started
###############

About
=====
*LAF-Fabric* is a `github project <https://github.com/ETCBC/laf-fabric>`_
in which there are Python packages called *laf* and *etcbc* and *emdros2laf*.
You must install them as packages in your current python installation.
This can be done in the standard pythonic way,
and the precise instructions will be spelled out below.

Platforms
=========
LAF-Fabric is being developed on **Mac OSX** on a Macbook Air with 8 GB RAM from 2012.
It is being used on a **Linux** virtual machine running on a laptop of respectable age,
and it runs straight under **Windows** as well, except for some testing/debugging functionality.

On a Virtual Machine (just a few steps)
=======================================
The easiest way to get started with LAF-Fabric and the data for the Hebrew Bible is using Oliver Glanz's Virtual Machine.
Go to his `OneDrive <http://1drv.ms/1QiCJ6N>`_ and download the file
*ETCBC-vm_v1.5_lubuntu14.04-32bit.ova*. This is a so-called vm-appliance file, which you will need to open with the program
`VirtualBox <http://virtualbox.org/>`_,
which you have to download and install.
Detailed instructions are in *running and preparing an ETCBC vm_v1.5.pdf*.

When all went well, you can continue with **Writing Notebooks** below.

On your own machine (many steps)
================================
You can also run LAF-Fabric on your own machine directly.
It takes more steps, and the steps are more dependent on the platform of your machine (Linux, Mac OSX, or Windows) and what is there already present.
It involves setting up the Python machinery, getting the data and some example notebooks.

Your python setup
-----------------
First of all, make sure that you have the right Python installation.
You need a python3 installation with numerous scientific packages.
Below is the easiest way to get up and running with python.
You can also use it if you have already a python, but in a different version and without some
necessary modules.
The following setup ensures that it will not interfere with existing python installations
and it will get you all modules in one go.

Getting to know Jupyter, formerly known as IPython
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The following step may take a while, so in the meantime you can familiarize yourself with
Jupyter, if you like.
If the concept of an IPython notebook is new to you, start with 
`IPython documentation <http://ipython.org/ipython-doc/3/notebook/notebook.html>`_.
`Jupyter <http://jupyter.org>`_
is a more generic tool by which you can also other programming languages,
such as `R <https://www.r-project.org>`_ in notebooks.

Download Anaconda
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
`Anaconda <https://store.continuum.io/cshop/anaconda/>`_ is our distribution of choice.
Download the free version for your platform, make sure that you choose version based on Python 3.x,
and let the installer do its work.

#. Pick the one that fits your operating system.
   Install it. If asked to install for single user or all users, choose single user.

#. On Windows you could get into trouble if you have another Python.
   If you have environment variables with the name of PYTHONPATH or PYTHONHOME, you should disable
   them. For diagnosis and remedy, see [#otherpython]_ 

This will install all anaconda packages in your fresh python3 installation.
Now you have *ipython*, *networkx*, *matplotlib*, *numpy* to name but a few popular
python packages for scientific computing.

It is convenient to upgrade Jupyter before you start working.
On the command line, say::

    conda update jupyter
 
Get LAF-Fabric
--------------------

LAF-Fabric is on the `Python Package Index <https://pypi.python.org/pypi/laf-fabric/4.5.8>`,
so you can just say::

    pip install laf-fabric

This installs the generic laf processor *laf* and the more specific ETCBC tools to work with the
Hebrew Text Database: *etcbc*.
It also installs *emdros2laf*, a conversion package from the source format of the
`ETCBC database <http://www.persistent-identifier.nl/?identifier=urn%3Anbn%3Anl%3Aui%3A13-048i-71>`_ (EMDROS) to LAF.
This package has been used to obtain the actual LAF version of the ETCBC database.

.. note::
    For advanced users only: 
    In order to use *emdros2laf* and parts of *etcbc*, you need to install `EMDROS <http://emdros.org>`_ software, which is freely available.
    Tip: it works nicely with an sqlite3 backend.
    You only need this when you want to run MQL queries (the same queries you can design and store in SHEBANQ) from withing your programs.

If you want to have the source code and examples you can get them from github.

If you have git you can just clone it from github on the command line::

    cd «directory of your choice»
    git clone https://github.com/ETCBC/laf-fabric

If you do not have git, consider getting it from `github <https://github.com>`_.

Nevertheless, you can also download the latest version from
`github/laf-fabric <https://github.com/ETCBC/laf-fabric>`_.
Unpack this somewhere on your file system. Change the name from *laf-fabric-master* to *laf-fabric*.
In a command prompt, navigate to this directory.

Get the data
--------------------
If you are interested in working with the Hebrew Bible,
go to the github repo
`laf-fabric-data <https://github.com/ETCBC/laf-fabric-data>`_
and consult its README.
Read the license and follow the instructions.
If all goes well you have a directory *laf-fabric-data* in your home directory.

Test and run LAF-Fabric
------------------------
Download as an example the `gender.ipynb <https://github.com/ETCBC/laf-fabric/blob/master/examples/gender.ipynb>`_
and put it in a directory, say `Downloads`.
Go to this directory and say on the command line::

    jupyter notebook

This starts a python process that communicates with a browser tab, which will pop up in front of you.
This is your dashboard of notebooks.
You can see the `gender.ipynb` notebook.
Click on it to open it, and run the cells by pressing Shift-Enter in each successive cell.
The notebook should execute without errors.

.. note::
    If you create a notebook that you are proud of, it would be nice to include it in the example
    notebooks of LAF-Fabric or in the `ETCBC notebooks <https://github.com/ETCBC/contributions>`_.
    If you want to share your notebook this way, mail it to `shebanq@ancient-data.org <mailto:shebanq@ancient-data.org>`_.

More configuration for LAF-Fabric
---------------------------------------
If you need the data to be at another location, you must modify the *laf-fabric.cfg*.
This configuration file *laf-fabric.cfg* is searched for in the directory of your script, or in a standard
directory, which is *laf-fabric-data* in your home directory.

There are just a few settings::

    [locations]
    data_dir  = ~/laf-data-dir
    laf_dir  = ~/laf-data-dir
    output_dir  = ~/output-data-dir
    
*data_dir* is folder where all the input data is.

*output_dir* is folder where all the output data is, the stuff that your tasks create.

*laf_dir* is the folder where the original laf-xml data is.
It is *optional*. LAF-Fabric can work without it.

Alternatively, you can override the config files by specifying the locations in your scripts.
Those scripts are not very portable, of course.

Writing notebooks
=================

Tutorial
--------
Here is a quick tutorial/example how to write LAF analytic tasks in an IPython notebook.

Our target LAF resource is the Hebrew text data base (see :ref:`data`).
Some nodes are annotated as words, and some nodes as chapters.
Words in Hebrew are either masculine, or feminine, or unknown.
The names of chapters and the genders of words are coded as features inside annotations to the
nodes that represent words and chapters.

We want to plot the percentage of masculine and feminine words per chapter.

With the example notebook `gender <http://nbviewer.ipython.org/github/ETCBC/laf-fabric/blob/master/examples/gender.ipynb>`_
we can count all words in the Hebrew bible and produce
a table, where each row consists of the bible book plus chapter, followed
by the percentage masculine words, followed by the percentage of feminine words in that chapter::

    Genesis 1,42.34769687964339,5.794947994056463
    Genesis 2,38.663967611336034,7.6923076923076925
    Genesis 3,37.4749498997996,10.02004008016032
    Genesis 4,43.04635761589404,11.920529801324504
    Genesis 5,40.74844074844075,18.91891891891892
    Genesis 6,36.61327231121282,9.610983981693364
    Genesis 7,33.59683794466403,11.462450592885375
    Genesis 8,31.30081300813008,9.959349593495935
    Genesis 9,37.97216699801193,9.74155069582505
    Genesis 10,30.679156908665107,4.68384074941452

From this table we can easily make a chart, within the same notebook!

.. image:: /files/gender.png

.. note::
    If you click on the notebook link above, you are taken to the public `notebook viewer website <http://nbviewer.ipython.org>`_,
    which shows static versions of notebooks without storing them.
    In order to run them, you need to download them to your computer.

The gender notebook is self documenting, it contains general information on how to do data analysis with LAF-Fabric.

Next steps
----------
Study the many `ETCBC4 features <http://shebanq-doc.readthedocs.org/en/latest/texts/welcome.html>`_.

Then have a look at the notebooks at the following locations

* `SHEBANQ tools <https://shebanq.ancient-data.org/tools/>`_ (notebooks that create data for usage in SHEBANQ, and are linked to research)
* `laf-fabric-nbs <https://github.com/ETCBC/laf-fabric-nbs>`_ (work in progress, often leading to SHEBANQ tools. Unpolished)
* `contributions <https://github.com/ETCBC/contributions>`_ (contributions by others)

You find notebooks by which you can study the rich feature set in the ETCBC data and notebooks that help you to add
your own annotations to the data. These notebooks require the additional *etcbc* package, which comes
with LAF-Fabric.


.. rubric:: Footnotes
.. [#otherpython] To check whether you have environment variables called PYTHONPATH or PYTHONHOME,
   go to a command prompt and say 

   ``echo %PYTHONPATH%``

   ``echo %PYTHONHOME%``
   
   If the system responds with the exact text you typed, there is nothing to worry about.
   Otherwise, you should rename these variables to something like ``NO_PYTHONPATH`` or
   ``NO_PYTHONHOME``.

   You can do that through: Configuration (Classical View) => System => Advanced Settings => button Environment Variables.

   If you have a reference to an other python in your ``PATH`` (check by ``echo %PATH%``) then you should remove it.

   After these operations, quit all your command prompts, start a new one, and say ``python3 --version``.
   You should see something with 3.3 and Anaconda in the answer.

