.. _exec-stream:

Streaming Execution
===================

The streaming mode provides a lightweight and interactive method to connect with the kernel containers.


Code Execution
--------------
* URI: ``/stream/kernel/:id/execute``
* Method: ``GET`` upgraded to WebSockets

This is a real-time streaming version of :doc:`exec-batch` and :doc:`exec-query` which uses
long polling via HTTP.

(under construction)

.. versionadded:: v4.20181215


.. _service-ports:

Service Ports (aka Service Proxies)
===================================

The service ports API provides WebSocket-based authenticated and encrypted tunnels
to network-facing services ("container services") provided by the kernel container.
The main advantage of this feature is that all application-specific network traffic
are wrapped as a standard WebSocket API (no need to open extra ports of the manager).
It also hides the container from the client and the client from the container,
offerring an extra level of security.

.. _service-port-diagram:
.. figure:: service-ports.svg

   The diagram showing how tunneling of TCP connections via WebSockets works.

As :numref:`service-port-diagram` shows, all TCP traffic to a container service
could be sent to a WebSocket connection to the following API endpoints.  A
single WebSocket connection corresponds to a single TCP connection to the
service, and there may be multiple concurrent WebSocket connections to
represent multiple TCP connections to the service.  It is the client's
responsibility to accept arbitrary TCP connections from users (e.g., web
browsers) with proper authorization for multi-user setups and wrap those as
WebSocket connections to the following APIs.

When the first connection is initiated, the Backend.AI Agent running the designated
kernel container signals the kernel runner daemon in the container to start the
designated service.  It shortly waits for the in-container port opening and
then delivers the first packet to the service.  After initialization, all
WebSocket payloads are delivered back and forth just like normal TCP packets.
Note that the WebSocket message type must be ``BINARY``.

The container service will see the packets from the manager and it never knows
the real origin of packets unless the service-level protocol enforces to state
such client-side information.  Likewise, the client never knows the container's
IP address (though the port numbers are included in :ref:`service port objects
<service-port-object>` returned by :ref:`the session creation API
<create-session-api>`).

.. note:: Currently non-TCP (e.g., UDP) services are not supported.


Service Proxy (HTTP)
--------------------

* URI: ``/stream/kernel/:id/httpproxy?app=:service``
* Method: ``GET`` upgraded to WebSockets

The service proxy API allows clients to directly connect to service daemons running *inside*
compute sessions, such as Jupyter and TensorBoard.

The service name should be taken from the list of :ref:`service port objects
<service-port-object>` returned by :ref:`the session creation API
<create-session-api>`.

.. versionadded:: v4.20181215

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
   * - ``:service``
     - ``slug``
     - The service name to connect.


Service Proxy (TCP)
-------------------

* URI: ``/stream/kernel/:id/tcpproxy?app=:service``
* Method: ``GET`` upgraded to WebSockets

This is the TCP version of service proxy, so that client users can connect to native services
running inside compute sessions, such as SSH.

The service name should be taken from the list of :ref:`service port objects
<service-port-object>` returned by :ref:`the session creation API
<create-session-api>`.

.. versionadded:: v4.20181215

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
   * - ``:service``
     - ``slug``
     - The service name to connect.


Terminal Emulation
------------------

* URI: ``/stream/kernel/:id/pty?app=:service``
* Method: ``GET`` upgraded to WebSockets

This endpoint provides a duplex continuous stream of JSON objects via the native WebSocket.
Although WebSocket supports binary streams, we currently rely on TEXT messages only
conveying JSON payloads to avoid quirks in typed array support in Javascript
across different browsers.

The service name should be taken from the list of :ref:`service port objects
<service-port-object>` returned by :ref:`the session creation API
<create-session-api>`.

.. note::

   We do *not* provide any legacy WebSocket emulation interfaces such as socket.io or SockJS.
   You need to set up your own proxy if you want to support legacy browser users.

.. versionchanged:: v4.20181215

   Added the ``service`` query parameter.

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
   * - ``:service``
     - ``slug``
     - The service name to connect.

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

The terminal output is compatible with xterm (including 256-color support).

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
     "data": "<human-readable-message>"
   }


Event Monitoring
================

Kernel Lifecycle Events
-----------------------

* URI: ``/stream/kernel/_/events``
* Method: ``GET``

Provides a continuous message-by-message JSON object stream of kernel lifecycles.
It uses `HTML5 Server-Sent Events (SSE) <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events>`_.
Browser-based clients may use `the EventSource API <https://developer.mozilla.org/en-US/docs/Web/API/EventSource>`_
for convenience.

.. versionadded:: v4.20190615

   First properly implemented in this version, deprecating prior unimplemented interfaces.


Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``kernelId``
     - ``slug``
     - The kernel ID to monitor the lifecycle events.
       If set ``"*"``, the API will stream events from all kernels visible to the client
       depending on the client's role and permissions.
   * - ``group``
     - ``str``
     - The group name to filter the lifecycle events.
       If set ``"*"``, the API will stream events from all kernels visible to the client
       depending on the client's role and permissions.

Responses
"""""""""

The response is a continuous stream of UTF-8 text lines following the ``text/event-stream`` format.
Each event is composed of the event type and data, where the data part is encoded as JSON.

Possible event names (more events may be added in the future):

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Event Name
     - Description
   * - ``kernel-preparing``
     - The session is just scheduled from the job queue and got an agent resource allocation.
   * - ``kernel-pulling``
     - The session begins pulling the kernel image (usually from a Docker registry) to the scheduled agent.
   * - ``kernel-creating``
     - The session is being created as containers (or other entities in different agent backends).
   * - ``kernel-started``
     - The session becomes ready to execute codes.
   * - ``kernel-terminated``
     - The session has terminated.

When using the EventSource API, you should add event listeners as follows:

.. code-block:: javascript

   const sse = new EventSource('/stream/kernel/_/events', {
     withCredentials: true,
   });
   sse.addEventListener('kernel-started', (e) => {
     console.log('kerenl-started', JSON.parse(e.data));
   });

.. note::

   The EventSource API must be used with the session-based authentication mode
   (when the endpoint is a console-server) which uses the browser cookies.
   Otherwise, you need to manually implement the event stream parser using the
   standard fetch API running against the manager server.

The event data contains a JSON string like this (more fields may be added in the future):

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Field Name
     - Description
   * - ``sessionId``
     - The source session ID.
   * - ``ownerAccessKey``
     - The access key who owns the session.
   * - ``reason``
     - A short string that describes why the event happened.
       This may be ``null`` or an empty string.
   * - ``result``
     - Only present for ``kernel-terminated`` events.
       Only meaningful for batch-type sessions.
       Either one of: ``"UNDEFINED"``, ``"SUCCESS"``, ``"FAILURE"``

.. code-block:: json

   {
     "sessionId": "mysession-01",
     "ownerAccessKey": "MYACCESSKEY",
     "reason": "self-terminated",
     "result": "SUCCESS"
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
