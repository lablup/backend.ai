Request API
===========

.. module:: ai.backend.client.request
.. currentmodule:: ai.backend.client.request

This module provides low-level API request/response interfaces
based on aiohttp.

Depending on the session object where the request is made from,
:class:`Request` and :class:`Response` differentiate their behavior:
works as plain Python functions or returns awaitables.

.. autoclass:: Request
   :members:
   :exclude-members: fetch, connect_websocket

   .. automethod:: fetch
      :with:
      :async-with: Response

   .. automethod:: connect_websocket
      :async-with: WebSocketResponse or its derivatives

.. autoclass:: Response
   :members:

.. autoclass:: WebSocketResponse
   :members:

.. autoclass:: FetchContextManager
   :members:

.. autoclass:: WebSocketContextManager
   :members:

.. autoclass:: AttachedFile
