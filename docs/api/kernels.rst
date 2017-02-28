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
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Description
   * - ``lang``
     - The kernel type, usually the name of one of our supported programming languages.
   * - ``clientSessionToken``
     - Client session token. Should be unique for continuous execution (for REPL).
   * - ``resourceLimits``
     - An optional argument to specify resource requirements.
       Additional charges may apply on the public API service.
       If the requested limits exceeds our internal hard-limits,
       the API may return HTTP 406 "Not acceptable".

       .. list-table::
          :widths: 20 80
          :header-rows: 1

          * - Fields
            - Values
          * - ``maxMem``
            - Maximum memory to use in KBytes.
          * - ``timeout``
            - Maximum execution timeout in milliseconds.

Example:

.. code-block:: json

   {
     "lang": "python3",
     "clientSessionToken": "EXAMPLE:STRING",
     "resourceLimits": {
       "maxMem": 51240,
       "timeout": 5000
     }
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
   :widths: 20 80
   :header-rows: 1

   * - Fields
     - Values
   * - ``kernelId``
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
For performance reasons, the returned information may not be real-time; usually they are updated every a few seconds in the server-side.

Parameters
""""""""""

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Description
   * - ``:id``
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
   :widths: 20 80
   :header-rows: 1

   * - Fields
     - Values
   * - ``lang``
     - The kernel type.
   * - ``age``
     - The time elapsed since the kernel has started in milliseconds.
   * - ``idle``
     - The time elapsed since the kernel has generated any output in milliseconds.
   * - ``queryTimeout``
     - The timeout for executing each query (the time between accepting a query and receiving the output) in milliseconds.
       If exceeded, the kernel is automatically destroyed.
   * - ``idleTimeout``
     - The maximum duration between queries in milliseconds.
       If exceeded, the kernel is automatically destroyed.
   * - ``maxCpuCredit``
     - The maximum amount of CPU time that this kernel can use in milliseconds.
       If exceeded, the kernel is automatically destroyed.
       If zero, there is no limit imposed.
   * - ``numQueriesExecuted``
     - The total number of queries executed after start-up.
   * - ``memoryUsed``
     - The amount of memory that this kernel is using now in KB.
   * - ``cpuCreditUsed``
     - The amount of CPU time that this kernel has used so far in milliseconds.

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
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Description
   * - ``:id``
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
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Description
   * - ``:id``
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
