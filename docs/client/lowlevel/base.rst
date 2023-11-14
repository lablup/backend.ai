Base Function
=============

.. module:: ai.backend.client.func.base

This module defines a few utilities that ease
complexities to support both synchronous and asynchronous API functions, using
some tricks with Python metaclasses.

Unless your are contributing to the client SDK, probably you won't
have to use this module directly.

.. currentmodule:: ai.backend.client.func.base

.. autoclass:: APIFunctionMeta

.. autoclass:: BaseFunction

.. autofunction:: api_function
  :decorator:
