Release Notes
#############
Upcoming
========
Mainly in the *etcbc* packages.

Current
=======
4.3.3
-----
The transliteration in *etcbc.lib* which converts between Hebrew characters and transliterated latin characters, has been extended to deal with
vowel pointings and accents too.

4.3.1
-----
The module *etcbc.px* retrieves one more field, called *instruction* from the *px* files.

4.3
---
Changes in the annotation space, a new *etcbc.px* which can read certain types of *px* data and transform it into an extra LAF annotation package.

Incompatible changes
^^^^^^^^^^^^^^^^^^^^
Due to the new names for edge features, the data for BHS3 and BHS4 has been recompiled, and all tasks that use the old names have to be updated.

4.2.15
------
A few changes in etcbc.emdros2laf: edge annotations are no longer empty annotations, but have a feature structure.

4.2.14
------
A few changes in etcbc.emdros2laf, which facilitates generating feature declaration documents.

4.2.13
------
In the API you can ask for the locations of the data directory and the output directory.

4.2.12
------
LAF-Fabric reports the date and time when it has loaded data for a task.
So in every notebook you can see the version of LAF-Fabric, the datetime when the loaded data has been compiled,
and the datetime when this data has been loaded for this task.
This is handy when you share tasks via nbviewer.

4.2.11
------
New API element *EE*, which yield all edges in unspecified order.
The module *featuredoc* can now document all features, also edge features.

4.2.10
------
Separated the data directory *laf-fabric-data* into an input directory (*laf-fabric-data*) and an output directory (*laf-fabric-output*).
In this way, it is easier to download new versions of the data without overwriting your own task results.

4.2.9
-----
Minor improvements in the emdros2laf conversion, discovered when converting the new BHS4 version of the Hebrew Text database.
If you want to use the BHS4 data (beta), `download <https://www.dropbox.com/s/1oqvb92sqn7vuml/laf-fabric-data.zip>`_ the data again.

4.2.8
-----
Minor improvements in the laf-api.

Past
====
4.2.7
-----
API
^^^
Added *NK*, which can be passed as a sort key for node sets. It corresponds with the "natural order" on nodes.
If an additional module, such as *etcbc.preprocess* has modified the natural order, this sort key will reflect the
modified order. If you let NN() yield nodes, they appear in this same order.

Also added *MK*, which can be passed as a sort key for sets of anchors. It corresponds with the "natural order" on
anchor sets.

ETCBC
^^^^^
Improvements in *etcbc.trees*, the module that generates trees from the ETCBC database.

4.2.6
-----
Developed the *etcbc.trees* module further.
Trees based on the implicit embedding relationship do not exhibit all embedding structure:
clauses can be further embedded by means of an explicit *mother* relationship.
The rules are a bit intricate, but it has been implemented (BHS3 only, no CALAP).
See the updates `trees <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/trees/trees_bhs.ipynb>`_ notebook.

4.2.5
-----
Added tree defining functionality to the etcbc package: *etcbc.trees*.
You can make the implicit embedding relationship between objects explicit by means of parent and children relationships.

Adapted the node order as customized by *etcbc.preprocess*: the order is now a total ordering.
Main idea: try to order monad sets by the subset relation, where embedder comes before embedded.
If the sets are equal, use the object type to force a decision.
If two monad sets cannot be ordered by the subset relation, look at the elements that they do *not* share.
The monad set that contains the smallest of these elements, is considered to come before the other.

4.2.4
-----
Added Syriac transcription conversions.

4.2.3
-----
In *emdros2laf* every source can now have its own metadata.
In *etcbc* there is a workable definition between consonantal Hebrew characters and their ETCBC latin transcriptions.

4.2.2
-----
More fixes in *emdros2laf*, a new source, the *CALAP* has been converted to LAF.
LAF-Fabric has compiled it, and it is ready for exploration.
See the example notebook
`plain-calap <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/syriac/plain_calap.ipynb>`_.
The CALAP is included in the data download (see :doc:`getting-started`).

4.2.1
-----
Small fixes in *emdros2laf*.

