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

The API is a method of the task processor: ``API()`` in ``laf.fabric``.
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

    from laf.fabric import LafFabric
    processor = LafFabric(
        work_dir="/Users/you/laf-fabric-data",
        laf_dir="/Users/you/laf-fabric_data/laf",
        save=True,
        verbose='NORMAL',
    )

All arguments to ``LafFabric()`` are optional. 
If you have a config file in your home directory, you can leave out ``work_dir=...`` and ``laf_dir=...`` and ``save=...``.
If you have not, or if you want to modify that file, you can pass the desired values to ``work_dir`` and ``laf_dir`` and say ``save=True``.
You have to do that once, after that you can leave out this stuff again.

The ``verbose`` argument tells LAF-Fabric how much feedback it should give you.
Possible values in increasing level of verbosity:: 

    SILENT      after initialization absolutely no messages
    ERROR       only error messages
    WARNING     only error and warning messages
    INFO        important information, warnings and errors
    NORMAL      normal progress messages and everything above (default)
    DETAIL      detailed messages and above
    DEBUG       absolutely everything

Then you have the processor to load data, according to the source you choose::

    API= processor.load('bhs3.txt.hdr', '--', 'cooccurrences',
        {
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
            "primary": False,
        },
        compile_main=False, compile_annox=False,
    )

If you want to do other tasks in your script, you can repeat calls to ``API()``.
LAF-Fabric will figure out which data can be kept in memory, which data has to be cleared, and which data
needs to be loaded.

**``compile-source`` and ``compile-annox``**
If you have changed the LAF resource or the selected annotation package, LAF-fabric will detect it and recompile it.
The detection is based on the modified dates of the GrAF header file and the compiled files.
In cases where LAF-fabric did not detect a change, but you need to recompile, use this flag.

After loading, you get the individuela API methods as follows::

    # features in sofar as declared under "features"
    F = API['F']

    # connectivity, only if you have declared edge features
    C = API['C']
    Ci = API['Ci']

    # primary data, only if you have specified "primary": True
    P = API['P']

    # XML identifiers, only in sofar as declared under "xmlids"
    X = API['X']

    # The "before" ordering of nodes
    BR = API['BR']

    # The "next node" iterator
    NN = API['NN']

    # The "next event" iterator, only if you have specified "primary": True
    NE = API['NE']

    # The function to issue messages with
    msg = API['msg']

    # File handling (opening for input, output, , closing, getting full path)
    infile = API['infile']
    outfile = API['outfile']
    close = API['close']
    my_file = API['my_file']

Of course, you only have to give names to the elements you really use.
And if performance is not important, you can leave out the naming altogether and just refer to 
the elements by means of the API dictionary::

    for i in API['NN']():
        this_type = API['F'].shebanq_db_otype.v(i)

Remember that if you have 10 million nodes, you may incur an appreciable performance difference
compared to::

    NN = API['NN']
    for i in NN():
        this_type = API['F'].shebanq_db_otype.v(i)

Not all API elements contain meaningful information.
It depends on what you have specified in the ``init()`` call.

LAF API
=======
Here is a description of the API elements as returned by the API() call.

F, FE, F_all, FE_all (Features)
-------------------------------
Examples::

    F.shebanq_db_otype.v(node)

    FE.shebanq_mother_.v(edge)

    F.shebanq_ft_gender.s()

    F.shebanq_ft_gender.s(value='feminine')

    all_node_features = API['F_all']
    all_edge_features = API['FE_all']

All that you want to know about features and are not afraid to ask.

*F* is an object, and for each *node* feature that you have declared, it has a member
with a handy name. Likewise for *FE*, but now for *edge* features.

``F.shebanq_db_otype`` is a feature object
that corresponds with the LAF feature given in an annotation in the annotation space ``shebanq``,
with label ``db`` and name ``otype``.
It is a node feature.

``FE.shebanq_mother_`` is also a feature object, but now on an edge, and corresponding
with an empty annotation.

If a node or edge is annotated by an empty annotation, we do not have real features, but still there
is an annotation label and an annotation space.
In such cases we leave the feature name empty.
The values of such annotations are always the empty string.

You can look up feature values by calling the method ``v(«node/edge»)`` on feature objects.

**Alternatively**, you can use the slightly more verbose alternative forms:: 

    F.item['shebanq_db_otype'].v(node)
    FE.item['shebanq_mother_'].v(edge)

