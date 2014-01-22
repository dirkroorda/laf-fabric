Release Notes
#############
3.2.1
=====
API
---
* API elements are now returned as named entries in a dictionary, instead of a list.
    In this way, the task code that calls the API and gives names to the elements remains more stable when elements
    are added to the API.

* Documentation: added release notes.

Incompatible changes
^^^^^^^^^^^^^^^^^^^^
* :meth:`API() <laf.task.LafTask.API>` now returns a keyed dictionary instead of a 6-tuple.
    The statement where you define API names must be changed from::

        (msg, NN, F, C, X, P) = processor.API()

    to::

        API = processor.API()
        F = API['F']
        NN = API['NN']

   etc.

3.2.0
=====
API
---
* Connectivity added to the API.
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
