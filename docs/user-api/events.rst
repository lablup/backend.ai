.. _events:

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
   * - ``sessionId``
     - ``slug``
     - The session ID to monitor the lifecycle events.
       If set ``"*"``, the API will stream events from all kernels visible to the client
       depending on the client's role and permissions.
   * - ``ownerAccessKey``
     - ``str``
     - *(optional)* The access key of the owner of the specified session, since different
       access keys (users) may share a same session ID for different session instances.
       You can specify this only when the client is either a domain admin or a superadmin.
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
   * - ``kernel_preparing``
     - The session is just scheduled from the job queue and got an agent resource allocation.
   * - ``kernel_pulling``
     - The session begins pulling the kernel image (usually from a Docker registry) to the scheduled agent.
   * - ``kernel_creating``
     - The session is being created as containers (or other entities in different agent backends).
   * - ``kernel_started``
     - The session becomes ready to execute codes.
   * - ``kernel_terminated``
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
