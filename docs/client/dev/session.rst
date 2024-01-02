Client Session
==============

Client Session Objects
----------------------

.. module:: ai.backend.client.session
.. currentmodule:: ai.backend.client.session

This module is the first place to begin with your Python programs
that use Backend.AI API functions.

The high-level API functions cannot be used alone -- you must initiate a client
session first because each session provides *proxy attributes* that represent API
functions and run on the session itself.

To achieve this, during initialization session objects internally construct new types
by combining the :class:`~ai.backend.client.base.BaseFunction` class with the
attributes in each API function classes, and makes the new types bound to itself.
Creating new types every time when creating a new session instance may look weird,
but it is the most convenient way to provide *class-methods* in the API function
classes to work with specific *session instances*.

When designing your application, please note that session objects are intended to
live long following the process' lifecycle, instead of to be created and disposed
whenever making API requests.

.. autoclass:: BaseSession
  :members:

.. autoclass:: Session
  :members:

.. autoclass:: AsyncSession
  :members:
