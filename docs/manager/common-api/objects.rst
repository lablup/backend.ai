JSON Object References
======================

.. _paging-query-object:

Paging Query Object
-------------------

It describes how many items to fetch for object listing APIs.
If ``index`` exceeds the number of pages calculated by the server, an empty list is returned.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``size``
     - ``int``
     - The number of items per page.
       If set zero or this object is entirely omitted, all items are returned and ``index`` is ignored.
   * - ``index``
     - ``int``
     - The page number to show, zero-based.

.. _paging-info-object:

Paging Info Object
------------------

It contains the paging information based on the paging query object in the request.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``pages``
     - ``int``
     - The number of total pages.
   * - ``count``
     - ``int``
     - The number of all items.

.. _keypair-item-object:

KeyPair Item Object
-------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``accessKey``
     - ``slug``
     - The access key part.
   * - ``isActive``
     - ``bool``
     - Indicates if the keypair is active or not.
   * - ``totalQueries``
     - ``int``
     - The number of queries done via this keypair. It may have a stale value.
   * - ``created``
     - ``datetime``
     - The timestamp when the keypair was created.

.. _keypair-props-object:

KeyPair Properties Object
-------------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``isActive``
     - ``bool``
     - Indicates if the keypair is activated or not.
       If not activated, all authentication using the keypair returns 401 Unauthorized.
       When changed from ``true`` to ``false``, existing running sessions continue to run but any requests to create new sessions are refused.
       (default: ``true``)
   * - ``concurrecy``
     - ``int``
     - The maximum number of concurrent sessions allowed for this keypair.
       (default: ``5``)
   * - ``ML.clusterSize``
     - ``int``
     - Sets the number of instances clustered together when launching new machine learning sessions. (default: ``1``)
   * - ``ML.instanceMemory``
     - ``int`` (MiB)
     - Sets the memory limit of each instance in the cluster launched for new machine learning sessions. (default: ``8``)

The enterprise edition offers the following additional properties:

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``cost.automatic``
     - ``bool``
     - If set ``true``, enables automatic cost optimization (BETA).
       With supported kernel types, it automatically suspends or resize the sessions not to exceed the configured cost limit per day.
       (default: ``false``)
   * - ``cost.dailyLimit``
     - ``str``
     - The string representation of money amount as decimals.
       The currency is fixed to USD. (default: ``"50.00"``)

.. _service-port-object:

Service Port Object
-------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``name``
     - ``slug``
     - The name of service provided by the container.
       See also: :ref:`service-ports`
   * - ``protocol``
     - ``str``
     - The type of network protocol used by the container service.

.. _batch-execution-query-object:

Batch Execution Query Object
----------------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``build``
     - ``str``

     - The bash command to build the main program from the given uploaded files.

       If this field is not present, an empty string or ``null``, it skips the build step.

       If this field is a constant string ``"*"``, it will use a default build script provided
       by the kernel.
       For example, the C kernel's default Makefile adds all C source files
       under the working directory and copmiles them into ``./main``
       executable, with commonly used C/link flags: ``"-pthread -lm -lrt -ldl"``.

   * - ``exec``
     - ``str``

     - The bash command to execute the main program.

       If this is not present, an empty string, or ``null``, the server only
       performs the build step and ``options.buildLog`` is assumed to be
       ``true`` (the given value is ignored).

   * - ``clean``
     - ``str``

     - The bash command to clean the intermediate files produced during the build phase.
       The clean step comes *before* the build step if specified so that the build step
       can (re)start fresh.

       If the field is not present, an empty string, or ``null``, it skips the clean step.

       Unlike the build and exec command, the default for ``"*"`` is do-nothing
       to prevent deletion of other files unrelated to the build by bugs or
       mistakes.

.. note::

   A client can distinguish whether the current output is from the build phase
   or the execution phase by whether it has received ``build-finished`` status
   or not.

.. note::

   All shell commands are by default executed under ``/home/work``.
   The common environment is:

   .. code-block:: text

      TERM=xterm
      LANG=C.UTF-8
      SHELL=/bin/bash
      USER=work
      HOME=/home/work

   but individual kernels may have additional environment settings.