They give exactly the same result:
``F.shebanq_db_otype`` is the same thing as ``F.item['shebanq_db_otype']`` provided the feature has been loaded.

The advantage of the alternative form is that the feature is specified by a *string*
instead of a *method name*.
That means that you can work with dynamically computed feature names.

You can use features to define sets in an easy manner.
The ``s()`` method yields an iterator that iterates over all nodes for which the feature in question
has a defined value. For the order of nodes, see :ref:`node-order`.

If a value is passed to ``s()``, only those nodes are visited that have that value for the feature in question.

The ``F_all`` and ``FE_all`` list all features that are loadable.
These are the features found in the compiled current source or in the compiled current annox.

**Main source and annox**

If you have loaded an extra annotation package (*annox*), each feature value is looked up first according to the
data of the *annox*, and only if that fails, according to the main source. The ``s()`` method
combines all relevant information.

.. _connectivity:

C, Ci (Connectivity)
--------------------
Examples:

**A. Normal edge features**::

    target_node in C.xyz_ft_property.v(source_node)
    (target_node, value) in C.xyz_ft_property.vv(source_node)
    target_nodes in C.xyz_ft_property.endnodes(source_nodes, value='val')

    source_node in Ci.xyz_ft_property.v(target_node)
    (source_node, value) in Ci.xyz_ft_property.vv(target_node)
    source_nodes in Ci.xyz_ft_property.endnodes(target_nodes, value='val')

**B. Special edge features**::

    target_node in C.__x.v(source_node)
    target_node in C.__y.v(source_node)

    source_node in Ci.__x.v(target_node)
    source_node in Ci.__y.v(target_node)

