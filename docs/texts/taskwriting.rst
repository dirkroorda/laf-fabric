Writing Tasks
#############

What is a task?
===============

A task is an ordinary Python script with some magical capabilities
for looking into a LAF resource (a *compiled* LAF resource to be precise).

There are two scenarios for executing tasks:

Notebook mode
-------------
In notebook mode you write your tasks in code cells in iPython notebooks.
There you have to import LAF-Fabric, or rather the *laf* module::

    import laf
    from laf.notebook import Notebook
    processor = Notebook()

Here is a list of current notebooks for LAF-fabric.

* `gender <http://nbviewer.ipython.org/github/dirkroorda/laf-fabric/blob/master/notebooks/gender.ipynb>`_
* `cooccurrences <http://nbviewer.ipython.org/github/dirkroorda/laf-fabric/blob/master/notebooks/cooccurrences.ipynb>`_

If you click on the link, you are taken to the public `notebook viewer website <http://nbviewer.ipython.org>`_,
which shows static versions of notebooks without storing them.
In order to run them, you need to download them to your computer.

Workbench mode
--------------
In workbench mode you place your tasks into the *tasks* directory.
In your script you have to define a function ``task(processor)`` that takes as its sole argument
an object that gives access to all the LAF data from your resource::

    def task(processor):
        '''this function executes your task'''

This scenario is handy if you have a bunch of tasks that you want to run in quick succession.

A leading example
=================
Our target LAF resource is the Hebrew text data base (see :ref:`data`).
Some nodes are annotated as words, and some nodes as chapters.
Words in Hebrew are either masculine, or feminine, or unknown.
We want to plot the percentage of masculine and feminine words per chapter.
The names of chapters and the genders of words are coded as features inside annotations to the
nodes that represent words and chapters.

More on features
================
The features we need are present in an annotation space named ``shebanq`` (after the project
that produced this LAF resource).
The chapter features are labeled with ``sft`` and the other features with ``ft``.

When LAF-Fabric compiles features into binary data, it forgets the annotations in which the features come,
but the annotation *space* and *label* are retained in a double prefix to the feature name.

LAF-Fabric remembers those features by their *fully qualified* names: ``shebanq:ft.gender``, ``shebanq:sft.chapter`` etc.
There may also be annotations without feature contents. Such annotations will be stored as features with as name the 
annotation label only, without the dot: ``shebanq:db``.

.. note::
    Annotations may reference nodes or edges.
    It is possible that nodes and edges have features with the same name. 
    However, LAF-Fabric maintains a strict distinction between features
    of nodes and features of edges. They have separate name spaces, implicitly.
    Features names that are used for nodes and edges may coexist, but their
    data are in separate tables.

The example task :mod:`gender` counts all words in the Hebrew bible and produces
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

Finally, here is the complete Python code of the task that produced this output::

    import sys

    load = {
        "xmlids": {
            "node": False,
            "edge": False,
        },
        "features": {
            "shebanq": {
                "node": [
                    "db.otype",
                    "ft.gender",
                    "sft.chapter,book",
                ],
                "edge": [
                ],
            },
        },
    }

    def task(processor):
        '''Counts the frequencies of words with male and female gender features.
        Outputs the frequencies in a tab-delimited file, with frequency values for
        each chapter in the whole Hebrew Bible.
        '''
        API = processor.API()
        F = API['F']
        NN = API['NN']

        stats_file = processor.add_output("stats.txt")

        stats = [0, 0, 0]
        cur_chapter = None
        ch = []
        m = []
        f = []

        for node in NN():
            otype = F.shebanq_db_otype.v(node)
            if otype == "word":
                stats[0] += 1
                if F.shebanq_ft_gender.v(node) == "masculine":
                    stats[1] += 1
                elif F.shebanq_ft_gender.v(node) == "feminine":
                    stats[2] += 1
            elif otype == "chapter":
                if cur_chapter != None:
                    masc = 0 if not stats[0] else 100 * float(stats[1]) / stats[0]
                    fem = 0 if not stats[0] else 100 * float(stats[2]) / stats[0]
                    ch.append(cur_chapter)
                    m.append(masc)
                    f.append(fem)
                    stats_file.write("{}\t{:.3g}\t{:.3g}\n".format(cur_chapter, masc, fem))
                this_chapter = "{} {}".format(F.shebanq_sft_book.v(node), F.shebanq_sft_chapter.v(node))
                sys.stderr.write("\r{:<15}".format(this_chapter))
                stats = [0, 0, 0]
                cur_chapter = this_chapter

Interactive execution
=====================
It is more fun to work with tasks interactively.
See :doc:`getting-started` how to set it up.

In interactive mode, the data remains in memory after the task has completed.
You can then load additional packages and add pieces of python code
to do fancy things with your data, such as plotting graphs.

