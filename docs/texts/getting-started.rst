Getting Started
###############

About
=====
*LAF-Fabric* is a `github project <https://github.com/ETCBC/laf-fabric>`_
in which there are Python packages called *laf and *etcbc*.
You must install them as packages in your current python installation.
This can be done in the standard pythonic way,
and the precise instructions will be spelled out below.

Platforms
=========
LAF-Fabric is being developed on **Mac OSX** Mavericks on a Macbook Air with 8 GB RAM.
It is being used on a **Linux** virtual machine running on a laptop of respectable age,
and it runs straight under **Windows** as well, except for some testing/debugging functionality.

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

#. On Windows you could get into trouble if you have another Python.
   If you have environment variables with the name of PYTHONPATH or PYTHONHOME, you should disable
   them. For diagnosis and remedy, see [#otherpython]_ 

#. Start up a new command prompt, and say::

       conda install anaconda
    
   This will install all anaconda packages in your fresh python3 installation.
   Now you have *ipython*, *networkx*, *matplotlib*, *numpy* to name but a few popular
   python packages for scientific computing.
 
Get LAF-Fabric
==============
If you have git you can just clone it from github on the command line::

    cd «directory of your choice»
    git clone https://github.com/ETCBC/laf-fabric

If you do not have git, consider getting it from `github <https://github.com>`_.
It makes updating your LAF-Fabric easier later on.

Nevertheless, you can also download the latest version from
`github/laf-fabric <https://github.com/ETCBC/laf-fabric>`_.
Unpack this somewhere on your file system. Change the name from *laf-fabric-master* to *laf-fabric*.
In a command prompt, navigate to this directory.

Install LAF-Fabric
==================
Preparation: you have to unpack a ``tar.gz`` file. On Windows you may have to install a tool for that,
such as `7-zip <http://www.7-zip.org>`_.

Here are the steps, assuming you are in the command line, at the top level directory in *laf-fabric*::

    cd dist
    tar xvf laf-*
    cd laf-*
    python setup.py install

This installs the generic laf processor *laf* and the more specific ETCBC tools to work with the
Hebrew Text Database: *etcbc*.

Get the data
============
If you are interested in working with the Hebrew Bible,
go to the `ETCBC github repository <https://github.com/ETCBC/laf-fabric-nbs>`_.
You find a download link for a ready made work directory containing the binary LAF data of the ETCBC Hebrew Text database.
(You need to ask for a password, though, to unlock the zip file).
Download and unpack it in your home directory. If all goes well you have a directory
*laf-fabric-data* in your home directory.

.. caution::
    If you have already a *laf-fabric-data* directory, unpack the download somewhere else,
    and copy over the relevant subdirectories to your own. In that way you do not loose your work.

Test and run LAF-Fabric
=======================
In the top-level directory of LAF-Fabric there is a gallery script.
If you run it, you will also configure your LAF-Fabric::

    python lf-gallery.py tinys

This points laf-fabric to the example data that comes with the distribution, which is just Genesis 1:1.
If you have downloaded the binary data for the full Hebrew Text Database, then
make sure the data is in *~/laf-fabric-data/etcbc-bhs3* and run::

    python lf-gallery.py fulls

After this you have a default config file *~/laf-fabric-data/laf-fabric.cfg* and you can use
laf-fabric scripts from anywhere on your system, also in notebooks.

On all platforms (Windows users: use Firefox or Chrome as your browser, not Internet Explorer),
you can also run notebooks with LAF-Fabric:: 

    cd examples
    ipython notebook

This starts a python process that communicates with a browser tab, which will pop up in front of you.
This is your dashboard of notebooks.
You can pick an existing notebook to work with, or create a new one.
It is recommended that you write your own notebooks in a separate directory, not under the LAF-Fabric installation.
In that way you can apply updates easily without overwriting your work.

#. Create a notebook directory somewhere in your system and navigate there in a command prompt.
#. Then::

    ipython notebook

.. note::
    If you create a notebook that you are proud of, it would be nice to include it in the example
    notebooks of LAF-Fabric or in the `ETCBC notebooks <https://github.com/ETCBC/contributions>`_.
    If you want to share your notebook this way, mail it to `me <mailto:dirk.roorda@dans.knaw.nl>`_.

More configuration for LAF-Fabric
=================================
If you need the data to be at another location, you must modify the *laf-fabric.cfg*.
This configuration file *laf-fabric.cfg* is searched for in the directory of your script, or in a standard
directory, which is *laf-fabric-data* in your home directory.

There are just one or two settings.

    [locations]
    work_dir  = /Users/you/laf-data-dir/etcbc-bhs3
    laf_dir  = /Users/you/laf-data-dir/etcbc-bhs3
    
*work_dir* is folder where all the data is, input, intermediate, and output.

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

    Genesis 1	22.9	5.2
    Genesis 2	19.2	6.48
    Genesis 3	20.6	9.02
    Genesis 4	32	11
    Genesis 5	36.6	17.9
    Genesis 6	22.7	8.7
    Genesis 7	18.8	10.7
    Genesis 8	16.7	8.94
    Genesis 9	19.9	6.76
    Genesis 10	22	4.45

From this table we can easily make a chart, within the same notebook!

.. image:: /files/gender.png

.. note::
    If you click on the notebook link above, you are taken to the public `notebook viewer website <http://nbviewer.ipython.org>`_,
    which shows static versions of notebooks without storing them.
    In order to run them, you need to download them to your computer.

The gender notebook is self documenting, it contains general information on how to do data analysis with LAF-Fabric.

Next steps
----------
Have a look at the notebooks in the
`ETCBC <https://github.com/ETCBC/laf-fabric-nbs>`_ and
`study <https://github.com/ETCBC/study>`_ and
`contributions <https://github.com/ETCBC/contributions>`_
repositories.
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

   After these operations, quit all your command prompts, start a new one, and say ``python --version``.
   You should see something with 3.3 and Anaconda in the answer.

