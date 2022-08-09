from unittest import mock
from unittest.mock import AsyncMock


def mock_corofunc(return_value):
    """
    Return mock coroutine function.

    Python's default mock module does not support coroutines.
    """

    async def _mock_corofunc(*args, **kargs):
        return return_value

    return mock.Mock(wraps=_mock_corofunc)


async def mock_awaitable(**kwargs):
    """
    Mock awaitable.

    An awaitable can be a native coroutine object "returned from" a native
    coroutine function.
    """
    return AsyncMock(**kwargs)


class AsyncContextManagerMock:
    """
    Mock async context manager.

    Can be used to get around `async with` statement for testing.
    Must implement `__aenter__` and `__aexit__` which returns awaitable.
    Attributes of the awaitable (and self for convenience) can be set by
    passing `kwargs`.
    """

    def __init__(self, *args, **kwargs):
        self.context = kwargs
        for k, v in kwargs.items():
            setattr(self, k, v)

    async def __aenter__(self):
        return AsyncMock(**self.context)

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        pass


class MockableZMQAsyncSock:

    # Since zmq.Socket/zmq.asyncio.Socket uses a special AttributeSetter mixin which
    # breaks mocking of those instances as-is, we define a dummy socket interface
    # which does not have such side effects.

    @classmethod
    def create_mock(cls):
        return mock.Mock(cls())

    def bind(self, addr):
        pass

    def connect(self, addr):
        pass

    def close(self):
        pass

    async def send(self, frame):
        pass

    async def send_multipart(self, msg):
        pass

    async def recv(self):
        pass

    async def recv_multipart(self):
        pass
