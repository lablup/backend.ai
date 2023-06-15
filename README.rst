Asyncio high level UDP sockets
==============================

Asyncio high level UDP sockets.

Project homepage: https://github.com/eerimoq/asyncudp

Documentation: https://asyncudp.readthedocs.org/en/latest

Installation
============

.. code-block:: python

   $ pip install asyncudp

Example client
==============

.. code-block:: python

   import asyncio
   import asyncudp

   async def main():
       sock = await asyncudp.create_socket(remote_addr=('127.0.0.1', 9999))
       sock.sendto(b'Hello!')
       print(await sock.recvfrom())
       sock.close()

   asyncio.run(main())

Example server
==============

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

Test
====

.. code-block::

   $ python3 -m unittest
