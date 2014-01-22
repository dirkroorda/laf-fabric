API Reference
#############

Parts of the API
================
The API deals with several aspects of task processing.
First of all, getting information out of the LAF resource.
But there are also methods for writing to and reading from task-related files and
for progress messages.

Finally, there is information about aspects of the organization of the LAF information,
e.g. the sort order of nodes.

Where is the API?
=================

The API is a method of the task processor: :meth:`API() <laf.task.LafTask.API>`.
This method returns you a set of *API elements*: objects and/or methods that you can use to retrieve
information about the LAF resource: its features, nodes, edges, primary data and
even some of the XML identifiers used.

By calling this method you can insert the API elements in your local namespace and give it your own names.

This has two advantages: efficiency and cleanliness of the code of tasks.

Because API elements might easily be called millions of times in a loop, no space should be
wasted by things as method lookup. Local names are faster.

The one who writes tasks may choose names that nicely stand out in the rest of his code,
enabling readers of the code to easily spot the interface with the actual LAF resource.

For the sake of documentation, however, I have chosen names for the API elements, and will stick to
them.

Calling the API
===============
First you have to get a *processor* object. This is how you get it:

* in notebook mode::

    import laf
    from laf.notebook import Notebook
    processor = Notebook()

* in workbench mode::

    def task(processor):
        '''this function executes your task'''

Once you have the processor, you get the API by means of a call like this::

    API = processor.API()
    F = API['F']
    C = API['C']
    P = API['P']
    X = API['X']
    NN = API['NN']
    msg = API['msg']

Of course, you only have to give names to the elements you really use.
And if performance is not important, you can leave out the naming altogether and just refer to 
the elements by means of the API dictionary::

    for i in API['NN']():
        this_type = API['F'].shebanq_db_otype.v(i)

LAF API
=======
Here is a description of the API elements as returned by the API() call, except ``msg``.

F (Features)
------------
Examples::

    F.shebanq_db_otype.v(node)
    F.shebanq_mother__e.v(edge)
    F.shebanq_ft_gender.s()
    F.shebanq_ft_gender.s(value='feminine')

All that you want to know about features and are not afraid to ask.

*F* is an object, and for each feature that you have declared, it has a member
with a handy name.

``F.shebanq_db_otype`` is a feature object
that corresponds with the LAF feature given in an annotation in the annotation space ``shebanq``,
with label ``db`` and name ``otype``.
It is a node feature.

``F.shebanq_mother__e`` is also a feature object, but now on an edge, and corresponding
with an empty annotation.
Note the extra ``_e`` appended to the name, because this is an *edge* feature.

If a node or edge is annotated by an empty annotation, we do not have real features, but still there
is an annotation label and an annotation space.
In such cases we leave the feature name empty.
The values of such annotations are always the empty string.
Whether a node or edge has such an empty feature is determined by whether the value is ``''`` or ``None``.

You can look up feature values by calling the method ``v(«node/edge»)`` on feature objects.

You can use features to define sets in an easy manner.
The ``s()`` method yields an iterator that iterates over all nodes for which the feature in question
has a defined value. For the order of nodes, see :ref:`node-order`.

If a value is passed to ``s()``, only those nodes are visited that have that value for the feature in question.

C (Connectivity)
----------------
Examples::

    target_node in C.xyz_ft_property['myvalue'][source_node]
    target_node in C.shebanq_mother_[''][source_node]
    target_node in C._node_[''][source_node]

This is the connectivity of nodes by edges.
It is an object that specifies completely how you can walk from one node to another
by means of an edge.

For each *edge*-feature that you have declared, it has a member
with a handy name.

``C.xyz_ft_property`` is a connection table based on the
edge-feature ``property`` in the annotation space ``xyz``, under annotation label ``ft``.
Note that there is no ``_e`` behind the name, because we are only dealing with edge-features here.

Such a table gives for each value of the edge-feature in question a nested dictionary, for example::

    C.xyz_ft_property['myvalue']

The first key it accepts is the node you want to start with (``source_node``),
and what you get then::

    C.xyz_ft_property['value'][source_node]

is a dictionary where the keys are nodes and the values are ``None``, in other words: a set of nodes.

These are the nodes reachable by an edge from ``source_node`` that has been annotated by
feature ``property`` in an annotation with label ``ft`` in the space ``xyz``.

There may be edges that have not been annotated.
These edges can also be used to travel from node to node.

Instead of specifying a feature, you specify ``_none_``, so::

    target_node in C._node_[''][source_node]

If you want to use these edges, you have to specify in your load directives::

    "other_edges": True,

.. caution::
    The edges indicated by ``none`` are the edges that do not have any of the features specified in your
    load directives. The only way to be sure that these edges are truly un-annotated, is to
    specify *all* edge features in your load directives.
    I am not pleased with this, but it is quite a job to find out the unannotated edges,
    especially in the presence of extra annotation packages, that may annotated previously
    un-annotated edges.

