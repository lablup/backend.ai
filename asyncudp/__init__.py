import asyncio
from .version import __version__


class _SocketProtocol:

    def __init__(self):
        self._packets = asyncio.Queue()

    def connection_made(self, transport):
        pass

    def connection_lost(self, transport):
        pass

    def datagram_received(self, data, addr):
        self._packets.put_nowait((data, addr))

    async def recvfrom(self):
        return await self._packets.get()


class Socket:
    """A UDP socket. Use :func:`~asyncudp.create_socket()` to create an
    instance of this class.

    """

    def __init__(self, transport, protocol):
        self._transport = transport
        self._protocol = protocol

    def close(self):
        """Close the socket.

        """

        self._transport.close()

    def sendto(self, data, addr=None):
        """Send given packet to given address ``addr``. Sends to
        ``remote_addr`` given to the constructor if ``addr`` is
        ``None``.

        >>> sock.sendto(b'Hi!')

        """

        self._transport.sendto(data, addr)

    async def recvfrom(self):
        """Receive a UDP packet.

        >>> data, addr = sock.recvfrom()

        """

        return await self._protocol.recvfrom()


async def create_socket(local_addr=None, remote_addr=None):
    """Create a UDP socket with given local and remote addresses.

    >>> sock = await asyncudp.create_socket(local_addr=('127.0.0.1', 9999))

    """

    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        _SocketProtocol,
        local_addr=local_addr,
        remote_addr=remote_addr)

    return Socket(transport, protocol)
