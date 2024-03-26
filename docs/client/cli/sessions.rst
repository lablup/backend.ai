Compute Sessions
================

.. note::

   Please consult the detailed usage in the help of each command
   (use ``-h`` or ``--help`` argument to display the manual).


Listing sessions
----------------

List the session owned by you with various status filters.
The most recently status-changed sessions are listed first.
To prevent overloading the server, the result is limited to the first 10
sessions and it provides a separate ``--all`` option to paginate further
sessions.

.. code-block:: shell

  backend.ai ps

The ``ps`` command is an alias of the following ``admin session list`` command.
If you have the administrator privilege, you can list sessions owned by
other users by adding ``--access-key`` option here.

.. code-block:: shell

  backend.ai admin session list

Both commands offer options to set the status filter as follows.
For other options, please consult the output of ``--help``.

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Option
     - Included Session Status

   * - (no option)
     - ``PENDING``, ``PREPARING``, ``RUNNING``, ``RESTARTING``,
       ``TERMINATING``, ``RESIZING``, ``SUSPENDED``, and ``ERROR``.

   * - ``--running``
     - ``PREPARING``, ``PULLING``, and ``RUNNING``.

   * - ``--dead``
     - ``CANCELLED`` and ``TERMINATED``.

Both commands offer options to specify which fields of sessions should be printed as follows.

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Option
     - Included Session Fields

   * - (no option)
     - ``Name``, ``Owner Access Key (admin only)``, ``Session ID``, ``Project/Group``,

       ``Main Kernel ID``, ``Image``, ``Type``, ``Status``,

       ``Status Info``, ``Last Updated``, and ``Result``.


   * - ``--name-only``
     - ``Name``.

   * - ``--detail``
     - ``Name``, ``Session ID``, ``Project/Group``,

       ``Main Kernel ID``, ``Image``, ``Type``, ``Status``,

       ``Status Info``, ``Last Updated``, ``Result``, ``Tag``,

       ``Created At``, and ``Occupying Slots``.

   * - ``-f``, ``--format``
     - Specified fields by user.

.. note::
    Fields for ``-f/--format`` option can be displayed by specifying comma-separated parameters.

    Available parameters for this option are: ``id (session_id)``, ``main_kernel_id``, ``tag``, ``name``, ``type``, ``image``, ``registry``, ``cluster_template (reserved for future release)``, ``cluster_mode``, ``cluster_size``, ``domain_name``, ``group_name``, ``group_id``, ``agent_ids``, ``user_email``, ``user_id``, ``access_key``, ``status``, ``status_info``, ``status_changed``, ``created_at``, ``terminated_at``, ``starts_at``, ``scheduled_at``, ``startup_command``, ``result``, ``resource_opts``, ``scaling_group``, ``service_ports``, ``mounts``, ``occupying_slots``, ``dependencies``, ``abusing_reports``, ``idle_checks``.

    For example:

    .. code-block:: shell

        backend.ai admin session list --format id,status,occupying_slots

.. _simple-execution:

Running simple sessions
-----------------------

The following command spawns a Python session and executes
the code passed as ``-c`` argument immediately.
``--rm`` option states that the client automatically terminates
the session after execution finishes.

.. code-block:: shell

  backend.ai run --rm -c 'print("hello world")' python:3.6-ubuntu18.04

.. note::

   By default, you need to specify language with full version tag like
   ``python:3.6-ubuntu18.04``. Depending on the Backend.AI admin's language
   alias settings, this can be shortened just as ``python``. If you want
   to know defined language aliases, contact the admin of Backend.AI server.


The following command spawns a Python session and executes
the code passed as ``./myscript.py`` file, using the shell command
specified in the ``--exec`` option.

.. code-block:: shell

  backend.ai run --rm --exec 'python myscript.py arg1 arg2' \
             python:3.6-ubuntu18.04 ./myscript.py


Please note that your ``run`` command may hang up for a very long time
due to queueing when the cluster resource is not sufficiently available.

To avoid indefinite waiting, you may add ``--enqueue-only`` to return
immediately after posting the session creation request.

.. note::

   When using ``--enqueue-only``, the codes are *NOT* executed and relevant
   options are ignored.
   This makes the ``run`` command to the same of the ``start`` command.

Or, you may use ``--max-wait`` option to limit the maximum waiting time.
If the session starts within the given ``--max-wait`` seconds, it works
normally, but if not, it returns without code execution like when used
``--enqueue-only``.

To watch what is happening behind the scene until the session starts,
try ``backend.ai events <sessionID>`` to receive the lifecycle events
such as its scheduling and preparation steps.


Running sessions with accelerators
----------------------------------

Use one or more ``-r`` options to specify resource requirements when
using ``backend.ai run`` and ``backend.ai start`` commands.

For instance, the following command spawns a Python TensorFlow session
using a half of virtual GPU device, 4 CPU cores, and 8 GiB of the main
memory to execute ``./mygpucode.py`` file inside it.

.. code-block:: shell

  backend.ai run --rm \
             -r cpu=4 -r mem=8g -r cuda.shares=2 \
             python-tensorflow:1.12-py36 ./mygpucode.py


Terminating or cancelling sessions
----------------------------------

Without ``--rm`` option, your session remains alive for a configured
amount of idle timeout (default is 30 minutes).
You can see such sessions using the ``backend.ai ps`` command.
Use the following command to manually terminate them via their session
IDs.  You may specifcy multiple session IDs to terminate them at once.

.. code-block:: shell

  backend.ai rm <sessionID> [<sessionID>...]

If you terminate ``PENDING`` sessions which are not scheduled yet,
they are cancelled.
