Code Exectuion and Monitoring (Streaming Mode)
==============================================

The streaming mode provides a direct web-based terminal access to kernel containers.


Terminal Emulation
------------------

* URI: ``/v1/stream/kernel/:id/pty``
* Method: GET upgraded to WebSockets

This endpoint provides a duplex continuous stream of JSON objects via the native WebSocket.
Although WebSocket supports binary streams, we currently rely on only text-based JSON messages
to avoid quirks in typed array support in Javascript across browsers.

.. note::

   We do *not* provide any legacy WebSocket emulation interfaces such as socket.io or SockJS.
   You need to set up your own proxy if you want to support legacy browser users.

Parameters
""""""""""

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Description
   * - ``:id``
     - The kernel ID.

Client-to-Server Protocol
"""""""""""""""""""""""""

The endpoint accepts the following four types of input messages.

Standard input stream
^^^^^^^^^^^^^^^^^^^^^

All ASCII (and UTF-8) inputs must be encoded as base64 strings.
The characters may include control characters as well.

.. code-block:: json

   {
     "type": "stdin",
     "chars": "<base64-encoded-raw-characters>"
   }

Terminal resize
^^^^^^^^^^^^^^^

Set the terminal size to the given number of rows and columns.
You should calculate them by yourself.

For instance, for web-browsers, you may do a simple math by measuring the width
and height of a temporarily created, invisible HTML element with the
(monospace) font styles same to the terminal container element that contains
only a single ASCII character.

.. code-block:: json

   {
     "type": "resize",
     "rows": 25,
     "cols": 80
   }

Ping
^^^^

Use this to keep the kernel alive (preventing it from auto-terminated by idle timeouts)
by sending pings periodically while the user-side browser is open.

.. code-block:: json

   {
     "type": "ping",
   }

Restart
^^^^^^^

Use this to restart the kernel without affecting the working directory and usage counts.
Useful when your foreground terminal program does not respond for whatever reasons.

.. code-block:: json

   {
     "type": "restart",
   }


Server-to-Client Protocol
"""""""""""""""""""""""""

Standard output/error stream
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since the terminal is an output device, all stdout/stderr outputs are merged
into a single stream as we see in real terminals.
This means there is no way to distinguish stdout and stderr in the client-side,
unless your kernel applies some special formatting to distinguish them (e.g.,
make all stderr otuputs red).

.. code-block:: json

   {
     "type": "out",
     "data": "<base64-encoded-raw-characters>"
   }

Server-side errors
^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
     "type": "error",
     "data": "<base64-encoded-raw-characters>"
   }


This API function is compatible with `node-webterm <https://github.com/Gottox/node-webterm/>`_.


Monitoring events from the kernel session
-----------------------------------------

* URI: ``/v1/stream/kernel/:id/events``
* Method: GET upgraded to WebSockets

This API function is read-only --- meaning that you cannot send any data to this URI.

.. warning::

   This API is not implemented yet.

.. note::

   There is timeout enforced in the server-side but you may need to adjust
   defaults in your client-side WebSocket library.


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
The limitation only applies to all client-generated messages including the
initial WebSocket connection handshake but except stdin type messages such as
individual keystrokes in the terminal.
Server-generated messages are also exempted from rate limiting.

Usage metrics
-------------

The streaming mode uses the same method that the query mode uses to measure the
usage metrics such as the memory and CPU time used.