.. warning::

   The shell does NOT have access to sudo or the root privilege.
   Though, some kernels may allow installation of language-specific packages in
   the user directory.

   Also, your build script and the main program is executed inside
   Backend.AI Jail, meaning that some system calls are blocked by our policy.
   Since ``ptrace`` syscall is blocked, you cannot use native debuggers
   such as gdb.

   This limitation, however, is subject to change in the future.

Example:

.. code-block:: json

   {
     "build": "gcc -Wall main.c -o main -lrt -lz",
     "exec": "./main"
   }


.. _execution-result-object:

Execution Result Object
-----------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description

   * - ``runId``
     - ``str``
     - The user-provided run identifier.
       If the user has NOT provided it, this will be set by the API server upon the first execute API call.
       In that case, the client should use it for the subsequent execute API calls during the same run.

   * - ``status``
     - ``enum[str]``

     - One of ``"continued"``, ``"waiting-input"``, ``"finished"``, ``"clean-finished"``, ``"build-finished"``,
       or ``"exec-timeout"``.
       See more details at :ref:`code-execution-model`.

   * - ``exitCode``
     - ``int | null``
     - The exit code of the last process.
       This field has a valid value only when the ``status`` is ``"finished"``, ``"clean-finished"`` or ``"build-finished"``.
       Otherwise it is set to ``null``.

       For batch-mode kernels and query-mode kernels *without* global context support,
       ``exitCode`` is the return code of the last executed child process in the kernel.
       In the execution step of a batch mode run, this is always 127 (a UNIX shell common practice for "command not found")
       when the build step has failed.

       For query-mode kernels with global context support, this value is always zero,
       regardless of whether the user code has caused an exception or not.

       A negative value (which cannot happen with normal process termination) indicates a Backend.AI-side error.

   * - ``console``
     - ``list[object]``

     - A list of :ref:`console-item-object`.

   * - ``options``
     - ``object``

     - An object containing extra display options.  If there is no options indicated by the kernel, this field is ``null``.
       When ``result.status`` is ``"waiting-input"``, it has a boolean field ``is_password`` so that you could use
       different types of text boxes for user inputs.

   * - ``files``
     - ``list[object]``

     - A list of :ref:`execution-result-file-object` that represents files
       generated in ``/home/work/.output`` directory of the
       container during the code execution .

.. _console-item-object:

Console Item Object
-------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description

   * - (root)
     - ``[enum, *]``
     - A tuple of the item type and the item content.
       The type may be ``"stdout"``, ``"stderr"``, and others.

       See more details at :ref:`handling-console-output`.


.. _execution-result-file-object:

Execution Result File Object
----------------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description

   * - ``name``
     - ``str``
     - The name of a created file after execution.

   * - ``url``
     - ``str``
     - The URL of a create file uploaded to AWS S3.

.. _container-stats-object:

Container Stats Object
----------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``cpu_used``
     - ``int`` (msec)
     - The total time the kernel was running.
   * - ``mem_max_bytes``
     - ``int`` (Byte)
     - The maximum memory usage.
   * - ``mem_cur_bytes``
     - ``int`` (Byte)
     - The current memory usage.
   * - ``net_rx_bytes``
     - ``int`` (Byte)
     - The total amount of received data through network.
   * - ``net_tx_bytes``
     - ``int`` (Byte)
     - The total amount of transmitted data through network.
   * - ``io_read_bytes``
     - ``int`` (Byte)
     - The total amount of received data from IO.
   * - ``io_write_bytes``
     - ``int`` (Byte)
     - The total amount of transmitted data to IO.
   * - ``io_max_scratch_size``
     - ``int`` (Byte)
     - Currently not used field.
   * - ``io_write_bytes``
     - ``int`` (Byte)
     - Currently not used field.

.. _creation-config-object:

