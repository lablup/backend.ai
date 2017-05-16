Code Execution (Batch Mode)
===========================

Some kernels provide the batch mode, which offers an explicit build step
required for multi-module programs or compiled programming languages.
In this mode, you first upload files in prior to execution.

Uploading files
---------------

* URI: ``/v2/kernel/:id/upload``
* Method: ``POST``

Parameters
""""""""""

Upload files to the kernel session.
You may upload multiple files at once using multi-part form-data encoding in the request body (RFC 1867/2388).
The uploaded files are placed under ``/home/work`` directory (which is the home directory for all kernels by default),
and existing files are always overwritten.
If the filename has a directory part, non-existing directories will be auto-created.
The path may be either absolute or relative, but only sub-directories under ``/home/work`` is allowed to be created.

.. hint::

   This API is for uploading frequently-changing source files in prior to batch-mode execution.
   All files uploaded via this API is deleted when the kernel terminates.
   Use :doc:`virtual folders </user-api/vfolders>` to store and access larger, persistent,
   static data and library files for your codes.

.. warning::

   You cannot upload files to mounted virtual folders using this API directly.
   However, you may copy/move the generated files to virtual folders in your build script or the main program for later uses.

There are several limits on this API:

.. list-table::
   :widths: 75 25

   * - The maximum size of each file
     - 1 MiB
   * - The number of files per upload request
     - 20

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - The kernel has responded with the execution result.
       The response body contains a JSON object as described below.
   * - 400 Bad Request
     - Returned when one of the uploaded file exeeds the size limit or there are too many files.


Executing
---------

* URI: ``/v2/kernel/:id``
* Method: ``POST``

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:id``
     - ``slug``
     - The kernel ID.
   * - ``mode``
     - ``enum[str]``
     - A constant string ``"batch"``.

   * - ``options``
     - ``object``
     - (see below)

   * - ``options.build``
     - ``str``

     - The bash command to build the main program from the given uploaded files.

       If this field is not present, an empty string or ``null``, it skips the build step.

       If this field is a constant string ``"*"``, it will use a default build script provided
       by the kernel.
       For example, the C kernel's default Makefile adds all C source files
       under the working directory and copmiles them into ``./main``
       executable, with commonly used C/link flags: ``"-pthread -lm -lrt -ldl"``.

   * - ``options.buildLog``
     - ``bool``

     - Indicates whether to separately report the logs from the build step.
       (default: ``false``)

       If set ``false``, all console outputs during the build step
       are swallowed silently and only the console outputs from the main
       program are returned.
       This looks like you only run the main program with a hidden build step.

       However, if the build command fails with a non-zero exit code, then the
       ``"finished"`` response contains the swallowed console outputs of the
       build command.  You can distinguish failures from the build step and the
       execution step using ``result.options.step`` value.

       If set ``true``, at least one ``"continued"`` response will be generated
       to explicitly report the console outputs from the build step.
       Like the execution step, there may be mulitple ``"continued"`` responses
       with ``result.options.exitCode`` set ``null`` when the build step takes
       long time.

   * - ``options.exec``
     - ``str``

     - The bash command to execute the main program.

       If this is not present, an empty string, or ``null``, the server only
       performs the build step and ``options.buildLog`` is assumed to be
       ``true`` (the given value is ignored).

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
   Sorna Jail, meaning that some system calls are blocked by our policy.
   Since ``ptrace`` syscall is blocked, you cannot use native debuggers
   such as gdb.

   This limitation, however, is subject to change in the future.

Example:

.. code-block:: json

   {
     "type": "batch",
     "options": {
       "build": "gcc -Wall main.c -o main -lrt -lz",
       "exec": "./main"
     }
   }

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - The kernel has responded with the execution result.
       The response body contains a JSON object as described below.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``result.status``
     - ``enum[str]``

     - One of ``"continued"``, ``"waiting-input"``, or ``"finished"``, like the query mode.
       Please refer :doc:`the query mode documentation </user-api/exec>`
       for their meanings and how you should handle them.

       Even when this is ``"continued"``, you may notice if the build step is
       finished by checking that ``result.options.exitCode`` is *not* ``null``
       and ``result.options.step`` is ``"build"``.

   * - ``result.console``
     - ``object``

     - Refer :doc:`the query mode documentation </user-api/exec>`.

   * - ``result.options``
     - ``object``

     - Refer :doc:`the query mode documentation </user-api/exec>`.
       In the batch mode, it always has at least the following fields:

       * ``exitCode``: An integer whose value is the exit code of the build command or the main command.
         Until the process for the current step exits, this field is ``null``.
       * ``step``: Which step it generated this response. Either ``"build"`` or ``"exec"``.
         It is useful when you wish to separately display the console outputs from the different steps.

