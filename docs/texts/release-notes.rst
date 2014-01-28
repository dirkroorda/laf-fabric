Release Notes
#############
3.3.1
=====
Bugfix. Thanks to Grietje Commelin for spotting the bug so quickly. 
My apologies for any `tension <http://xkcd.com/859/>`_ it might have created in the meantime.
Better code under the hood: the identifiers for nodes, edges and regions now start at 0 instead of 1.
This reduces the need for many `` + 1`` and `` - 1`` operations, including the need to figure out
which one is appropriate.

3.3
===
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
=====
API
---
* API elements are now returned as named entries in a dictionary, instead of a list.
    In this way, the task code that calls the API and gives names to the elements remains more stable when elements
    are added to the API.

* Documentation: added release notes.

* New Example Notebook: `participle <http://nbviewer.ipython.org/github/dirkroorda/laf-fabric/blob/master/notebooks/participle.ipynb>`_.

Incompatible changes
^^^^^^^^^^^^^^^^^^^^
* :meth:`API() <laf.task.LafTask.API>` now returns a keyed dictionary instead of a 6-tuple.
    The statement where you define API is now 

        API = processor.API()
        F = API['F']
        NN = API['NN']
        ...

    (was::

        (msg, NN, F, C, X, P) = processor.API()

    )

3.2.0
=====
API
---
* Connectivity added to the API, see :ref:`connectivity`.
    There is an object C by which you can traverse from nodes via annotated edges to other nodes.

* Documentation organization:
    separate section for API reference.

Incompatible changes
^^^^^^^^^^^^^^^^^^^^
* :meth:`API() <laf.task.LafTask.API>` now returns a 6-tuple instead of a 5-tuple:
    C has been added.
* nodes or edges annotated by an empty annotation will get a feature based on the annotation label.
    This feature yields value ``''`` (empty string) for all nodes or edges for which it is defined. Was ``1``.
    **Existing LAF resources should be recompiled**.
