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

    def test_getsockname(self):
        asyncio.run(self.getsockname())

    async def getsockname(self):
        addr = ('127.0.0.1', 0)
        socket = await asyncudp.create_socket(local_addr=addr)
        actual_addr, actual_port = socket.getsockname()
        self.assertTrue(actual_port > 0)
        self.assertEqual(actual_addr, '127.0.0.1')
        socket.close()

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

    def test_context(self):
        asyncio.run(self.context())

    async def context(self):
        server_addr = ('127.0.0.1', 13000)
        client_addr = ('127.0.0.1', 13001)

        server = await asyncudp.create_socket(local_addr=server_addr)
        client = await asyncudp.create_socket(local_addr=client_addr)

        async with server, client:
            client.sendto(b'local_addresses to server', server_addr)
            data, addr = await server.recvfrom()

            self.assertEqual(data, b'local_addresses to server')
            self.assertEqual(addr, client_addr)

            server.sendto(b'local_addresses to client', client_addr)
            data, addr = await client.recvfrom()

            self.assertEqual(data, b'local_addresses to client')
            self.assertEqual(addr, server_addr)

            self.assertEqual(server._transport.is_closing(), False)
            self.assertEqual(client._transport.is_closing(), False)

        self.assertEqual(server._transport.is_closing(), True)
        self.assertEqual(client._transport.is_closing(), True)

    def test_packets_queue_max_size(self):
        asyncio.run(self.packets_queue_max_size())

    async def packets_queue_max_size(self):
        server = await asyncudp.create_socket(local_addr=('127.0.0.1', 0),
                                              packets_queue_max_size=1)
        server_addr = server.getsockname()
        client = await asyncudp.create_socket(remote_addr=server_addr)

        client.sendto(b'local_addresses to server 1')
        client.sendto(b'local_addresses to server 2')
        await asyncio.sleep(1.0)
        data, _ = await server.recvfrom()
        self.assertEqual(data, b'local_addresses to server 1')

        client.sendto(b'local_addresses to server 3')
        data, _ = await server.recvfrom()
        self.assertEqual(data, b'local_addresses to server 3')

        server.close()
        client.close()

    def test_create_socket_reuse_port(self):
        asyncio.run(self.create_socket_reuse_port())

    async def create_socket_reuse_port(self):
        sock = await asyncudp.create_socket(local_addr=('127.0.0.1', 13003),
                                            reuse_port=True)

        with self.assertRaises(OSError):
            await asyncudp.create_socket(local_addr=('127.0.0.1', 13003))

        sock.close()
        sock2 = await asyncudp.create_socket(local_addr=('127.0.0.1', 13003),
                                             reuse_port=True)
        sock2.close()
