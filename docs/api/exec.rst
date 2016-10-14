Code Execution (Query Mode)
===========================

Executing a user code snippet
-----------------------------

* URI: ``/v1/kernel/:id``
* Method: ``POST``

Executes a snippet of user code using the specified kernel session.
Each execution request to a same kernel session may have side-effects to subsequent executions.
For instance, setting a global variable in a request and reading the variable in another request is completely legal.
It is the job of the user (or the front-end) to gaurantee the correct execution order of multiple interdependent requests.
When the kernel session is terminated or restarted, all such volatile states vanish.

Parameters
""""""""""

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Description
   * - ``:id``
     - The kernel ID.
   * - ``codeId``
     - A unique identifier of the given code.  Currently, the API server ignores it.
   * - ``code``
     - A string of user-written code.  All non-ASCII data must be encoded in UTF-8 or any format acceptable by the kernel.

Example:

.. code-block:: json

   {
     "codeId": "ea24bba4-5499-4f4c-bdbd-c475cf019bfe",
     "code": "print('Hello, world!')"
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
       The result may include UTF-8 encoded stdout/stderr strings, a list of media responses, and a list of exceptions raised in the user code.

.. note::

   Even when the user code raises exceptions, such queries are treated as successful execution.

.. warning::

   If the user code tries to breach the system, causes crashs (e.g., segmentation fault), or runs too long (timeout), the kernel session is automatically terminated.

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Fields
     - Values
   * - ``result``
     - .. list-table::
          :widths: 20 80

          * - ``stdout``
            - A string containing standard output.
          * - ``stderr``
            - A string containing standard error.

       Both stdout/stderr is truncated to 524,288 Unicode characters.


Example:

.. code-block:: json

   {
     "result": {
       "stdout": "Hello, world!\n",
       "stderr": "",
       "media": [],
       "exceptions": []
     }
   }