(the methods ``vv`` and ``endnodes`` are also valid for the special features.

**Ad A. Normal edge features**

This is the connectivity of nodes by edges.
``C`` and ``Ci`` are objects that specify completely how you can walk from one node to another
by means of edges.

For each *edge*-feature that you have declared, it has a member with a handy name, exactly as in the ``FE`` object.

``C.xyz_ft_property`` is a connection table based on the
edge-feature ``property`` in the annotation space ``xyz``, under annotation label ``ft``.

Such a table yields for each node ``node1`` pairs ``(node2, val)`` for which there is an edge going
from ``node1`` to ``node2``, annotated by this feature with value ``val``.

This is what the ``vv()`` methods yields as a generator.
If you are not interested in the actual values, there is a simpler generator ``v()``, just yielding the nodes.
If there are multiple edges with several values going from ``node1`` to ``node2``, ``node2`` will be yielded
only once.

If you want to travel onwards until there are no outgoing edges left that qualify, use the method ``endnodes()``.

For all this functionality there is also a version that uses the opposite edge direction.
Use ``Ci`` instead of ``C``.

If you have loaded an extra annotation package (*annox*), lookups are first performed with the data from the *annox*,
and only if that fails, from the main source. All relevant data will be combined.

**Ad B. Special edge features**

There may be edges that are completely unannotated. These edges are made available through the special
``C`` and ``Ci`` members called ``__x``. (No annotation namespace, no annotation label, name ``'x'``.)

If you have loaded an *annox*, it may have annotated formerly unannotated edges.
However, this will not influence the ``__x`` feature.

``__x`` always corresponds to the unannotated edges in the main source, irrespective of any *annox* whatsoever.

But loading an annox introduces an other special edge feature: ``__y``: all edges that have been annotated by the annox.

In your script you can compute what the unannotated edges are according to the combination of main source and annox.
It is all the edges that you get with ``__x``, minus those yielded by ``__y``.

Think of ``x`` as *excluded* from annotations, and ``y`` as *yes annotations*.

See the example notebook
`trees <http://nbviewer.ipython.org/github/judithgottschalk/ETCBC-data/blob/master/notebooks/syntax/trees.ipynb>`_
for working code with connectivity.

BF (Before)
-----------
Examples::

    if BF(nodea, nodeb) == None:
        # code for the case that nodea and nodeb do not have a mutual order
    elif BF(nodea, nodeb):
        # code for the case that nodea comes before nodeb
    else:
        # code for the case that nodea comes after nodeb

With this function you can do an easy check on the order of nodes.
The *BF* relation corresponds with the order used in the enumeration of nodes ``NN()`` below.

Especially when two nodes have no defined mutual order, you might want to supply an order
yourself in your tasks. 
With ``BF`` you can quickly see when that is the case.

There is no mutual order between two nodes if at least one of the following holds:

* at least one of them is not linked to the primary data
* both start and end at the same point in the primary data (what happens in between is immaterial).

NN (Next Node)
--------------
Examples::
    
    (a) for node in NN():
            pass

    (b) for node in NN(test=F.shebanq_db_otype.v, value='book'):
            pass

    (c) for node in NN(test=F.shebanq_sft_book.v, values=['Isaiah', 'Psalms']):
            pass

    (d) for node in NN(
            test=F.shebanq_db_otype.v,
            values=['phrase', 'word'],
            extrakey=lambda x: F_shebanq_db_otype.v(x) == 'phrase',
        ):
            pass

NN() walks through nodes, not by edges, but through a predefined set, in the
natural order given by the primary data (see :ref:`node-order`).
Only nodes that are linked to a region (one or more) of the primary data are
being walked.

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

In example (c) you can give multiple values for which you want the corresponding nodes.

Example (d) passes an extra sort key. The set of nodes is sorted on the basis of how they
are anchored to the primary data. Left comes before right, embedding comes before embedded.
But there are many cases where this order is not defined, namely between nodes that start at the
same point and end at the same point.

If you have extra information to order these cases, you can do so by passing ``extrakey``.
In this case the extrakey is ``False`` for nodes with carry a certain feature with value ``phrase``,
and ``True`` for the other nodes, which carry value ``word`` for that feature.
Because ``False`` comes before ``True``, the phrases come before the words they contain.

.. note::
    Without extrakey, all nodes that have not identical start and end points
    have already the property that they are yielded in the proper mutual order.
    The difficulty is where the ``BF`` method above yields ``None``.
    It is exactly these cases that are remedied with ``extrakey``. 
    The rest of the order remains untouched.

.. note::
    You can invoke a supplementary module of your choice to make the ordering more complete.
    See the section on extra data preparation below.

See ``next_node()`` in ``laf.fabric``.

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

**``NE()`` is only available if you have specified in the *load* directives: ``primary: True``.**

NE() walks through the primary data, or, more precisely, through the anchor positions where
something happens with the nodes.

It is an *iterator* that yields the set of events for the next anchor that has events everytime it is called.
It will return a pair, consisting of the anchor position and a list of events.

See ``next_event()`` in ``laf.fabric``.

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
    If not, you have to code intricate event reordering in your notebook.

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

X, XE (XML Identifiers)
-----------------------

Examples::

    X.r(i)
    X.i(x)
    XE.r(i)
    XE.i(x)

If you need to convert the integers that identify nodes and edges in the compiled data back to
their original XML identifiers, you can do that with the *X* object for nodes and the *XE* object for edges.

Both have two methods, corresponding to the direction of the translation:
with ``i(«xml id»)`` you get the corresponding number of a node/edge, and with ``r(«number»)``
you get the original XML id by which the node/edge was identified in the LAF resource.

P (Primary Data)
----------------
Examples::

    P.data(node)

**The primary data is only available if you have specified in the *load* directives: ``primary: True``.**

Your gateway to the primary data. For nodes ``node`` that are linked to the primary data by one or more regions,
``P.data(node)`` yields a set of chunks of primary data, corresponding with those regions.

The chunks are *maximal*, *non-overlapping*, *ordered* according to the primary data.

Every chunk is given as a tuple (*pos*, *text*), where *pos* is the position in the primary data where
the start of *text* can be found, and *text* is the chunk of actual text that is specified by the region.

.. caution:: Note that *text* may be empty.
    This happens in cases where the region is not a true interval but merely
    a point between two characters.

Input and Output
----------------
Examples::

    out_handle = outfile("output.txt")
    in_handle  = infile("input.txt")
    file_path = my_file("thefile.txt")
    close()

    msg(text)
    msg(text, verbose='ERROR')
    msg(text, newline=False)
    msg(text, withtime=False)


You can create an output filehandle, open for writing, by calling the ``outfile()`` method
and assigning the result to a variable, say *out_handle*.

From then on you can write output simply by saying::

    out_handle.write(text)

You can create as many output handles as you like in this way.
All these files end up in the task specific working directory.

Likewise, you can place additional input files in that directory,
and read them by saying::

    text = in_handle.read()

You can have LAF-Fabric close them all by means of ``close()`` without arguments.

If you want to refer in your notebook, outside the LAF-Fabric context, to files in the task-specific working directory,
you can do so by saying::

    full_path = my_file("thefile.txt")

The method ``my_file`` prepends the full directory path in front of the file name.
It does not check whether the file exists.

You can issue progress messages while executing your task.
These messages go to the output of a code cell.

You can adjust the verbosity level of messages, see above for possible values.

These messages get the elapsed time prepended, unless you say ``withtime=False``.

A newline will be appended, unless you say ``newline=False``.

The elapsed time is reckoned from the start of the task, but after all the task-specific
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

If you have a LAF resource and a method to order the nodes more completely,
you can supply that as an extra data preparation step. See below.

The nice property of this ordering is that if a set of nodes consists of a proper hierarchy with respect to embedding,
the order specifies a walk through the nodes were enclosing nodes come first,
and embedded children come in the order dictated by the primary data.

Extra data preparation
======================
.. caution::
    This section is meant for developers of extra modules on top of LAF-Fabric

LAF-Fabric admits other modules to precompute data to which it should be pointed.

Here is how it works. The example is that of adding additional order to the nodes
based on the informal embedding levels between books, chapters, sentences, clauses etc.

Suppose you are working with a specific resource, say the ETCBC Hebrew Text Database.
Probably there is already a package *etcbc* to streamline the tasks relevant to this resource.
To this package you can add a module, say *preprocess.py* in which you can define
an additional sort order on nodes.
Here is the actual contents of *etcbc.preprocess* in this distribution::

    import collections
    import array

    def node_order(API):
        '''Creates a form based on the information passed when creating this object.'''
        msg = API['msg']
        F = API['F']
        NN = API['NN']
        object_rank = {
            'book': -4,
            'chapter': -3,
            'verse': -2,
            'half_verse': -1,
            'sentence': 1,
            'sentence_atom': 2,
            'clause': 3,
            'clause_atom': 4,
            'phrase': 5,
            'phrase_atom': 6,
            'subphrase': 7,
            'word': 8,
        }
        def hierarchy(node): return object_rank[F.shebanq_db_otype.v(node)]
        return array.array('I', NN(extrakey=hierarchy))

    def node_order_inv(API):
        make_array_inverse = API['make_array_inverse']
        data_items = API['data_items']
        return make_array_inverse(data_items['zG00(node_sort)'])

    prepare = collections.OrderedDict((
        ('zG00(node_sort)', (node_order, __file__, True, 'etcbc')),
        ('zG00(node_sort_inv)', (node_order_inv, __file__, True, 'etcbc')),
    ))

Back to your notebook. Say::

    from etcbc import preprocess

then the following will happen:

* LAF-Fabric checks whether file *Z/etcbc/zG00(node_sort)* and *Z/etcbc/zG00(node_sort_inv)* exist next to the binary compiled data, and whether these files
  are newer than your module *preprocess.py*.
* If so, it loads this data from disk.
* If not, it will execute the *node_order* function, which sorts the nodes more completely than LAF-Fabric can, and write this data to disk
  in *Z/etcbc/zG00(node_sort)* and it also computes *node_order_inv* in order to get an inverse: *Z/etcbc/zG00(node_sort_inv)*.

Note that these functions can be programmed using the API of LAF-Fabric itself. Preparing data always takes place after full loading.
The prepared data will be subsequently loaded.

The *True* component in the dictionary *prepare* tells LAF-Fabric to use this data **instead of previously compiled data**.
In this case, there should be a data item keyed with ``mG00(node_sort)`` in the already loaded data (otherwise you get an error).
In fact, LAF-Fabric uses a data item with this name to help *NN()* iterate over its nodes in a convenient order.
So you have effectively supplanted LAF-Fabric's standard ordering of the nodes by your own ordering, which makes better use
of the particular structure of this data. 

If you had said ``False`` instead, no attempt of overriding existing data would have been made. If you want to use this data,
you can refer to it by:: 

        API['data_items']['zG00(node_sort)']

The *etcbc* directory corresponds to the ``etcbc`` component in the dictionary *prepare*.
In this way, different modules may keep their computed data separate from each other.
Computed data is always separated from the previously compiled data.

This data is only loaded if you have ``'prepare': etcbc.preprocess.prepare`` in your load instructions,
or if you have done an import like this::

    from etcbc.preprocess import prepare

then ``'prepare': prepare`` suffices.

In order to know the data that LAF-Fabric uses natively, look at the list in the ``names`` module.
