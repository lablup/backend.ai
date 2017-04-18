Code Execution (Query Mode)
===========================

Executing a user code snippet
-----------------------------

* URI: ``/v2/kernel/:id``
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
   * - ``mode``
     - A constant string ``"query"``.
   * - ``code``
     - A string of user-written code.  All non-ASCII data must be encoded in UTF-8 or any format acceptable by the kernel.

**Example:**

.. code-block:: json

   {
     "type": "query",
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

     - One of ``"continued"``, ``"waiting-input"``, ``"finished"``.

       If this is ``"continued"``, you should repeat making another API call until you get ``"finished"`` status.
       This happens when the user code runs longer than a few seconds, to allow the client to show its progress.
       When each call returns, the below ``result.stdout`` and ``result.stderr`` fields have the console logs captured since the last previous call.
       You should append returned console logs to your UI view to make it a complete log.
       When making continuation calls, you should not put anything in ``code`` field of the request, otherwise you will get 400 Bad Request.

       If this is ``"waiting-input"``, you should make another API call with setting ``code`` field of the request to the user-input text.
       This happens when the user code calls interactive ``input()`` functions.
       Until you send the user input, the kernel code is blocked.
       You may use modal dialogs or other input forms (e.g., HTML input) to retrieve user inputs.
       When the server receives the user input, the kernel's ``input()`` returns the given value.
       Note that the exact functions that trigger this mechanism are different language by langauge.

   * - ``result.console``

     - Contains a list of console output items. Each item is a pair of the item type and its value.
       The type can be one of ``"stdout"``, ``"stderr"``, ``"media"``, ``"html"``, or ``"log"``.

       When this is ``"stdout"`` or ``"stderr"``, the value is the standard I/O stream outputs as (non-escaped) UTF-8 string.
       Both fields are truncated to 524,288 Unicode characters.
       The stderr field includes not only stderr outputs but also language-specific tracebacks of (unhandled) exceptions or errors occurred in the user code.

       When this is ``"media"``, the value is a pair of the MIME type and the content data.
       If the MIME type is text-based (e.g., ``"text/plain"``) or XML-based (e.g., ``"image/svg+xml"``), the content is just a string that represent the content.
       Otherwise, the data is encoded as a data URI format (RFC 2397).
       You may use `sorna-media library <https://github.com/lablup/sorna-media>`_ to handle this field in Javascript on web-browsers.

       When this is ``"html"``, the value is a partial HTML document string, such as a table to show tabular data.
       If you are implementing a web-based front-end, you may use it directly to the standard DOM API, for instance, ``consoleElem.insertAdjacentHTML(value, "beforeend")``.

       When this is ``"log"``, the value is a 4-tuple of the log level, the timestamp in the ISO 8601 format, the logger name and the log message string.
       The log level may be one of ``"debug"``, ``"info"``, ``"warning"``, ``"error"``, or ``"fatal"``.
       You may use different colors/formatting by the log level when printing the log message.
       This rich logging facilities are available to only supported kernels.

       .. tip::

          All returned strings are *not* escaped. You should take care of this as well as formatting new lines properly
          (use ``<pre>`` element or replace them with ``<br>``) when rendering the result to web browsers.
          An easy way to do this safely is to use ``insertAdjacentText()`` DOM API.

   * - ``result.options``

     - An object containing extra display options.  If there is no options indicated by the kernel, this field is ``null``.
       When ``result.status`` is ``"waiting-input"``, it has a boolean field ``is_password`` so that you could use
       different types of text boxes for user inputs.

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
       "status": "finished",
       "console": [
         ["stdout", "Hello, Lablup!\n"]
       ],
       "options": null
     }
   }

Auto-completion
---------------

* URI: ``/v2/kernel/:id``
* Method: ``POST``

.. warning::

   This API is draft and may be changed without notices.

Parameters
""""""""""

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Description
   * - ``:id``
     - The kernel ID.
   * - ``mode``
     - A constant string ``"complete"``.
   * - ``preCode``
     - A string containing the code until the current cursor position.
   * - ``postCode``
     - A string containing the code after the current cursor position.
   * - ``line``
     - A string containing the content of the current line.
   * - ``row``
     - An integer indicating the line number (0-based) of the cursor.
   * - ``col``
     - An integer indicating the column number (0-based) in the current line of the cursor.

**Example:**

.. code-block:: json

   {
     "type": "complete",
     "preCode": "pri",
     "postCode": "\nprint(\"world\")\n",
     "line": "pri",
     "row": 0,
     "col": 3
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
   * - ``result``

     - An ordered list containing the possible auto-completion matches as strings.
       This may be empty if the current kernel does not implement auto-completion
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

