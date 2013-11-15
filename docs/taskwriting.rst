Writing Tasks
=============

What is a task?
---------------

A task is an ordinary Python script with some magical capabilities for looking into a LAF resource (a *compiled* LAF resource to be precise).

A task gets those capabilities because it is called by the workbench. In order to be called by the workbench, you have to put into the *tasks* directory, next to the example tasks.

The workbench passes an object to your task, which contains the information needed to peek into the LAF resource. Conversely, in your task script you can pass some initialization information to the workbench, so that it can build or load the appropriate indexes. 

Apart from these things, your script may contain arbitrary Python code, it may import arbitrary modules. The workbench is agnostic of your code.

A leading example
-----------------
Our target LAF resource is the conversion of a text database with objects to nodes with annotations. Nodes correspond to objects. The types of objects translate to annotations with label *db* with the feature *otype*. Likewise for the id of objects and the anchoring of objects to primary data: the features *minmonad*, *maxmonad* and *monads* take care of that. In the original LAF it looks like this::

    <node xml:id="n28737"><link targets="w_1 w_2 w_3 w_4 w_5 w_6 w_7 w_8 w_9 w_10 w_11"/></node>
    <a xml:id="al28737" label="db" ref="n28737"><fs>
        <f name="otype" value="clause"/>
        <f name="oid" value="28737"/>
        <f name="monads" value="1-11"/>
        <f name="minmonad" value="1"/>
        <f name="maxmonad" value="11"/>
    </fs></a>

The example task *object.py* lists all objects in "resource order" with their original ids, object types etc and even their node number in the compiled resource.
Not very useful, but handy for debugging or linking new annotation files to the existing data. Here is a snippet of output::

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

    # -*- coding: utf8 -*-

    precompute = {
        "plain": {},
        "memo": {},
        "assemble": {
            "only_nodes": "db:oid,otype,monads",
            "only_edges": '',
        },
        "assemble_all": {
        },
    }

    def task(graftask):
        (msg, Li, Lr, Ni, Nr, Vi, Vr, NN, NNFV, Fi, Fr) = graftask.get_mappings()

        out = graftask.add_result("output.txt")

        for i in NN():
            oid = Fr(i, Li["db"], Ni["oid"])
            otype = Fr(i, Li["db"], Ni["otype"])
            monads = Fr(i, Li["db"], Ni["monads"])
            out.write("{:>7} {:>7} {:<20} {{{:<13}}}\n".format(i, oid, otype, monads))

Information flow from task to workbench
---------------------------------------
The main thing the workbench needs to know about the task are directives for its processing. Remember that tasks can be run with different *flavours*.
A flavour is a way of optimizing tasks and it can be specified on the command line which flavour to use. A flavour may take some directives, such as
the indexes that have to be built, and the *precompute* dictionary is the place to specify the directives. 
Currently, only the *assemble* flavour needs any directives. It needs to be told for which features indexes should be built. This must be specified separately for features that occur on nodes and that occur on edges.

The feature specification takes the form of a space separated string of items of the form::

    «annotation label»:«feature names»

where ``«feature names»`` is a comma separated list of feature names. For all implied features ``«annotion label»:«feature name»`` an index will be created and saved if it does not already exist. If it exists already, it will be loaded.

.. caution:: Missing indexes.
    If you use the ``assemble`` flavour you **must** instruct the workbench to make indexes for all features that you use in your task. The workbench will always use indexes when retrieving feature values. If you forget to mention a feature in the directives, the workbench will deliver the value ``None``, even if the compiled LAF has a real value there. The reason for this behaviour is that it is to costly to let every feature lookup check whether the index exists.

Information flow from workbench to task
---------------------------------------
The workbench will call the function *task(object)* in your task script, and the thing that is passed to it as *object* is an object of class :class:`GrafTask <graf.task.GrafTask>`.
By using this object, you have to access all of its methods. 

In order to write an efficient task, it is convenient to import the names of the most important methods as *local variables* of the *task* function. The lookup of names in Python is fastest for local names. And it makes the code much cleaner.

The method :meth:`get_mappings() <graf.task.GrafTask.get_mappings>` delivers the methods, and it is up to you to give them names. It is recommended to stick to the names provided here in this example. Here is a short description of the corresponding methods.

*Fi()* and *Fr()*
    Feature value lookup functions.
    They need a node or edge, then an annotation label, then a feature name, and then they return the value.
    All arguments must be given as integers, the integers to which nodes and labels and names have been mapped during compiling.
    (There are ways to get those numbers).
    The difference between :meth:`Fi() <graf.task_plain.GrafTaskPlain.Fi>` and :meth:`Fr() <graf.task_plain.GrafTaskPlain.Fr>` is that
    :meth:`Fi() <graf.task_plain.GrafTaskPlain.Fi>` returns the internal number corresponding to the value,
    and :meth:`Fr() <graf.task_plain.GrafTaskPlain.Fr>` the original string value as encountered in the original LAF resource.
    Use :meth:`Fi() <graf.task_plain.GrafTaskPlain.Fi>` when the value is needed in other parts of your script,
    use :meth:`Fr() <graf.task_plain.GrafTaskPlain.Fr>` when you need to output values. 

*Li* and *Lr*
    Tables to convert between annotation labels as string values found in the original LAF and the integers they have been mapped to during compilation. *Li* yields integers from string representations, *Lr* yields representations (strings) from internal integers.

*Ni* and *Nr*
    Same pattern as above, but now for feature names.

*Vi* and *Vr*
    Same pattern as above, but now for feature values.

*NN()* and *NNFV()* are *iterators* that yield a new node everytime they are called. They yield the nodes in so-called *primary data order*, which will be explained below. The difference between *NN()* and *NNFV()* is that *NN()* iterates over absolutely all nodes, and *NNFV()* only yields node that have a certain value for a certain feature. See :class:`GrafTaskBase <graf.task_base>`, methods :meth:`nextnode() <graf.task_base.GrafTaskBase.next_node>` and :meth:`next_node_with_fval() <graf.task_base.GrafTaskBase.next_node_with_fval>`.

Output
------
You can create an output filehandle, open for writing, by calling the method :meth:`add_result() <graf.task_base.GrafTaskBase.add_result>` of the :class:`GrafTaskBase <graf.task_base>` class and assigning the result to a variable, say *out*.  From then on you can write output simply by saying::

    out.write(text)

You can create as many output handles as you like in this way. Once your task has finished, the workbench will close them all.

.. _node-order:

Node order
----------
There is an implicit partial order on nodes, derived from their attachment to *regions* which are stretches of primary data, and the primary data is totally ordered.
The order we use in the workbench is defined as follows.

Suppose we compare node *A* and node *B*. Look up all regions for *A* and for *B* and determine the first point of the first region and the last point of the last region for *A* and *B*, and call those points *Amin, Amax*, *Bmin, Bmax* respectively. 

Then region *A* comes before region *B* if and only if *Amin* < *Bmin* or *Amin* = *Bmin* and *Amax* > *Bmax*.

In other words: if *A* starts before *B*, then *A* becomes before *B*. If *A* and *B* start at the same point, the one that ends last, counts as the earlier of the two.

If neither *A* < *B* nor *B* < *A* then the order is not specified. The workbench will select an arbitrary but consistent order between thoses nodes. The only way this can happen is when *A* and *B* start and end at the same point. Between those points they might be very different. 

The nice property of this ordering is that if a set of nodes consists of a proper hierarchy with respect to embedding, the order specifies a walk through the nodes were enclosing nodes come first, and embedded children come in the order dictated by the primary data.

