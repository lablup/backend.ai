.. _event-bus:

Event Bus
=========

Concept
-------

Since the manager instances share nothing, there are needs to take action in other manager instance(s) once some tasks are done in a specific manager instance.

For instance, once a batch-mode session has started, its startup command must be executed.
The triggering of execution may be performed by any one of the manager instances, not only the instance that received the session creation API request.
The consumer pattern handles this case.

Another example is :ref:`the background task framework <bgtask>`.
A background task is executed in a specific manager instance, but the API requests to query background task status may be routed to any manager instance.
Here the progress updates of background tasks must be visible by all manager instances.
The subscriber pattern handles this case.

Event Dispatcher
----------------

Subscriber
~~~~~~~~~~

Regardless of which manager (or even agent) instance produces the event, get the notification.
All manager instances receive the same copy of event messages.

Internally this is implemented using Redis publish-subscribe channels.

Consumer
~~~~~~~~

Regardless of which manager (or even agent) instance produces the event, get the notification.
Only one manager instance receives the event message.

Internally this is implemented using Redis lists, where the Redis daemon wakes up the clients (here, manager instances) blocked at the ``BLPOP`` command in a round-robin fashion.


Producing events
----------------

Any manager instance or agent instance may produce event messages at any time.
The event messages are msgpack-encoded object with the following fields:

.. _event-message:

.. list-table::
   :header-rows: 1

   * - Field Name
     - Description
   * - ``event_name``
     - The name of event in snake_case
   * - ``agent_id``
     - The source of event. For manager instances, it is set to ``"manager"``.
   * - ``args``
     - Additional arguments as a tuple.  Each item must be also serializable as msgpack.

When produced, one copy of the message is published to ``"events.pubsub"`` key of the configured Redis instance, and another copy of the message is appended to ``"events.prodcons"`` key.
As long as there are at least one live manager instance, those keys are fetched immediately.
When there is no manager instance running, the messages will be accumulated in the Redis daemon.
If the manager instances start up again, those pending messages will be delivered to them again.


TODO: event dispatcher API reference


Synchronization
---------------

TODO
