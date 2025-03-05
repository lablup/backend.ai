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


class AsyncContextMock(mock.Mock):
    """
    Provides a mock that can be used:

        async with mock():
          ...

    Example:

        # In the test code:
        mock_obj = unittest.mock.Mock()
        mock_obj.fetch.return_value = AsyncContextMock(
            status=200,
            json=mock.AsyncMock(return_value={'hello': 'world'})
        )
        mocker.patch('mypkg.mymod.MyClass', return_value=mock_obj)

        # In the tested code:
        obj = mpkg.mymod.MyClass()
        async with obj.fetch() as resp:
            # resp.status is 200
            result = await resp.json()
            # result is {'hello': 'world'}
    """

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class AsyncContextMagicMock(mock.MagicMock):
    """
    Provides a magic mock that can be used:

        async with mock():
          ...
    """

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class AsyncContextCoroutineMock(AsyncMock):
    """
    Provides a mock that can be used:

        async with (await mock(...)):
          ...

    Example:

        # In the test code:
        mock_obj = unittest.mock.AsyncMock()
        mock_obj.fetch.return_value = AsyncContextMock(
            status=200,
            json=mock.AsyncMock(return_value={'hello': 'world'})
        )
        mocker.patch('mypkg.mymod.MyClass', return_value=mock_obj)

        # In the tested code:
        obj = mpkg.mymod.MyClass()
        async with (await obj.fetch()) as resp:
            # resp.status is 200
            result = await resp.json()
            # result is {'hello': 'world'}
    """

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