When your task has finished, put this into a cell::

    processor.final()

This will close all output and input files, and show you
the location of those files plus a listing of them, complete
with sizes and modification times.

If you want to work with those files in following code cells,
you can get their location into a python variable, say *table_file*, as follows::

    table_file = processor.my_files(«filename»)

LAF-Fabric does not check whether ``«filename»`` exists, it just
prepends the directory name to ``/«filename»``.

Information flow from task to LAF-Fabric
========================================
The main thing LAF-Fabric needs to know about your task is a declaration of
what data the task will use.
The task needs to tell whether to load the primary data (with the region information),
which feature data should be loaded and whether XML identifier tables
should be loaded.
Some of these must be specified separately for nodes and edges.

The feature specification takes the form a dictionary, keyed by annotation spaces first
and then by kind (node or edge). Under those keys the declaration proceeds
with a list of lines specifying bunches of features as follows::

    «annotation label».«feature names»

where ``«feature names»`` is a comma separated list of feature names without annotation labels.
For all implied features ``«annotation space»:«annotion label».«feature name»`` of the chosen kind (node or edge),
data will be loaded.
For all other features data will be unloaded, if still loaded.

.. caution:: Missing feature data.

    If you forget to mention a feature in the load declaration and you
    do use it in your task,
    LAF-Fabric will stop your task and shout error messages at you.
    If you declare features that do not exist in the LAF data, you just get
    a warning. But if you try to use such features, you get also a loud error.

Information flow from LAF-Fabric to task
========================================
LAF-Fabric will call the function *task(object)* in your task script (assuming you follow workbench mode),
and the thing it hands over to it as *object* is an object of
class :class:`LafTask <laf.task.LafTask>`.
By using this object, you have to access all of its methods. 

In notebook this handing over occurs when you say::

    processor = Notebook()

In order to write an efficient task,
it is convenient to import the names of the API methods as *local variables* of the *task* function.
The lookup of names in Python is fastest for local names.
And it makes the code much cleaner.

The method :meth:`API() <laf.task.LafTask.API>` delivers the methods,
and it is up to you to give them names.
It is recommended to stick to the names provided here in this example.
Here is a short description of the corresponding methods.
See :doc`API-reference` for full documentation of the API.

Here is just a very short description:

*F*
    **Features**: All information stored in features

*C*
    **Connectivity**: How to get from one node to another via edges

*P*
    **Primary Data**: Get chunks of primary data that belong to a node

*N*
    **NextNode**: walk through a selected set of nodes (not via edges)

*X*
    **XML identifiers**: retrieve the original XML identifiers as they appear in the LAF resource on nodes and edges

*msg*
    **message**: issue timed messages to console (standard error) and log file

Input and Output
================
You can create an output filehandle, open for writing, by calling the
method :meth:`add_output() <laf.task.LafTask.add_output>`
and assigning the result to a variable, say *out* ::

    out = processor.add_output("output.txt")

From then on you can write output simply by saying::

    out.write(text)

You can create as many output handles as you like in this way.
All these files and up in the task specific working directory.

Likewise, you can place additional input files in that directory,
and read them by saying::

    inp = processor.add_input("input.txt")
    inp.read(text)

Once your task has finished, LAF-Fabric will close them all.

Node order
==========
There is an implicit partial order on nodes.
The short story is: the nodes that are linked to primary data, inherit the order that is present
in the primary data.
The long story is a bit more complicated, since nodes may be attached to multiple ranges of 
primary data.

See :ref:`node-order` for details. If you don't, it might be enough to know
that *embedding* nodes always come before *embedded* nodes, meaning that if a node happens 
to be attached to a big piece of primary data, and a second node to a part of that data,
then the node with the bigger attachment comes first.

When there is no inclusion either way, and the start and end points are the same, the order is left undefined. 

Linking to the LAF resource
===========================
As a consequence of LAF-Fabric's efficient implementation of the data in a LAF resource,
the concrete XML identifiers present in the LAF resource have been replaced by integers.
For normal operations this is noproblem whatsoever.

But when you want to add new annotations to your LAF resource, you eventually need the
original XML identifiers in order to specify the nodes or edges they point to.

In that case you can ask LAF-Fabric to load mappings
between the xml-identifiers and the internal integer codes for nodes and for edges.
This requires considerable overhead.
     
Whoever designs a LAF resource to be worked on by LAF-fabric,
should not rely on XML identifiers with an ad-hoc syntax with implicit meaning.
For example, if you use identifiers ``n_1, n_2, e_1, e_2`` for node 1, 2 and edge 1, 2,
there is nothing wrong with that.
But it is not recommended that in your tasks you split those identifiers up in order to 
see whether it denotes a node or an edge.
