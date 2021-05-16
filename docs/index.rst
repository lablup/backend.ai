.. asyncudp documentation master file, created by
   sphinx-quickstart on Sat Apr 25 11:54:09 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :maxdepth: 2

Asyncio high level UDP sockets
==============================

.. include:: ../README.rst

Functions and classes
=====================

.. autofunction:: asyncudp.create_socket

.. autoclass:: asyncudp.Socket

   .. automethod:: asyncudp.Socket.close
   .. automethod:: asyncudp.Socket.sendto
   .. automethod:: asyncudp.Socket.recvfrom
