Code Execution (Query Mode)
===========================

Executing Snippet
-----------------

* URI: ``/session/:id``
* Method: ``POST``

Executes a snippet of user code using the specified session.
Each execution request to a same session may have side-effects to subsequent executions.
For instance, setting a global variable in a request and reading the variable in another request is completely legal.
It is the job of the user (or the front-end) to guarantee the correct execution order of multiple interdependent requests.
When the session is terminated or restarted, all such volatile states vanish.

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
     - The session ID.
   * - ``mode``
     - ``str``
     - A constant string ``"query"``.
   * - ``code``
     - ``str``
     - A string of user-written code.
       All non-ASCII data must be encoded in UTF-8 or any format acceptable by the session.
   * - ``runId``
     - ``str``
     - A string of client-side unique identifier for this particular run.
       For more details about the concept of a run, see :ref:`code-execution-model`.
       If not given, the API server will assign a random one in the first response and the client must use it for the same run afterwards.

**Example:**

.. code-block:: json

   {
     "mode": "query",
     "code": "print('Hello, world!')",
     "runId": "5facbf2f2697c1b7"
   }


Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - The session has responded with the execution result.
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

.. note::

   Even when the user code raises exceptions, such queries are treated as successful execution.
   i.e., The failure of this API means that our API subsystem had errors, not the user codes.

.. warning::

   If the user code tries to breach the system, causes crashes (e.g., segmentation fault), or runs too long (timeout), the session is automatically terminated.
   In such cases, you will get incomplete console logs with ``"finished"`` status earlier than expected.
   Depending on situation, the ``result.stderr`` may also contain specific error information.


Here we demonstrate a few example returns when various Python codes are executed.

**Example: Simple return.**

.. code-block:: python

   print("Hello, world!")

.. code-block:: json

   {
     "result": {
       "runId": "5facbf2f2697c1b7",
       "status": "finished",
       "console": [
         ["stdout", "Hello, world!\n"]
       ],
       "options": null
     }
   }

**Example: Runtime error.**

.. code-block:: python

   a = 123
   print('what happens now?')
   a = a / 0

.. code-block:: json

   {
     "result": {
       "runId": "5facbf2f2697c1b7",
       "status": "finished",
       "console": [
         ["stdout", "what happens now?\n"],
         ["stderr", "Traceback (most recent call last):\n  File \"<input>\", line 3, in <module>\nZeroDivisionError: division by zero"],
       ],
       "options": null
     }
   }

**Example: Multimedia output.**

Media outputs are also mixed with other console outputs according to their execution order.

.. code-block:: python

   import matplotlib.pyplot as plt
   a = [1,2]
   b = [3,4]
   print('plotting simple line graph')
   plt.plot(a, b)
   plt.show()
   print('done')

.. code-block:: json

   {
     "result": {
       "runId": "5facbf2f2697c1b7",
       "status": "finished",
       "console": [
         ["stdout", "plotting simple line graph\n"],
         ["media", ["image/svg+xml", "<?xml version=\"1.0\" ..."]],
         ["stdout", "done\n"]
       ],
       "options": null
     }
   }

**Example: Continuation results.**

.. code-block:: python

   import time
   for i in range(5):
       print(f"Tick {i+1}")
       time.sleep(1)
   print("done")

.. code-block:: json

   {
     "result": {
       "runId": "5facbf2f2697c1b7",
       "status": "continued",
       "console": [
         ["stdout", "Tick 1\nTick 2\n"]
       ],
       "options": null
     }
   }

Here you should make another API query with the empty ``code`` field.

.. code-block:: json

   {
     "result": {
       "runId": "5facbf2f2697c1b7",
       "status": "continued",
       "console": [
         ["stdout", "Tick 3\nTick 4\n"]
       ],
       "options": null
     }
   }

Again.

.. code-block:: json

   {
     "result": {
       "runId": "5facbf2f2697c1b7",
       "status": "finished",
       "console": [
         ["stdout", "Tick 5\ndone\n"],
       ],
       "options": null
     }
   }

**Example: User input.**

.. code-block:: python

   print("What is your name?")
   name = input(">> ")
   print(f"Hello, {name}!")

.. code-block:: json

   {
     "result": {
       "runId": "5facbf2f2697c1b7",
       "status": "waiting-input",
       "console": [
         ["stdout", "What is your name?\n>> "]
       ],
       "options": {
         "is_password": false
       }
     }
   }

You should make another API query with the ``code`` field filled with the user input.

.. code-block:: json

   {
     "result": {
       "runId": "5facbf2f2697c1b7",
       "status": "finished",
       "console": [
         ["stdout", "Hello, Lablup!\n"]
       ],
       "options": null
     }
   }

Auto-completion
---------------

* URI: ``/session/:id/complete``
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
     - The session ID.
   * - ``code``
     - ``str``
     - A string containing the code until the current cursor position.
   * - ``options.post``
     - ``str``
     - A string containing the code after the current cursor position.
   * - ``options.line``
     - ``str``
     - A string containing the content of the current line.
   * - ``options.row``
     - ``int``
     - An integer indicating the line number (0-based) of the cursor.
   * - ``options.col``
     - ``int``
     - An integer indicating the column number (0-based) in the current line of the cursor.

**Example:**

.. code-block:: json

   {
     "code": "pri",
     "options": {
       "post": "\nprint(\"world\")\n",
       "line": "pri",
       "row": 0,
       "col": 3
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
     - The session has responded with the execution result.
       The response body contains a JSON object as described below.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``result``
     - ``list[str]``

     - An ordered list containing the possible auto-completion matches as strings.
       This may be empty if the current session does not implement auto-completion
       or no matches have been found.

       Selecting a match and merging it into the code text are up to the front-end
       implementation.

**Example:**

.. code-block:: json

   {
     "result": [
       "print",
       "printf"
     ]
   }

Interrupt
---------

* URI: ``/session/:id/interrupt``
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
     - The session ID.

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 204 No Content
     - Sent the interrupt signal to the session.
       Note that this does *not* guarantee the effectiveness of the interruption.
