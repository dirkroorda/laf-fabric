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
Our target LAF resource is the conversion of a text database with objects to nodes with annotations. Nodes correspond to objects. The types of objects translate to annotations with label ``db`` with the feature ``otype``. Likewise for the id of objects and the anchoring of objects to primary data: the features ``minmonad``, ``maxmonad`` and ``monads`` take care of that. In the original LAF it looks like this::

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

Note the same clause object ``28737`` as in the original LAF file.
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
the indexes that have to be built, and the ``precompute`` dictionary is the place to specify the directives. 
Currently, only the ``assemble`` flavour needs any directives. It needs to be told for which features indexes should be built. This must be specified separately for features that occur on nodes and that occur on edges.

The feature specification takes the form of a space separated string of items of the form::

    «annotation label»:«feature names»

where ``«feature names»`` is a comma separated list of feature names. For all implied features ``«annotion label»:«feature name»`` an index will be created and saved if it does not already exist. If it exists already, it will be loaded.

.. caution:: Missing indexes.
    If you use the ``assemble`` flavour you **must** instruct the workbench to make indexes for all features that you use in your task. The workbench will always use indexes when retrieving feature values. If you forget to mention a feature in the directives, the workbench will deliver the value ``None``, even if the compiled LAF has a real value there. The reason for this behaviour is that it is to costly to let every feature lookup check whether the index exists.

Information flow from workbench to task
---------------------------------------
The workbench will call the function ``task(object)`` in your task script, and the thing that is passed to it as ``object`` is an object of class ``GrafTask`` (see :class:`graf.task`). By using this object, you have to access all of its methods. 

In order to write an efficient task, it is convenient to import the names of the most important methods as *local variables* of the ``task`` function. The lookup of names in Python is fastest for local names. And it makes the code much cleaner.

The method ``get_mappings`` delivers the methods, and it is up to you to give them names. It is recommended to stick to the names provided here in this example. Here is a short description of the corresponding methods.

``Fi`` and ``Fr``

