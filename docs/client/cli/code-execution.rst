Advanced Code Execution
=======================

.. note::

   Please consult the detailed usage in the help of each command
   (use ``-h`` or ``--help`` argument to display the manual).


Running concurrent experiment sessions
--------------------------------------

In addition to single-shot code execution as described in
:ref:`simple-execution`, the ``run`` command offers concurrent execution of
multiple sessions with different parameters interpolated in the execution
command specified in ``--exec`` option and environment variables specified
as ``-e`` / ``--env`` options.

To define variables interpolated in the ``--exec`` option, use ``--exec-range``.
To define variables interpolated in the ``--env`` options, use ``--env-range``.

Here is an example with environment variable ranges that expands into 4
concurrent sessions.

.. code-block:: shell

  backend.ai run -c 'import os; print("Hello world, {}".format(os.environ["CASENO"]))' \
      -r cpu=1 -r mem=256m \
      -e 'CASENO=$X' \
      --env-range=X=case:1,2,3,4 \
      lablup/python:3.6-ubuntu18.04

Both range options accept a special form of argument: "range expressions".
The front part of range option value consists of the variable name used for
interpolation and an equivalence sign (``=``).
The rest of range expressions have the following three types:

.. list-table::
   :widths: 24 76
   :header-rows: 1

   * - Expression
     - Interpretation

   * - ``case:CASE1,CASE2,...,CASEN``
     - A list of discrete values. The values may be either string or numbers.

   * - ``linspace:START,STOP,POINTS``
     - An inclusive numerical range with discrete points, in the same way
       of ``numpy.linspace()``.  For example, ``linspace:1,2,3`` generates
       a list of three values: 1, 1.5, and 2.

   * - ``range:START,STOP,STEP``
     - A numerical range with the same semantics of Python's :func:`range`.
       For example, ``range:1,6,2`` generates a list of values:
       1, 3, and 5.

If you specify multiple occurrences of range options in the ``run``
command, the client spawns sessions for *all possible combinations* of all
values specified by each range.

.. note::

  When your resource limit and cluster's resource capacity cannot run all
  spawned sessions at the same time, some of sessions may be queued and the
  command may take a long time to finish.

.. warning::

  Until all cases finish, the client must keep its network connections to
  the server alive because this feature is implemented in the client-side.
  Server-side batch job scheduling is under development!
