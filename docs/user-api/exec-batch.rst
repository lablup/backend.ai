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


Executing with Build Step
-------------------------

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
   * - ``code``
     - ``str``
     - Must be an empty string ``""``.
   * - ``runId``
     - ``str``
     - A string of client-side unique identifier for this particular run.
       For more details about the concept of a run, see :ref:`code-execution-model`.
       If not given, the API server will assign a random one in the first response and the client must use it for the same run afterwards.
   * - ``options``
     - ``object``
     - :ref:`batch-execution-query-object`.

Example:

.. code-block:: json

   {
     "type": "batch",
     "options": "{batch-execution-query-object}",
     "runId": "af9185c5fb0eacb2"
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
   * - ``result``
     - ``object``
     - :ref:`execution-result-object`.


Listing Files
-------------

Once files are uploaded to the kernel session or generated during the execution
of the code, there is a need to identify what files actually are in the current
session. In this case, use this API to get the list of files of your compute
sesison.

* URI: ``/v2/kernel/:id/files``
* Method: ``GET``

Parameters
""""""""""

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:id``
     - ``slug``
     - The kernel ID.
   * - ``path``
     - ``str``
     - Path inside the session (default: ``/home/work``).

Response
""""""""

.. list-table::
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - Success.
   * - 404 Not Found
     - There is no such path.

.. list-table::
   :widths: 20 20 75
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``files``
     - ``str``
     - Stringified json containing list of files.
   * - ``folder_path``
     - ``str``
     - Absolute path inside kernel session.


Downloading Files
-----------------

Download files from your compute session.

The response contents are multiparts with tarfile binaries. Post-processing,
such as unpacking and save them, should be handled by the client.

* URI: ``/v2/kernel/:id/download``
* Method: ``GET``

Parameters
""""""""""

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:id``
     - ``slug``
     - The kernel ID.
   * - ``files``
     - ``list`` of ``str``
     - File paths inside the virtual folder to download.

Response
""""""""

.. list-table::
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - Success.