4.2
---
LAF Usability
^^^^^^^^^^^^^
The conversion program from EMDROS to LAF (now the package *emdros2laf*) has been integrated in LAF-Fabric.
Because of this a small reorganization of subdirectories was necessary (again).
The EMDROS source of the LAF has a place in *laf-fabric-data* as well.
So: again: a new download of the data is required.

4.1.4
-----
LAF Usability
^^^^^^^^^^^^^
Small reorganization of subdirectories. The structure is now better adapted to work with completely different data sources.
Update your configuration files. The trailing directory names must be removed. So::

    work_dir = ~/laf-fabric-data/etcbc-bhs

should change into::

    work_dir = ~/laf-fabric-data

Same for ``laf-dir``.

Because of this reorganization you have to download the data again.

4.1.3
-----
Small fixes.

4.1.2
-----
LAF Usability
^^^^^^^^^^^^^
Small usability improvements in ``etcbc`` and in ``laf``.

4.1.1
-----
LAF Usability
^^^^^^^^^^^^^
After loading LAF-Fabric display the compilation data and time of the data used.

4.1
---
ETCBC Emdros integration
^^^^^^^^^^^^^^^^^^^^^^^^
In the *etcbc* package there is a module *mql* that enables the user to run emdros queries, capture the results as a node set, and use that for
further processing in LAF-Fabric.
See `notebook MQL <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/querying/MQL.ipynb>`_

4.0.6
-----
API
^^^
In specifying what features to load, you may omit namespaces and labels.
You can specify the features to load in a much less verbose way.

The functions ``load()`` and ``load_again()`` have a new optional parameter ``add``, which instructs laf fabric to
do an incremental loading, without discarding anything that has already been loaded.

ETCBC
^^^^^
The order defined by ``etcbc.preprocess`` has been refined, so that it can also deal with empty words. 

Under the hood
^^^^^^^^^^^^^^
More unit tests, especially w.r.t. node order and empty words.
The example data on which the unit tests act, has been enlarged: it now contains also Isaiah 41:19 in which two empty words occur.

4.0.5
-----
Usability
^^^^^^^^^
Better error handling, especially when the load dictionary does not conform to the specs of the API reference.

Under the hood
^^^^^^^^^^^^^^
More unit tests, especially w.r.t. error checking, and node order, and the ``BF`` API element.

4.0.4
-----
API
^^^
The special edge features for all annotated edges and unannotated edges are now called ``laf:.y`` and ``laf:.x``, because otherwise
their names become private method names in Python.

Under the hood
--------------
More unit tests.

Incompatible changes
--------------------
Because of the renaming of special edge features, a new copy of the data is needed. Download the latest version.

