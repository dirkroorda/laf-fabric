Writing Tasks
=============

What is a task?
---------------

A task is an ordinary Python script with some magical capabilities
for looking into a LAF resource (a *compiled* LAF resource to be precise).

A task gets those capabilities because it is called by the workbench.
In order to be called by the workbench, you have to put into the *tasks* directory
(see :ref:`configuration <task_dir>`).

The workbench passes an object to your task,
which contains the information needed to peek into the LAF resource.
Conversely, in your task script you can pass some initialization information to the workbench,
so that it can build or load the appropriate feature data. 

Apart from these things, your script may contain arbitrary Python code,
it may import arbitrary modules.
The workbench is agnostic of your code.

A leading example
-----------------
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
----------------
When the workbench compiles features into binary data, it forgets the annotations in which the features come,
but the annotation *label* is retained as a prefix to the feature name.
In the example above, you see an annotation with label ``db`` and in it a feature structure
with features named ``otype``, ``oid``, etc.
The workbench remembers those features by their *fully qualified* names: ``db.otype``, ``db.oid`` etc.
There may also be annotations without feature contents. Such annotations will be stored as features with as name the 
annotation label only, without the dot: ``db``.

.. note::
	Annotations may reference nodes or edges.
	It is possible that nodes and edges have features with the same name. 
	However, the workbench maintains a strict distinction between features
	of nodes and features of edges. They have separate name spaces, implicitly.
	The API has different methods to the address the features of nodes and edges.
	And features names that are used for nodes and edges may coexist, but their
	internal representations are separate tables.

The example task *object.py* lists all objects in "resource order" with their original ids,
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

	features = {
		"node": "db:oid,otype,monads",
		"edge": '',
	}

	def task(graftask):
		(msg, Ni, Nr, Vi, Vr, NN, NNFV, FNi, FNr, FEi, FEr) = graftask.get_mappings()

		out = graftask.add_result("output.txt")

		for i in NN():
			oid = FNr(i, Ni["db.oid"])
			otype = FNr(i, Ni["db.otype"])
			monads = FNr(i, Ni["db.monads"])
			out.write("{:>7} {:>7} {:<20} {{{:<13}}}\n".format(i, oid, otype, monads))


Information flow from task to workbench
---------------------------------------
The main thing the workbench needs to know about the task are directives for its processing.
The task needs to be told for which features data should be loaded.
This must be specified separately for features that occur on nodes and that occur on edges.

The feature specification takes the form of a space separated string of items of the form::

    «annotation label»:«unqualified feature names»

where ``«unqualified feature names»`` is a comma separated list of feature names without annotation labels.
For all implied features ``«annotion label»:«feature name»`` data will be loaded.
For all other features data will be unloaded, if still loaded.

.. caution:: Missing feature data.

    If you forget to mention a feature in the directives,
	the workbench will deliver the value ``None``,
	even if the compiled LAF has a real value there.
    The reason for this behaviour is that it is to costly
	to let every feature lookup check whether its data has been loaded.

Information flow from workbench to task
---------------------------------------
The workbench will call the function *task(object)* in your task script,
and the thing that is passed to it as *object* is an object of
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

*FNi()* and *FNr()*, *FEi()* and *FEr()*
	The *FNx* versions need a node, the *FEx* versions and edge,
	then they need an a qualified feature name.
	They return the value that the feature carries on that node or edge.
	The *FXi* versions return the value code that the compiler has assigned
	to the real value (read *i* as *internal*).
	The *FXr* versions return the real values as strings, exactly as
	they appear in the original LAF resource (read *r* as *real*).

	All arguments must be given as integers,
	the integers to which nodes and labels and names have been mapped during compiling.
	(There are ways to get those numbers).
	Use *FXi* versions when the value is needed in other parts of your script,
	and the *FXr* versions when you need to output values. 

*Ni* and *Nr*
    Tables to convert between qualified feature names as real values
	found in the original LAF and the integers they have been mapped to during compilation.
	*Ni* yields integers from string representations,
	*Nr* yields representations (strings) from internal integers.

*Vi* and *Vr*
    Same pattern as above, but now for feature values.

*NN()* and *NNFV()*
	*iterators* that yield a new node everytime they are called.
	They yield the nodes in so-called *primary data order*, which will be explained below.
	The difference between *NN()* and *NNFV()* is
	that *NN()* iterates over absolutely all nodes,
	and *NNFV()* only yields node that have a certain value for a certain feature.
	See :class:`GrafTask <graf.task>`,
	methods :meth:`nextnode() <graf.task.GrafTask.next_node>`
	and :meth:`next_node_with_fval() <graf.task.GrafTask.next_node_with_fval>`.

Output
------
You can create an output filehandle, open for writing, by calling the
method :meth:`add_result() <graf.task.GrafTask.add_result>`
of the :class:`GrafTask <graf.task>` class
and assigning the result to a variable, say *out*.
From then on you can write output simply by saying::

    out.write(text)

You can create as many output handles as you like in this way.
Once your task has finished, the workbench will close them all.

.. _node-order:

Node order
----------
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