Creation Config Object
----------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description

   * - ``environ``
     - ``object``
     - A dictionary object specifying additional environment variables.
       The values must be strings.

   * - ``mounts``
     - ``list[str]``
     - An optional list of the name of virtual folders that belongs to the current API key.
       These virtual folders are mounted under ``/home/work``.
       For example, if the virtual folder name is ``abc``, you can access it on
       ``/home/work/abc``.

       If the name contains a colon in the middle, the second part of the string indicates
       the alias location in the kernel's file system which is relative to ``/home/work``.

       You may mount up to 5 folders for each session.

   * - ``clusterSize``
     - ``int``
     - The number of instances bundled for this session.

   * - ``resources``
     - :ref:`resource-slot-object`
     - The resource slot specification for each container in this session.

       .. versionadded:: v4.20190315

   * - ``instanceMemory``
     - ``int`` (MiB)
     - The maximum memory allowed per instance.
       The value is capped by the per-kernel image limit.
       Additional charges may apply on the public API service.

       .. deprecated:: v4.20190315

   * - ``instanceCores``
     - ``int``
     - The number of CPU cores.
       The value is capped by the per-kernel image limit.
       Additional charges may apply on the public API service.

       .. deprecated:: v4.20190315

   * - ``instanceGPUs``
     - ``float``
     - The fraction of GPU devices (1.0 means a whole device).
       The value is capped by the per-kernel image limit.
       Additional charges may apply on the public API service.

       .. deprecated:: v4.20190315

.. _resource-slot-object:

Resource Slot Object
--------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description

   * - ``cpu``
     - ``str | int``
     - The number of CPU cores.

   * - ``mem``
     - ``str | int``
     - The amount of main memory in bytes.
       When the slot object is used as an input to an API,
       it may be represented as binary numbers using the binary scale suffixes
       such as *k*, *m*, *g*, *t*, *p*, *e*, *z*, and *y*, e.g., "512m", "512M",
       "512MiB", "64g", "64G", "64GiB", etc.
       When the slot object is used as an output of an API, this field is
       **always** represented in the unscaled number of bytes as strings.

       .. warning::

          When parsing this field as JSON, you must check whether your JSON
          library or the programming language supports large integers.
          For instance, most modern Javascript engines support up to
          :math:`2^{53}-1` (8 PiB -- 1) which is often defined as the
          ``Number.MAX_SAFE_INTEGER`` constant.
          Otherwise you need to use a third-party big number calculation
          library.  To prevent unexpected side-effects, Backend.AI always
          returns this field as a string.

   * - ``cuda.device``
     - ``str | int``
     - The number of CUDA devices.
       Only available when the server is configured to use the CUDA agent plugin.

   * - ``cuda.shares``
     - ``str``
     - The virtual share of CUDA devices represented as fractional decimals.
       Only available when the server is configured to use the CUDA agent plugin
       with the fractional allocation mode (enterprise edition only).

   * - ``tpu.device``
     - ``str | int``
     - The number of TPU devices.
       Only available when the server is configured to use the TPU agent plugin
       (cloud edition only).

   * - (others)
     - ``str``
     - More resource slot types may be available depending on the server configuration
       and agent plugins.
       There are two types for an arbitrary slot: "count" (the default) and "bytes".

       For "count" slots, you may put arbitrary positive real number there,
       but fractions may be truncated depending on the plugin implementation.

       For "bytes" slots, its interpretation and representation follows that of
       the ``mem`` field.

.. _resource-preset-object:

