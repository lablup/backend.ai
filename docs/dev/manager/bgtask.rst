.. _bgtask:

Background Task Framework
=========================

Motivation
----------

The API handlers must return the processing result as quickly as possible to keep responsiveness of client applications.
A common technique is to use a pool of background workers and let clients query the progress of requested tasks.
There are many frameworks and libraries to assist implementation of such long-running background tasks for web services such as `Celery <https://docs.celeryproject.org/en/stable/>`_.

Backend.AI does not use external task-queue services because most of them are too complicated or have limited support for asyncio.
Backend.AI Manager has a small, minimal framework to directly execute long-running background tasks in the manager instance that received the API request.
The background tasks are wrapped as a separate asyncio task, separate to the API handler task implicitly created by aiohttp.
The clients can query the task status with a reference ID via any manager instance, because the progress updates of a background task is propagated via :ref:`the event bus <event-bus>`.

Example scenarios:

* When a client invokes the container registry rescan API, the API handler creates a background task and returns the task ID immediately.
  The client keeps track of the progress and result of registry scanning via the background task API using the returned task ID.


Writing BGTask-enabled API Handler
----------------------------------

TODO


.. _bgtask-sse-api:

The SSE API for Background Tasks
--------------------------------

TOD
