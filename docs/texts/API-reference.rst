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
First you have to get a *processor* object. This is how you get it::

    import laf
    from laf.notebook import Notebook
    processor = Notebook()

Then you have to *initialize* the processor, by which you direct it to a LAF source, possibly with extra annotation packages,
and where you specify which data to load::

    processor.init('bhs3.txt.hdr', '--', 'cooccurrences', {
        "xmlids": {
            "node": False,
            "edge": False,
        },
        "features": {
            "shebanq": {
                "node": [
                    "db.otype",
                    "ft.part_of_speech,noun_type,lexeme_utf8",
                    "sft.book",
                ],
                "edge": [
                ],
            },
        },
    })

Once you have the processor, you get the API by means of a call like this::

    API = processor.API()
    F = API['F']
    C = API['C']
    Ci = API['Ci']
    P = API['P']
    X = API['X']
    NN = API['NN']
    NE = API['NE']
    msg = API['msg']
    infile = API['infile']
    outfile = API['outfile']
    my_file = API['my_file']

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

**Alternatively**, you can use the slightly more verbose alternative forms:: 

    F.F['shebanq_db_otype'].v(node)

They give exactly the same result:
``F.shebanq_db_otype`` is the same thing as ``F.F['shebanq_db_otype']`` provided the feature has been loaded.

The advantage of the alternative form is that the feature is specified by a *string*
instead of a *method name*.
That means that you can work with dynamically computed feature names.

You can use features to define sets in an easy manner.
The ``s()`` method yields an iterator that iterates over all nodes for which the feature in question
has a defined value. For the order of nodes, see :ref:`node-order`.

If a value is passed to ``s()``, only those nodes are visited that have that value for the feature in question.

``F.feature_list`` is a dictionary containing all features that are loadable.
These are the features found in the compiled current source or in the compiled current annox.

The dictionary has exactly the same organization as the dictionary that you have to pass to ``processor.init()``
when you specifiy the features to load.
So you can copy and paste the features to load from the output of ``F.feature_list`` to the ``processor.init()`` call.

.. _connectivity:

C, Ci (Connectivity)
--------------------
Examples::

    target_node in C.xyz_ft_property['myvalue'][source_node]
    target_node in C.shebanq_mother_[''][source_node]
    target_node in C._node_[''][source_node]

    source_node in C.xyz_ft_property['myvalue'][target_node]
    source_node in C.shebanq_mother_[''][target_node]
    source_node in C._node_[''][target_node]

    top_nodes = C.shebanq_parents__T('', words)

This is the connectivity of nodes by edges.
It is an object that specifies completely how you can walk from one node to another
by means of an edge.

For each *edge*-feature that you have declared, it has a members
with a handy name.

.. caution::
    This functionality takes processing time when you load the API.
    It takes 10-15 seconds on a Macbook Air for the Hebrew Bible.

    However, you do not have to suffer from this repeated overhead.
    Once you have called the *API()* function, the data stays in memory, and you can experiment
    without recomputing this information over and over again.

``C.xyz_ft_property`` is a connection table based on the
edge-feature ``property`` in the annotation space ``xyz``, under annotation label ``ft``.
Note that there is no ``_e`` behind the name, because we are only dealing with edge-features here.

Such a table gives for each value of the edge-feature in question a nested dictionary, for example::

    C.xyz_ft_property['myvalue']

The first key it accepts is the node you want to start with (``source_node``),
and what you get then::

    C.xyz_ft_property['value'][source_node]

is :py:class:`set` of nodes.

These are the nodes reachable by an edge from ``source_node`` that has been annotated by
feature ``property`` in an annotation with label ``ft`` in the space ``xyz``.

Analogously::

    Ci.xyz_ft_property['value'][target_node]

are the nodes that have an outgoing edge to ``target_node`` that has been annotated by
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

