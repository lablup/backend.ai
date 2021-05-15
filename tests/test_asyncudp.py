import asyncio
import unittest

import asyncudp


class AsyncudpTest(unittest.TestCase):

    def test_local_addresses(self):
        asyncio.run(self.local_addresses())

    async def local_addresses(self):
        server_addr = ('127.0.0.1', 13000)
        client_addr = ('127.0.0.1', 13001)

        server = await asyncudp.create_socket(local_addr=server_addr)
        client = await asyncudp.create_socket(local_addr=client_addr)

        client.sendto(b'local_addresses to server', server_addr)
        data, addr = await server.recvfrom()

        self.assertEqual(data, b'local_addresses to server')
        self.assertEqual(addr, client_addr)

        server.sendto(b'local_addresses to client', client_addr)
        data, addr = await client.recvfrom()

        self.assertEqual(data, b'local_addresses to client')
        self.assertEqual(addr, server_addr)

        server.close()
        client.close()

    def test_remote_address(self):
        asyncio.run(self.remote_address())

    async def remote_address(self):
        server_addr = ('127.0.0.1', 13000)
        client_addr = ('127.0.0.1', 13001)

        server = await asyncudp.create_socket(local_addr=server_addr)
        client = await asyncudp.create_socket(local_addr=client_addr,
                                              remote_addr=server_addr)

        client.sendto(b'remote_address to server')
        data, addr = await server.recvfrom()

        self.assertEqual(data, b'remote_address to server')
        self.assertEqual(addr, client_addr)

        server.close()
        client.close()

    def test_cancel(self):
        asyncio.run(self.cancel())

    async def server_main(self, event):
        server = await asyncudp.create_socket(local_addr=('127.0.0.1', 13000))

        try:
            await server.recvfrom()
        except asyncio.CancelledError:
            server.close()
            event.set()

    async def cancel(self):
        event = asyncio.Event()
        task = asyncio.create_task(self.server_main(event))
        await asyncio.sleep(1.0)
        task.cancel()
        await event.wait()
