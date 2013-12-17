Writing Tasks
#############

What is a task?
===============

A task is an ordinary Python script with some magical capabilities
for looking into a LAF resource (a *compiled* LAF resource to be precise).

A task gets those capabilities because it is called by the workbench.
In order to be called by the workbench, you have to put into the *tasks* directory
(see :ref:`configuration <task_dir>`).

The workbench passes an object to your task,
which contains the information needed to peek into the LAF resource.
Conversely, in your task script you can pass some initialization information to the workbench,
so that it can build or load the appropriate feature data. 
And you can ask the workbench for convenient names by which you can use the feature
data that is present in the LAF resource.

Apart from these things, your script may contain arbitrary Python code,
it may import arbitrary modules.
The workbench is agnostic of your code, it does not screen it, and will not perform deep tricks.

A leading example
=================
Our target LAF resource is the Hebrew text data base (see :ref:`data`).
In the text database there are objects carrying features.
The conversion to LAF has translated objects in to nodes, and relationships between objects into edges.
The features of the text database have been grouped and put into annotations, which carry labels.
Objects have types in the database.
The types of objects translate to annotations with label *db* with the feature *otype*.
Likewise the *id* of objects translates into feature *db.oid*.
The anchoring of objects to primary data: the features *minmonad*, *maxmonad* and *monads* take care of that.
In the original LAF it looks like this::

    <node xml:id="n28737"><link targets="w_1 w_2 w_3 w_4 w_5 w_6 w_7 w_8 w_9 w_10 w_11"/></node>
    <a xml:id="al28737" label="db" ref="n28737"><fs>
        <f name="otype" value="clause"/>
        <f name="oid" value="28737"/>
        <f name="monads" value="1-11"/>
        <f name="minmonad" value="1"/>
        <f name="maxmonad" value="11"/>
    </fs></a>

More on features
================
When the workbench compiles features into binary data, it forgets the annotations in which the features come,
but the annotation *space* and *label* are retained in a double prefix to the feature name.
In the example above, you see an annotation with label ``db`` and in it a feature structure
with features named ``otype``, ``oid``, etc.
The annotation is in the default *annotation space*, which happens to be ``shebanq``.
The workbench remembers those features by their *fully qualified* names: ``shebanq:db.otype``, ``shebanq:db.oid`` etc.
There may also be annotations without feature contents. Such annotations will be stored as features with as name the 
annotation label only, without the dot: ``shebanq:db``.

.. note::
    Annotations may reference nodes or edges.
    It is possible that nodes and edges have features with the same name. 
    However, the workbench maintains a strict distinction between features
    of nodes and features of edges. They have separate name spaces, implicitly.
    Features names that are used for nodes and edges may coexist, but their
    data are in separate tables.

The example task :mod:`objects` lists all objects in *resource order* with their original ids,
object types etc and even their node number in the compiled resource.
Not very useful, but handy for debugging or linking new annotation files to the existing data.
Here is a snippet of output::

     426500   28737 clause               {1-11         }
     514887   34680 clause_atom          {1-11         }
    1131695   84383 sentence             {1-11         }
    1203049   88917 sentence_atom        {1-11         }
    1385280   95056 half_verse           {1-4          }
     604948   59556 phrase               {1-2          }
     862057   40767 phrase_atom          {1-2          }
          1       2 word                 {1            }
          2       3 word                 {2            }
          3       4 word                 {3            }
     604949   59557 phrase               {3            }
     862058   40768 phrase_atom          {3            }
          4       5 word                 {4            }

Note the same clause object *28737* as in the original LAF file.
Finally, here is the complete Python code of the task that produced this output::

    load = {
        "xmlids": {
            "node": False,
            "edge": False,
        },
        "features": {
            "shebanq": {
                "node": [
                    "db.oid,otype,monads",
                ],
                "edge": [
                ],
            },
        },
    }

    def task(graftask):
        '''Produces a list of all WIVU objects with their types, ids and
        *monads* (words) they contain.
        '''
        (msg, P, NN, F, X) = graftask.get_mappings()

        out = graftask.add_result("output.txt")

        for i in NN():
            oid = F.shebanq_db_oid.v(i)
            otype = F.shebanq_db_otype.v(i)
            monads = F.shebanq_db_monads.v(i)
            out.write("{:>7} {:>7} {:<20} {{{:<13}}}\n".format(i, oid, otype, monads))

Information flow from task to workbench
=======================================
The main thing the workbench needs to know about your task is a declaration of
what data the task will use.
The task needs to tell which feature data should be loaded and whether XML identifier tables
should be loaded.
Both must be specified separately for nodes and edges.

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
    the workbench will stop your task and shout error messages at you.
    If you declare features that do not exist in the LAF data, you just get
    a warning. But if you try to use such features, you get also a loud error.

