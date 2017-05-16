Kernel Management
=================

Creating a kernel session
-------------------------

* URI: ``/v2/kernel/create``
* Method: ``POST``

Creates a kernel session to run user-input code snippets.

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description

   * - ``lang``
     - ``str``
     - The kernel type, usually the name of one of our supported programming languages.

   * - ``clientSessionToken``
     - ``str``
     - Client session token. Should be unique for continuous execution (for REPL).

   * - ``limits``
     - ``object``
     - An optional :ref:`resource-limit-object` to specify resource requirements.
       Additional charges may apply on the public API service.
       If the requested limits exceeds our internal hard-limits,
       the API may return HTTP 406 "Not acceptable".

   * - ``mounts``
     - ``list[str]``
     - An optional list of the name of virtual folders that belongs to the current API key.
       These virtual folders are mounted under ``/home/work``.
       For example, if the virtual folder name is ``abc``, you can access it on
       ``/home/work/abc``.

       If the name contains a colon in the middle, the second part of the string indicates
       the alias location in the kernel's file system which is relative to ``/home/work``.

       You may mount up to 5 folders for each kernel session.

Example:

.. code-block:: json

   {
     "lang": "python3",
     "clientSessionToken": "EXAMPLE:STRING",
     "limits": {
       "maxMem": 51240,
       "execTimeout": 5000
     },
     "mounts": [
       "mydata",
       "mypkgs:.local/lib/python3.6/site-packages"
     ]
   }


Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 201 Created
     - The kernel is successfully created.
   * - 406 Not acceptable
     - The requested resource limits exceed the server's own limits.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``kernelId``
     - ``slug``
     - The kernel ID used for later API calls.


Example:

.. code-block:: json

   {
     "kernelId": "TSSJT2Z4SnmQhxjWMnJljg"
   }


Getting kernel information
--------------------------

* URI: ``/v2/kernel/:id``
* Method: ``GET``

Retrieves information about a kernel session.
For performance reasons, the returned information may not be real-time; usually
they are updated every a few seconds in the server-side.

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

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - The information is successfully returned.
   * - 404 Not Found
     - There is no such kernel.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``lang``
     - ``str``
     - The kernel type.
   * - ``age``
     - ``int`` (msec)
     - The time elapsed since the kernel has started.
   * - ``idle``
     - ``int`` (msec)
     - The time elapsed since the kernel has generated any output.
   * - ``queryTimeout``
     - ``int`` (msec)
     - The timeout for executing each query (the time between accepting a query and receiving the output) in milliseconds.
       If exceeded, the kernel is automatically destroyed.
   * - ``idleTimeout``
     - ``int`` (msec)
     - The maximum duration between queries.
       If exceeded, the kernel is automatically destroyed.
   * - ``maxCpuCredit``
     - ``int`` (msec)
     - The maximum amount of CPU time that this kernel can use.
       If exceeded, the kernel is automatically destroyed.
       If zero, there is no limit imposed.
   * - ``numQueriesExecuted``
     - ``int``
     - The total number of queries executed after start-up.
   * - ``memoryUsed``
     - ``int`` (KiB)
     - The amount of memory that this kernel is using now.
   * - ``cpuCreditUsed``
     - ``int`` (msec)
     - The amount of CPU time that this kernel has used so far.

Example:

.. code-block:: json

   {
     "lang": "python3",
     "age": 30220,
     "idle": 1204,
     "queryTimeout": 15000,
     "idleTimeout": 3600000,
     "maxCpuCredit": 0,
     "numQueriesExecuted": 12,
     "memoryUsed": 6531,
     "cpuCreditUsed": 102
   }


Destroying a kernel session
---------------------------

* URI: ``/v2/kernel/:id``
* Method: ``DELETE``

Terminates a kernel session.

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

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 204 No Content
     - The kernel is successfully destroyed.
   * - 404 Not Found
     - There is no such kernel.


Restarting a kernel session
---------------------------

* URI: ``/v2/kernel/:id``
* Method: ``PATCH``

Restarts a kernel session.
The idle time of the kernel will be reset, but other properties such as the age and CPU credit will continue to accumulate.
All global states such as global variables and modules imports are also reset.

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

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 204 No Content
     - The kernel is successfully restarted.
   * - 404 Not Found
     - There is no such kernel.
