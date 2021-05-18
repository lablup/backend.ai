.. asyncudp documentation master file, created by
   sphinx-quickstart on Sat Apr 25 11:54:09 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. include:: ../README.rst

Examples
========

Client
------

.. code-block:: python

   import asyncio
   import asyncudp

   async def main():
       sock = await asyncudp.create_socket(remote_addr=('127.0.0.1', 9999))
       sock.sendto(b'Hello!')
       print(await sock.recvfrom())
       sock.close()

   asyncio.run(main())

Server
------

.. code-block:: python

   import asyncio
   import asyncudp

   async def main():
       sock = await asyncudp.create_socket(local_addr=('127.0.0.1', 9999))

       while True:
           data, addr = await sock.recvfrom()
           print(data, addr)
           sock.sendto(data, addr)

   asyncio.run(main())

Functions and classes
=====================

.. autofunction:: asyncudp.create_socket

.. autoclass:: asyncudp.Socket

   .. automethod:: asyncudp.Socket.close
   .. automethod:: asyncudp.Socket.sendto
   .. automethod:: asyncudp.Socket.recvfrom