Information flow from workbench to task
=======================================
The workbench will call the function *task(object)* in your task script,
and the thing it hands over to it as *object* is an object of
class :class:`GrafTask <graf.task.GrafTask>`.
By using this object, you have to access all of its methods. 

In order to write an efficient task,
it is convenient to import the names of the most important methods as *local variables* of the *task* function.
The lookup of names in Python is fastest for local names.
And it makes the code much cleaner.

The method :meth:`get_mappings() <graf.task.GrafTask.get_mappings>` delivers the methods,
and it is up to you to give them names.
It is recommended to stick to the names provided here in this example.
Here is a short description of the corresponding methods.

*F*
    All that you want to know about features and are not afraid to ask.
    It is an object, and for each feature that you have declared, it has a member
    with a handy name. For example, ``F.shebanq_db_otype`` is a feature object
    that corresponds with the LAF feature given in an annotation in the annotation space ``shebanq``,
    with label ``db`` and name ``otype``.
    It is a node feature, because otherwise the name had a 
    ``_e`` appended to it.
    You can look up a feature value of this feature, say for node ``n``,by saying:
    ``F.shebanq_db_otype.v(n)``. 

*P(node)*
    Your gateway to the primary data. For nodes *n* that are linked to the primary data by 1 or more regions,
    P(*n*) yields a set of chunks of primary data, corresponding with those regions.
    The chunks are maximal, non-overlapping, ordered according to the primary data.
    Every chunk is given as a tuple (*pos*, *text*), where *pos* is the position in the primary data where
    the start of *text* can be found, and *text* is the chunk of actual text that is specified by the region.
    Note that *text* may be empty. This happens in cases where the region is not a true interval but merely
    a point between two characters.

*NN(test=function value=something)*
    If you want to walk through all the nodes, possibly skipping some, then this is your method.
    It is an *iterator* that yields a new node everytime it is called.
    The order is so-called *primary data order*, which will be explained below.
    The ``test`` and ``value`` arguments are optional.
    If given, ``test`` should be a *callable* with one argument, returning a string;
    ``value`` should be a string.
    ``test`` will be called for each passing node,
    and if the value returned is not equal to the given ``value``,
    the node will be skipped.
    See :meth:`next_node() <graf.task.GrafTask.get_mappings>`.

*X*
    If you need to convert the integers that identify nodes and edges in the compiled data back to
    their original XML identifiers, you can do that with the *X* object.
    It has two members, ``X.node`` and ``X.edge``, which contain the separate mapping tables for
    nodes and edges. Both have two methods, corresponding to the direction of the translation:
    with ``X.node.i(«xml id»)`` you get the corresponding number of a node, and with ``X.node.r(«number»)``
    you get the original XML id by which the node was identified in the LAF resource.

msg(text, newline=True, withtime=True)
    Use this to write a message with time information to the terminal and log file.
    Normally it appends a newline to the text, but you can suppress it.
    You can also suppress the time indication before the text.

Output
======
You can create an output filehandle, open for writing, by calling the
method :meth:`add_result() <graf.task.GrafTask.add_result>`
and assigning the result to a variable, say *out*.
From then on you can write output simply by saying::

    out.write(text)

You can create as many output handles as you like in this way.
Once your task has finished, the workbench will close them all.

.. _node-order:

Node order
==========
There is an implicit partial order on nodes, derived from their attachment to *regions*
which are stretches of primary data, and the primary data is totally ordered.
The order we use in the workbench is defined as follows.

Suppose we compare node *A* and node *B*.
Look up all regions for *A* and for *B* and determine the first point of the first region
and the last point of the last region for *A* and *B*, and call those points *Amin, Amax*, *Bmin, Bmax* respectively. 

Then region *A* comes before region *B* if and only if *Amin* < *Bmin* or *Amin* = *Bmin* and *Amax* > *Bmax*.

In other words: if *A* starts before *B*, then *A* becomes before *B*.
If *A* and *B* start at the same point, the one that ends last, counts as the earlier of the two.

If neither *A* < *B* nor *B* < *A* then the order is not specified.
The workbench will select an arbitrary but consistent order between thoses nodes.
The only way this can happen is when *A* and *B* start and end at the same point.
Between those points they might be very different. 

The nice property of this ordering is that if a set of nodes consists of a proper hierarchy with respect to embedding,
the order specifies a walk through the nodes were enclosing nodes come first,
and embedded children come in the order dictated by the primary data.

