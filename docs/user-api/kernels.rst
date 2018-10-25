Kernel Management
=================

Here are the API calls to create and manage compute sessions.

Creating Kernel Session
-----------------------

* URI: ``/v2/kernel/`` (``/v2/kernel/create`` also works for legacy)
* Method: ``POST``

Creates a kernel session if there is no existing (running) kernel with the same ``clientSessionToken``.
If there is an existing session and it has the same ``lang``, no new session is created but the API returns successfully.
In this case, ``config`` options are *ignored* and the ``created`` field in the response is set ``false`` (otherwise it's ``true``).
If there is an existing session but with a different ``lang``, then the API server returns an error.

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
     - The kernel runtime type, usually in the form of the language name and its version tag connected with a colon.
       (e.g., ``"python:latest"``)

   * - ``tag``
     - ``str``
     - An optional per-session, user-provided tag for administrators to keep track of additional information of each session,
       such as which sessions are from which users.


   * - ``clientSessionToken``
     - ``str``
     - Client-provided session token which can contain ASCII alphabets, numbers, and hyphens in the middle.
       The length must be between 4 to 64 characters inclusively.
       It is useful for aliasing the session with a human-friendly name.
       There can exist only one running session with the same token at a time, but you can reuse the same token if previous session has been terminated.

   * - ``config``
     - ``object``
     - An optional :ref:`creation-config-object` to specify extra kernel
       configuration.

Example:

.. code-block:: json

   {
     "lang": "python:3.6",
     "tag": "example-tag",
     "clientSessionToken": "EXAMPLE:STRING",
     "config": {
       "clusterSize": 1,
       "instanceMemory": 51240,
       "environ": {
         "MYCONFIG": "XXX",
       },
       "mounts": [
         "mydata",
         "mypkgs:.local/lib/python3.6/site-packages"
       ],
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
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``kernelId``
     - ``slug``
     - The kernel ID used for later API calls.
   * - ``created``
     - ``bool``
     - True if the kernel is freshly created.


Example:

.. code-block:: json

   {
     "kernelId": "TSSJT2Z4SnmQhxjWMnJljg",
     "created": true
   }


Getting Kernel Information
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
   * - ``item``
     - ``object``
     - :ref:`session-item-object`.


Destroying Kernel Session
-------------------------

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


Restarting Kernel Session
-------------------------

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