A common task is to find the top nodes of a given set of nodes with respect to a set of edges.
For example, if you have a node set with all word nodes, and if you have edges labelled with the string ``parents``,
you might be interested in following these edges from each of the words until you cannot travel further, and then
collect all the nodes where you came to a stand still. These are the top nodes.
You can do this as follows::

    words = NN(test=F.shebanq_db_otype.v, value='word')
    top_nodes = C.shebanq_parents__T('', words)

Note the extra ``T`` after the name of the feature.
In the Hebrew Text database, you get all *sentence* nodes in this way.

.. note::
    In this particular case, you can also get the sentences by::

        sentences = NN(test=F.shebanq_db_otype.v, value='sentence')

    The point is that you can check whether really all top nodes are sentences and vice versa.

You can also travel backwards::

    sentences = NN(test=F.shebanq_db_otype.v, value='sentence')
    bottom_nodes = Ci.shebanq_parents__T('', sentences)

See the example task :mod:`mother` and :mod:`edges` and :mod:`trees` for working code with connectivity.

NN (Next Node)
--------------
Examples::
    
    (a) for node in NN():
            pass

    (b) for node in NN(test=F.shebanq_db_otype.v, value='book'):
            pass

    (c) for node in NN(test=F.shebanq_sft_book.v, values=['Isaiah', 'Psalms']):
            pass

NN() walks through nodes, not by edges, but through a predefined set, in the
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

.. _node-events:

NE (Next Event)
---------------
Examples::
    
    for (anchor, events) in NE():
        for (node, kind) in events:
            if kind == 3:
                '''close node event'''
            elif kind == 2:
                '''suspend node event'''
            elif kind == 1:
                '''resume node event'''
            elif kind == 0:
                '''start node event'''
            
    for (anchor, events) in NE(key=filter):
    for (anchor, events) in NE(simplify=filter):
    for (anchor, events) in NE(key=filter1, simplify=filter2):

NE() walks through the primary data, or, more precisely, through the anchor positions where
something happens with the nodes.

It is an *iterator* that yields the set of events for the next anchor that has events everytime it is called.
It will return a pair, consisting of the anchor position and a list of events.

See :meth:`next_event() <laf.task.LafTask.API>`.

What can happen is that a node *starts*, *resumes*, *suspends* or *ends* at a certain anchor position.
This things are called *node_events*.

*start*
    The start anchor of the first range that the node is linked to
*resume*
    The start anchor of any non-first range that the node is linked to
*suspend*
    The end anchor of any non-last range that the node is linked to
*end*
    The end anchor of the last range that the node is linked to

The events for each anchored are are ordered according to the primary data order of nodes, see :ref:`node-order`,
where for events of the kind *suspend* and *end* the order is reversed.

.. caution::
    While the notion of node event is quite natural and intuitive, there are subtle difficulties.
    It all has to do with embedding, gaps and empty nodes. 
    If your nodes link to portions of primary data with gaps, and if some nodes link to points in de primary data
    (rather than stretches), then the node events generated by NE() will in general not completely ordered as desired.
    You should consider using more explicit information in your data about embedding, such as edges between nodes.
    If not, you have to code intricate event reordering in your task.

.. note::
    For non-empty nodes (i.e. nodes linked to at least one region with a distinct start and end anchor),
    this works out nicely.
    At any anchor the closing events are before the opening events.
    However, an empty node would close before all other closing events at that node, and open after all
    other opening events at that node. It would close before it would open.
    That is why we treat empty nodes differently: their open-close events are placed between
    the list of close events of other nodes and the list of open events of other nodes.

.. note::
    The embedding of empty nodes is hard to define without further knowledge.
    Are two empty nodes at the same anchor position embedded in each other or not?
    Is an empty node embedded in a node that opens or close at the same anchor?
    We choose a minimalistic interpretation: multiple embedded nodes at the same anchor
    are not embedded in each other, and are not embedded in nodes that open or close at the
    same anchor.

The consequence of this ordering is that if the nodes correspond to a tree structure, the node events
correspond precisely with the tree structure.
You can use the events to generate start and end tags for each node and you get a properly nested representation.

