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
       The response body contains a JSON object as described below.

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Fields
     - Values
   * - ``result.status``

     - One of ``"finished"``, ``"continued"``, ``"waiting-input"``.

       If this is ``"continued"``, you should repeat making another API call until you get ``"finished"`` status.
       This happens when the user code runs longer than a few seconds, to allow the client to show its progress.
       When each call returns, the below ``result.stdout`` and ``result.stderr`` fields have the console logs captured since the last previous call.
       You should append returned console logs to your UI view to make it a complete log.
       When making continuation calls, you should not put anything in ``code`` field of the request, otherwise you will get 400 Bad Request.

       If this is ``"waiting-input"``, you should make another API call with setting ``code`` field of the request to the user-input text.
       This happens for interactive ``input()`` functions are called by the code sent during the previous API call.
       Until you send the user input, the kernel code is blocked.
       You may use modal dialogs or other input forms (e.g., HTML input) to retrieve user inputs.
       When the server receives the user input, the kernel's ``input()`` returns the given value.
       Note that the exact functions that trigger this mechanism are different language by langauge.

   * - ``result.stdout``

     - A string containing standard output.
       Both ``result.stdout`` and ``result.stderr`` is truncated to 524,288 Unicode characters.

   * - ``result.stderr``

     - A string containing standard error.
       This includes not only stderr outputs but also language-specific tracebacks of (unhandled) exceptions or errors occurred in the user code.

   * - ``result.media``

     - A list representing media outputs. Each list item consists of pairs of the media MIME-type and the data.
       Depending on the MIME-type, the data may be encoded in different ways.
       For instance, for ``"image/xxx"`` types the data is encoded as the data URI format.
       You may use `sorna-media library <https://github.com/lablup/sorna-media>`_ to handle this field in Javascript on web-browsers.

   * - ``result.options``

     - An object containing extra options.  If there is no options indicated by the kernel, this field is ``null``.
       When the ``status`` is ``"waiting-input"``, it has a boolean field ``is_password`` so that you could use
       different types of text boxes for user inputs.

   * - ``result.exceptions``

     - *Deprecated.*  Will contain an empty list only for backward compatibility.

.. note::

   Even when the user code raises exceptions, such queries are treated as successful execution.
   i.e., The failure of this API means that our API subsystem had errors, not the user codes.

.. warning::

   If the user code tries to breach the system, causes crashs (e.g., segmentation fault), or runs too long (timeout), the kernel session is automatically terminated.
   In such cases, you will get incomplete console logs with ``"finished"`` status earlier than expected.
   Depending on situation, the ``result.stderr`` may also contain specific error information.


Here we demonstrate a few example returns when various Python codes are executed.

**Example: Simple return.**

.. code-block:: python

   print("Hello, world!")

.. code-block:: json

   {
     "result": {
       "status": "finished",
       "stdout": "Hello, world!\n",
       "stderr": "",
       "options": null,
       "media": [],
       "exceptions": []
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
       "status": "continued",
       "stdout": "Tick 1\nTick 2\n",
       "stderr": "",
       "options": null,
       "media": [],
       "exceptions": []
     }
   }

Here you should make another API query with the empty ``code`` field.

.. code-block:: json

   {
     "result": {
       "status": "continued",
       "stdout": "Tick 3\nTick 4\n",
       "stderr": "",
       "options": null,
       "media": [],
       "exceptions": []
     }
   }

Again.

.. code-block:: json

   {
     "result": {
       "status": "finished",
       "stdout": "Tick 5\ndone\n",
       "stderr": "",
       "options": null,
       "media": [],
       "exceptions": []
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
       "status": "waiting-input",
       "stdout": "What is your name?\n>> ",
       "stderr": "",
       "options": {
         "is_password": false
       },
       "media": [],
       "exceptions": []
     }
   }

You should make another API query with the ``code`` field filled with the user input.

.. code-block:: json

   {
     "result": {
       "status": "finished",
       "stdout": "Hello, Lablup!\n",
       "stderr": "",
       "options": null,
       "media": [],
       "exceptions": []
     }
   }
