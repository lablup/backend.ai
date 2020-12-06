.. _events:

Event Monitoring
================

.. _session-lifecycle-events:

Session Lifecycle Events
------------------------

* URI: ``/events/session``
* Method: ``GET``

Provides a continuous message-by-message JSON object stream of session lifecycles.
It uses `HTML5 Server-Sent Events (SSE) <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events>`_.
Browser-based clients may use `the EventSource API <https://developer.mozilla.org/en-US/docs/Web/API/EventSource>`_
for convenience.

.. versionadded:: v4.20190615

   First properly implemented in this version, deprecating prior unimplemented interfaces.

.. versionchanged:: v5.20191215

   The URI is changed from ``/stream/session/_/events`` to ``/events/session``.


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
       If set ``"*"``, the API will stream events from all sessions visible to the client
       depending on the client's role and permissions.
   * - ``ownerAccessKey``
     - ``str``
     - *(optional)* The access key of the owner of the specified session, since different
       access keys (users) may share a same session ID for different session instances.
       You can specify this only when the client is either a domain admin or a superadmin.
   * - ``group``
     - ``str``
     - The group name to filter the lifecycle events.
       If set ``"*"``, the API will stream events from all sessions visible to the client
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
   * - ``session_preparing``
     - The session is just scheduled from the job queue and got an agent resource allocation.
   * - ``session_pulling``
     - The session begins pulling the session image (usually from a Docker registry) to the scheduled agent.
   * - ``session_creating``
     - The session is being created as containers (or other entities in different agent backends).
   * - ``session_started``
     - The session becomes ready to execute codes.
   * - ``session_terminated``
     - The session has terminated.

When using the EventSource API, you should add event listeners as follows:

.. code-block:: javascript

   const sse = new EventSource('/events/session', {
     withCredentials: true,
   });
   sse.addEventListener('session_started', (e) => {
     console.log('session_started', JSON.parse(e.data));
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
     - Only present for ``session-terminated`` events.
       Only meaningful for batch-type sessions.
       Either one of: ``"UNDEFINED"``, ``"SUCCESS"``, ``"FAILURE"``

.. code-block:: json

   {
     "sessionId": "mysession-01",
     "ownerAccessKey": "MYACCESSKEY",
     "reason": "self-terminated",
     "result": "SUCCESS"
   }


.. _bgtask-progress-events:

Background Task Progress Events
-------------------------------

* URI: ``/events/background-task``
* Method: ``GET`` for server-side events

.. versionadded:: v5.20191215

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``taskId``
     - ``UUID``
     - The background task ID to monitor the progress and completion.

Responses
"""""""""

The response is a continuous stream of UTF-8 text lines following ``text/event-stream`` format.
Each event is composed of the event type and data, where the data part is encoded as JSON.
Possible event names (more events may be added in the future):

.. list-table::
   :widths: 15 85
   :header-rows: 1

   * - Event Name
     - Description
   * - ``task_updated``
     - Updates for the progress. This can be generated many times during the background task execution.
   * - ``task_done``
     - The background task is successfully completed.
   * - ``tak_failed``
     - The background task has failed.
       Check the ``message`` field and/or query the error logs API for error details.
   * - ``task_cancelled``
     - The background task is cancelled in the middle.
       Usually this means that the server is being shutdown for maintenance.
   * - ``server_close``
     - This event indicates explicit server-initiated close of the event monitoring connection,
       which is raised just after the background task is either done/failed/cancelled.
       The client should not reconnect because there is nothing more to monitor about the given task.

The event data (per-line JSON objects) include the following fields:

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Field Name
     - Type
     - Description
   * - ``task_id``
     - ``str``
     - The background task ID.
   * - ``current_progress``
     - ``int``
     - The current progress value.
       Only meaningful for ``task_update`` events.
       If ``total_progress`` is zero, this value should be ignored.
   * - ``total_progress``
     - ``int``
     - The total progress count.
       Only meaningful for ``task_update`` events.
       The scale may be an arbitrary positive integer.
       If the total count is not defined, this may be zero.
   * - ``message``
     - ``str``
     - An optional human-readable message indicating what the task is doing.
       It may be ``null``.
       For example, it may contain the name of agent or scaling group being worked on for image preload/unload APIs.

Check out :ref:`the session lifecycle events API <session-lifecycle-events>` for example client-side Javascript implementations to handle ``text/event-stream`` responses.

If you make the request for the tasks already finished, it may return either "404 Not Found" (the result is expired or the task ID is invalid) or a single event which is one of ``task_done``, ``task_fail``, or ``task_cancel`` followed by immediate  response disconnection.
Currently, the results for finished tasks may be archived up to one day (24 hours).