Resource Preset Object
----------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description

   * - ``name``
     - ``str``
     - The name of this preset.

   * - ``resource_slots``
     - :ref:`resource-slot-object`
     - The pre-configured combination of resource slots.
       If it contains slot types that are not currently used/activated in the cluster,
       they will be removed when returned via ``/resource/*`` REST APIs.

   * - ``shared_memory``
     - ``int`` (Byte)
     - The pre-configured shared memory size.
       Client can send humanized strings like '2g', '128m', '534773760', etc,
       and they will be automatically converted into bytes.

.. _vfolder-creation-result-object:

Virtual Folder Creation Result Object
-------------------------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``id``
     - ``UUID``
     - An internally used unique identifier of the created vfolder.
       Currently it has no use in the client-side.
   * - ``name``
     - ``str``
     - The name of created vfolder, as the client has given.
   * - ``host``
     - ``str``
     - The host name where the vfolder is created.
   * - ``user``
     - ``UUID``
     - The user who has the ownership of this vfolder.
   * - ``group``
     - ``UUID``
     - The group who is the owner of this vfolder.

.. versionadded:: v4.20190615

   ``user`` and ``group`` fields.

.. _vfolder-list-item-object:

Virtual Folder List Item Object
-------------------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``name``
     - ``str``
     - The human readable name set when created.
   * - ``id``
     - ``slug``
     - The unique ID of the folder.
   * - ``host``
     - ``str``
     - The host name where this folder is located.
   * - ``is_owner``
     - ``bool``
     - True if the client user is the owner of this folder.
       False if the folder is shared from a group or another user.
   * - ``permission``
     - ``enum``
     - The requested user's permission for this folder. (One of "ro", "rw", and
       "wd" which represents read-only, read-write, and write-delete
       respectively. Currently "rw" and "wd" has no difference.)
   * - ``user``
     - ``UUID``
     - The user ID if the owner of this item is a user vfolder. Otherwise, ``null``.
   * - ``group``
     - ``UUID``
     - The group ID if the owner of this item is a group vfolder. Otherwise, ``null``.
   * - ``type``
     - ``enum``
     - The owner type of vfolder. One of "user" or "group".

.. versionadded:: v4.20190615

   ``user``, ``group``, and ``type`` fields.

.. _vfolder-item-object:

Virtual Folder Item Object
--------------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``name``
     - ``str``
     - The human readable name set when created.
   * - ``id``
     - ``UUID``
     - The unique ID of the folder.
   * - ``host``
     - ``str``
     - The host name where this folder is located.
   * - ``is_owner``
     - ``bool``
     - True if the client user is the owner of this folder.
       False if the folder is shared from a group or another user.
   * - ``num_files``
     - ``int``
     - The number of files in this folder.
   * - ``permission``
     - ``enum``
     - The requested user's permission for this folder.
   * - ``created_at``
     - ``datetime``
     - The date and time when the folder is created.
   * - ``last_used``
     - ``datetime``
     - The date and time when the folder is last used.
   * - ``user``
     - ``UUID``
     - The user ID if the owner of this item is a user. Otherwise, ``null``.
   * - ``group``
     - ``UUID``
     - The group ID if the owner of this item is a group. Otherwise, ``null``.
   * - ``type``
     - ``enum``
     - The owner type of vfolder. One of "user" or "group".

.. versionadded:: v4.20190615

   ``user``, ``group``, and ``type`` fields.

.. _vfolder-file-object:

Virtual Folder File Object
--------------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``filename``
     - ``str``
     - The filename.
   * - ``mode``
     - ``int``
     - The file's mode (permission) bits as an integer.
   * - ``size``
     - ``int``
     - The file's size.
   * - ``ctime``
     - ``int``
     - The timestamp when the file is created.
   * - ``mtime``
     - ``int``
     - The timestamp when the file is last modified.
   * - ``atime``
     - ``int``
     - The timestamp when the file is last accessed.

.. _vfolder-invitation-object:

Virtual Folder Invitation Object
--------------------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``id``
     - ``UUID``
     - The unique ID of the invitation. Use this when making API requests referring this invitation.
   * - ``inviter``
     - ``str``
     - The inviter's user ID (email) of the invitation.
   * - ``permission``
     - ``str``
     - The permission that the invited user will have.
   * - ``state``
     - ``str``
     - The current state of the invitation.
   * - ``vfolder_id``
     - ``UUID``
     - The unique ID of the vfolder where the user is invited.
   * - ``vfolder_name``
     - ``str``
     - The name of the vfolder where the user is invited.

.. _vfolder-fstab-object:

.. list-table::
   :widths: 15, 5, 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``content``
     - ``str``
     - The retrieved content (multi-line string) of fstab.
   * - ``node``
     - ``str``
     - The node type, either "agent" or "manager.
   * - ``node_id``
     - ``str``
     - The node's unique ID.

.. versionadded:: v4.20190615