Note however, that if two nodes have the same set of ranges, it is impossible to say which embeds which.

You can, however, pass a *key=filter* argument to NE(). 
Before a node event is generated for a node, *filter* will be applied to it.
If the outcome is ``None``, the events for this node will be skipped, the consumer of events will not see them.
If the outcome is not ``None``, the value will be used as a sort key for additional sorting.

The events are already sorted fairly good, but only those node events that have the same kind and corresponds to nodes
with the same start and end point, may occur in an undesirable order.
By assigning a key, you can remedy that. 
The key will be used in inversed order for opening/resume events, and in normal order for close/suspend events.

For example, if you pass a filter as *key* that assigns to nodes that correspond to *sentences* the number 5,
and to nodes that correspond to *clauses* the number 4, then the following happens.

Whenever there is a sentence that coincides with a clause, then the sentence-open event will
occur before the clause-open event, and the clause-close before the sentence-close.

.. note::
    The ordering induced by *key=filter* is also applied to multiple empty nodes at the same anchor.
    Without the ordering, they are not embedded in each other, but the ordering
    may embed some empty nodes in other ones.
    This additional ordering will not reorder events for empty nodes with those of enclosing non-empty nodes,
    because it is impossible to tell whether an empty node is embedded in a node that is closing at this point
    or at a node that is opening at this point. 

If there are many regions in the primary data that are not inside regions or in regions that are not linked to nodes,
or in regions not linked to relevant nodes, it may bethe case that many relevant nodes get interrupted around these gaps.
That will cause many spurious suspend-resume pairs of events. It is possible to suppress those.

Example: suppose that all white space is not linked to nodes, and suppose that sentences and clauses are linked
to their individual words. Then they become interrupted at each word.

If you pass the *simplify=filter* argument to NE() the following will happen.
First of all: a gap is now a stretch of primary data that does not occur between the start and end position
of any node for which the filter is not None.

In our example of sentences and clauses: suppose that a verse is linked to the continuous regions of all its material,
including white space. Suppose that by our *key=filter1* argument we are interested in sentences, clauses and verses.
With respect to this set, the white spaces are no gaps, because they occur in the verses.

But if we give a simplify=filter2 that only admits sentences and clauses, then the white spaces become true gaps.
And NE(simplify=filter2) will actively weed out all node-suspend, node-resume pairs around true gaps.

Even if the nodes do not correspond with a tree, the order of the node events correspond to an
intuitive way to mark the embedding of nodes.

Note that we do not say *region* but *range*.
LAF-Fabric has converted the region-linking of nodes by range-linking.
The range list of a node is a sequence of maximal, non-overlapping pieces of primary data in primary data order.

Consequently, if a node suspends at an anchor, it will not resume at that anchor,
so the node has a real gap at that anchor.

Formally, a node event is a tuple ``(node, kind)`` where ``kind`` is 0, 1, ,2, or 3, meaning
*start*, *resume*, *suspend*, *end* respectively.

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

    out_handle = outfile("output.txt")
    in_handle  = infile("input.txt")

    msg(text)
    msg(text, newline=False)
    msg(text, withtime=False)


You can create an output filehandle, open for writing, by calling the
method :meth:`outfile <laf.task.LafTask.add_output>`
and assigning the result to a variable, say *out_handle*.

From then on you can write output simply by saying::

    out_handle.write(text)

You can create as many output handles as you like in this way.
All these files and up in the task specific working directory.

Likewise, you can place additional input files in that directory,
and read them by saying::

    text = in_handle.read()

Once your task has finished, LAF-Fabric will close them all.

If you want to refer in your notebook, outside the LAF-Fabric context, to files in the task-specific working directory,
you can do so by saying::

    full_path = my_file("output.csv")

The method ``my_file`` prepends the full directory path in front of the file name.
It does not check whether the file exists.

You can issue progress messages while executing your task.
These messages go to the output of a code cell.

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

