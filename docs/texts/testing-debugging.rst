Testing and Debugging
#####################

If you are *not* on windows, you can test your installation in this way:

In the command prompt, go to the directory where *laf-fabric.py* resides::

    cd «path_to_dir_of_laf-fabric.py»

*single use mode* (not on Windows)::

    python laf-fabric.py --source=«source» --annox=«annox» --task=«task» [--force-compile-source] [--force-compile-annox]

If all of the ``«source»``, ``«annox»`` and ``«task»`` arguments are present and if the ``--menu`` argument is absent
LAF-fabric runs the specified task without asking and quits.

*re-use mode* (not on Windows)::

    python laf-fabric.py [--source=«source» ] [--annox=«annox»] [--task=«task» ] [--force-compile-source] [--force-compile-annox]

If some of the ``«source»``, ``«annox»`` and ``«task»`` arguments are missing or if the ``--menu`` argument is present
it starts in interactive mode prompting you for sources and commands to run tasks.
The ``«source»``, ``«annox»`` and ``«task»`` arguments that are given are used for initial values.
In interactive mode you can change your ``«source»``, ``«annox»`` and ``«task»`` selection, and run tasks.
There is a help command and the prompt is self explanatory.

Other options
-------------
``--force-compile-source`` and ``--force-compile-annox``
    If you have changed the LAF resource or the selected annotation package, LAF-fabric will detect it and recompile it.
    The detection is based on the modified dates of the GrAF header file and the compiled files.
    In cases where LAF-fabric did not detect a change, but you need to recompile, use this flag.
    In interactive mode, there is a command to force recompilation of the current source.