4.0.3
-----
API
^^^
The methods of the connectivity objects (except ``e()`` yield all iterators and have an optional parameter ``sort=False``.  
The API elements now can be added very easily to your local namespace by saying: ``exec(Fabric.localnames.format(var='Fabric'))``.

4.0.2
-----
API
^^^
For connectivity there is a new API method: ``C.feature.e(n)``. This returns ``True`` if and only if 
``n`` is connected to a node by means of an edge annotated with ``feature``. 
This function can also be obtained by using ``C.feature.v(n)``, but the direct ``e(n)`` is much more efficient.

Usability
^^^^^^^^^
When calling up features as in ``F_shebanq_ft_part_of_speech``, you may now leave out the namespace and also the label.
So ``F.part_of_speech`` also works.

4.0.1
-----
Small bug fixes.

4.0
---
API
^^^
The API has changed for initializing the processor and for working with connectivity (``C`` and ``Ci``).
Please consult :doc:`API-reference`.

Usability
^^^^^^^^^
* There is an example dataset included: Genesis 1:1 according to the ETCBC database.
* Configuration is easier: a global config file in your home directory.
* There is a *laf-fabric-test.py* script for a basic test.

Incompatible changes
^^^^^^^^^^^^^^^^^^^^
More data has been precompiled. This reduces the load time when working with LAF-Fabric.
The data organization has changed. Please download a new version of the data.

Configuration is easier now. A single config file in your home directory is sufficient.
There are also other ways, including a config file next to your notebook.

Changes under the hood
^^^^^^^^^^^^^^^^^^^^^^
* The mechanism to store and load LAF data now has a hook by which auxiliary modules can register new data with LAF Fabric.
  Currently, this mechanism is used by the ``etcbc`` module to inject a better ordering of the nodes than LAF Fabric can generate on its own.
  In future versions we will use this mechanism to load compute and load extra indices needed for working with the EMDROS database.
* Unit tests. In the file *lf-unittest.py* there are now several unit tests. If they pass most things in LAF-Fabric are working as expected.
  However, the set needs to be enlarged before new changes are undertaken.

3.7
---
API
^^^
* You can make additional sorting persistent now, so that it becomes part of the compiled data. See the ``prep`` function in the API reference.

Usability
^^^^^^^^^
* It is possible to set a verbosity level for messages.
* There were chunks of time consuming data that were either completely or often unnecessary. This data has been removed, or is loadable on demand respectively.
  Overall performance during load time is a bit better now.  

Extra's
^^^^^^^
The *etcbc* module has a method to compute a better ordering on the nodes. 
This module works together with the new API method to store computed results.

3.6
---
API
^^^
There is a significant addition for dealing with the order of nodes:

* New function ``BF(nodea, nodeb)`` for node comparison.
  Handy to find the nodes that cannot be ordered because they have the same start points and end points in the primary data.
* New argument to ``NN()`` for additionally sorting those enumerated nodes that have the same start points and end points in the primary data.

Incompatible changes
^^^^^^^^^^^^^^^^^^^^
* The representation of node anchors has changed.
  **Existing LAF resources should be recompiled**.

Usability
^^^^^^^^^
When LAF-Fabric starts it shows a banner indicating its version.

3.5.1
-----
Bugfixes
^^^^^^^^
Opening and closing of files was done without specifying explicitly the ``utf-8`` encoding.
Python then takes the result of ``locale.getprefferredencoding()`` which may not be ``utf-8`` on some systems,
notably Windows ones.

Remedy: every ``open()`` call for a text file is now passed the ``encoding='utf-8'`` parameter.
``open()`` calls for binary files do not get an encoding parameter of course.

3.5
---
Usability
^^^^^^^^^
Code supporting ETCBC notebooks has moved into separate package *etcbc*, included in the laf distribution.

3.4.1
-----
Usability
^^^^^^^^^
When loading data in a notebook, the progress messages are far less verbose.

API
^^^
Added an introspection facility: you can ask the *F* object which features are loadable.

3.4
---
API
^^^
Changes in the way you refer to input and output files.
You had to call them as methods on the ``processor`` object, now they are given with the ``API()`` call,
like the ``msg()`` method.

Bugfixes
^^^^^^^^
Under some conditions XML identifiers got mistakenly unloaded.
Fixed by modifying the big table with conditions in ``check_load_status`` in ``laf.laf``.

3.3.7
-----
Usability
^^^^^^^^^
Configuration fix: the LAF source directory can be anywhere on the system, specified by an *optional* config setting.
If this setting is not specified, LAF-Fabric works with a binary source only.

A download link to the data is provided, it is a dropbox link to a zipped file with a password.
You can ask `me <mailto:dirk.roorda@dans.knaw.nl>`_ for a password.

Focus on working with notebooks. Command line usage only supported for testing and debugging, not on Windows.

Documentation
^^^^^^^^^^^^^
Thoroughly reorganized and adapted to latest changes.

Notebooks
^^^^^^^^^
This distribution only contains example tasks and notebooks.
The real stuff can be found in the `ETCBC repository <https://github.com/ETCBC/laf-fabric-nbs>`_
and in a `study repo <https://github.com/ETCBC/study>`_ maintained by Judith Gottschalk.

3.3.6
-----
Usability
^^^^^^^^^
The configuration file, *laf-fabric.cfg* will no longer be distributed. Instead, a file *laf-fabric-sample.cfg* will be
distributed. You have to copy it to *laf-fabric.cfg* which you can adapt to your local situation.
Subsequent updates will not affect your local settings.

3.3.5
-----
API
^^^
New methods to find top most and bottom most nodes when traveling from a node set along annotated edges.
See :ref:`connectivity`.

3.3.4
-----
Notebook additions only.

The notebook `clause_constituent_relation <http://nbviewer.ipython.org/github/ETCBC/study/blob/master/notebooks/clause_constituent_relation.ipynb>`_
is an example how you can investigate a LAF data source and document your findings.

We intend to create a separate github dedicated to notebooks that specifically analyse the Hebrew Text Database.

3.3.3
-----
Other
^^^^^
Bugfixes: Data loading, unloading, keeping data better adapted to circumstances.

3.3.2
-----
API
^^^
* New API element ``Ci`` for connectivity.
    There is a new object ``Ci`` analogous to ``C`` by which you can traverse from nodes via annotated edges to other nodes.
    The difference is that ``Ci`` uses the edges in the opposite direction.
    See :ref:`connectivity`.
 
Incompatible changes
^^^^^^^^^^^^^^^^^^^^
Bugfix. The order of node events turned out wrong in the case of nodes that are linked to point regions,
i.e. regions with zero width (e.g. ``(n, n)``, being the point between characters ``n-1`` and ``n``).
This caused weird behaviour in the tree generating notebook
`trees (rough path) <http://nbviewer.ipython.org/github/ETCBC/laf-fabric/blob/master/examples/trees-r.ipynb>`_.

Yet it is impossible to guarantee natural behaviour in all cases.
If there are nodes linked to empty regions in your LAF resource, you should sort the node events per anchor yourself,
in your custom task.
**Existing LAF resources should be recompiled**.

Other
^^^^^
The `trees (smooth path) <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/trees/trees.ipynb>`_
notebook is evolving to get nice syntax trees from the Hebrew database.

3.3.1
-----
Bugfix. Thanks to Grietje Commelin for spotting the bug so quickly. 
My apologies for any `tension <http://xkcd.com/859/>`_ it might have created in the meantime.
Better code under the hood: the identifiers for nodes, edges and regions now start at 0 instead of 1.
This reduces the need for many ``+ 1`` and ``- 1`` operations, including the need to figure out
which one is appropriate.

3.3
^^^
API
---
* Node events are added to the API, see :ref:`node-events`. With ``NE()`` you traverse the anchor positions in the primary data,
  and at each anchor position there is a list of which nodes start, end, resume or suspend there.
  This helps greatly if your task needs the embedding structure of nodes.
  There are facilities to suppress certain sets of node events.

Incompatible changes
^^^^^^^^^^^^^^^^^^^^
* Node events make use of new data structures that are created when the LAF resource is being compiled.
  **Existing LAF resources should be recompiled**.

3.2.1
-----
API
^^^
* API elements are now returned as named entries in a dictionary, instead of a list.
    In this way, the task code that calls the API and gives names to the elements remains more stable when elements
    are added to the API.

* Documentation: added release notes.

* New Example Notebook: `participle <http://nbviewer.ipython.org/github/ETCBC/laf-fabric-nbs/blob/master/lingvar/participle.ipynb>`_.

Incompatible changes
^^^^^^^^^^^^^^^^^^^^
* ``API()`` in  ``laf.task`` now returns a keyed dictionary instead of a 6-tuple.
    The statement where you define API is now 

        API = processor.API()
        F = API['F']
        NN = API['NN']
        ...

    (was::

        (msg, NN, F, C, X, P) = processor.API()

    )

3.2.0
-----
API
^^^
* Connectivity added to the API, see :ref:`connectivity`.
    There is an object C by which you can traverse from nodes via annotated edges to other nodes.

* Documentation organization:
    separate section for API reference.

Incompatible changes
^^^^^^^^^^^^^^^^^^^^
* ``API()`` in  ``laf.task`` now returns a 6-tuple instead of a 5-tuple:
    C has been added.
* nodes or edges annotated by an empty annotation will get a feature based on the annotation label.
    This feature yields value ``''`` (empty string) for all nodes or edges for which it is defined. Was ``1``.
    **Existing LAF resources should be recompiled**.
