Code Exectuion and Monitoring (Streaming Mode)
==============================================

The streaming mode allows the clients to interact with the kernel session in real-time.
For example, a front-end service may provide an input field for CLI prompts of the user program or a complete terminal emulation.


Terminal Emulation
------------------

* URI: ``/v1/stream/kernel/:id/pty``
* Method: WebSockets

Parameters
""""""""""

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Description
   * - ``:id``
     - The kernel ID.

This API function is compatible with `node-webterm <https://github.com/Gottox/node-webterm/>`_.


Monitoring events from the kernel session
-----------------------------------------

* URI: ``/v1/stream/kernel/:id/events``
* Method: WebSockets

This API function is read-only --- meaning that you cannot send any data to this URI.

Parameters
""""""""""

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Description
   * - ``:id``
     - The kernel ID.

Responses
"""""""""

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Field Name
     - Value
   * - ``name``
     - The name of an event as a string. May be one of:
       ``"terminated"``, ``"restarted"``
   * - ``reason``
     - The reason for the event as a canonicalized string
       such as ``"out-of-memory"``, ``"bad-action"``, and ``"execution-timeout"``.

Example:

.. code-block:: json

   {
     "name": "terminated",
     "reason": "execution-timeout"
   }


Rate limiting
-------------

The streaming mode uses the same rate limiting policy as other APIs use.
The limitation only applies to client-generated messages but not to the server-generated messages.

Usage metrics
-------------

The streaming mode uses the same method that the query mode uses to measure the usage metrics such as the memory and CPU time used.