See the example task :mod:`mother` and :mod:`edges` for working code with connectivity.

NN (Next Node)
--------------
Examples::
    
    (a) for node in NN():
            pass

    (b) for node in NN(test=F.shebanq_db_otype.v, value='book'):
            pass

    (c) for node in NN(test=F.shebanq_sft_book.v, values=['Isaiah', 'Psalms']):
            pass

This is also walking through nodes, not by edges, but through a predefined set, in the
natural order given by the primary data (see :ref:`node-order`).

It is an *iterator* that yields a new node everytime it is called.

The ``test`` and ``value`` arguments are optional.
If given, ``test`` should be a *callable* with one argument, returning a string;
``value`` should be a string and ``values`` should be an iterable of strings.

``test`` will be called for each passing node,
and if the value returned is not in the set given ``value`` and/or ``values``,
the node will be skipped.

Example (a) iterates through all nodes, (b) only through the book nodes, because *test*
is the feature value lookup function associated with the ``shebanq_db_otype`` function,
which gives for each node its type.

.. note::
    The type of a node is not a LAF concept, but a concept in this particular LAF resource.
    There are annotations which give the feature ``shebanq_db_otype`` to nodes, stating
    that nodes are books, chapters, words, phrases, and so on.

See :meth:`next_node() <laf.task.LafTask.API>`.

X (XML Identifiers)
-------------------

Examples::

    X.node.r(i)
    X.node.i(x)
    X.edge.r(i)
    X.edge.i(x)

If you need to convert the integers that identify nodes and edges in the compiled data back to
their original XML identifiers, you can do that with the *X* object.

It has two members, ``X.node`` and ``X.edge``, which contain the separate mapping tables for
nodes and edges.

Both have two methods, corresponding to the direction of the translation:
with ``X.node.i(«xml id»)`` you get the corresponding number of a node, and with ``X.node.r(«number»)``
you get the original XML id by which the node was identified in the LAF resource.

Analogously for edges.

P (Primary Data)
----------------
Examples::

    P.data(node)

Your gateway to the primary data. For nodes ``node`` that are linked to the primary data by one or more regions,
``P.data(node)`` yields a set of chunks of primary data, corresponding with those regions.

The chunks are *maximal*, *non-overlapping*, *ordered* according to the primary data.

Every chunk is given as a tuple (*pos*, *text*), where *pos* is the position in the primary data where
the start of *text* can be found, and *text* is the chunk of actual text that is specified by the region.
The primary data is only available if you have specified in the *load* directives: 
``primary: True``

.. caution:: Note that *text* may be empty.
    This happens in cases where the region is not a true interval but merely
    a point between two characters.

Input and Output
================
Examples::

    out_handle = processor.add_output("output.txt")
    in_handle  = processor.add_input("input.txt")

    msg(text)
    msg(text, newline=False)
    msg(text, withtime=False)


You can create an output filehandle, open for writing, by calling the
method :meth:`add_output() <laf.task.LafTask.add_output>`
and assigning the result to a variable, say *out_handle*.

From then on you can write output simply by saying::

    out_handle.write(text)

You can create as many output handles as you like in this way.
All these files and up in the task specific working directory.

Likewise, you can place additional input files in that directory,
and read them by saying::

    text = in_handle.read()

Once your task has finished, LAF-Fabric will close them all.

You can issue progress messages while executing your task.
These messages go to the console (the terminal, or the output of a code cell,
depending whether you are in workbench mode or notebook mode).

These messages get the elapsed time prepended, unless you say ``withtime=False``.

A newline will be appended, unless you say ``newline=False``.

The elapsed timeis reckoned from the start of the task, but after all the task-specific
loading of features.

.. _node-order:

Node order
==========
There is an implicit partial order on nodes, derived from their attachment to *regions*
which are stretches of primary data, and the primary data is totally ordered.
The order we use in LAF-Fabric is defined as follows.

Suppose we compare node *A* and node *B*.
Look up all regions for *A* and for *B* and determine the first point of the first region
and the last point of the last region for *A* and *B*, and call those points *Amin, Amax*, *Bmin, Bmax* respectively. 

Then region *A* comes before region *B* if and only if *Amin* < *Bmin* or *Amin* = *Bmin* and *Amax* > *Bmax*.

In other words: if *A* starts before *B*, then *A* becomes before *B*.
If *A* and *B* start at the same point, the one that ends last, counts as the earlier of the two.

If neither *A* < *B* nor *B* < *A* then the order is not specified.
LAF-Fabric will select an arbitrary but consistent order between thoses nodes.
The only way this can happen is when *A* and *B* start and end at the same point.
Between those points they might be very different. 

The nice property of this ordering is that if a set of nodes consists of a proper hierarchy with respect to embedding,
the order specifies a walk through the nodes were enclosing nodes come first,
and embedded children come in the order dictated by the primary data.
