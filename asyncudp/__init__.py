import asyncio
from .version import __version__


class ClosedError(Exception):
    pass


class _SocketProtocol:

    def __init__(self):
        self._error = None
        self._packets = asyncio.Queue()

    def connection_made(self, transport):
        pass

    def connection_lost(self, transport):
        self._packets.put_nowait(None)

    def datagram_received(self, data, addr):
        self._packets.put_nowait((data, addr))

    def error_received(self, exc):
        self._error = exc
        self._packets.put_nowait(None)

    async def recvfrom(self):
        return await self._packets.get()

    def raise_if_error(self):
        if self._error is None:
            return

        error = self._error
        self._error = None

        raise error


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

        Raises an error if a connection error has occurred.

        >>> sock.sendto(b'Hi!')

        """

        self._transport.sendto(data, addr)
        self._protocol.raise_if_error()

    async def recvfrom(self):
        """Receive a UDP packet.

        Raises ClosedError on connection error, often by calling the
        close() method from another task. May raise other errors as
        well.

        >>> data, addr = sock.recvfrom()

        """

        packet = await self._protocol.recvfrom()
        self._protocol.raise_if_error()

        if packet is None:
            raise ClosedError()

        return packet

    def getsockname(self):
        """Get bound infomation.

        >>> local_address, local_port = sock.getsockname()

        """

        return self._transport.get_extra_info('sockname')

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        self.close()


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
