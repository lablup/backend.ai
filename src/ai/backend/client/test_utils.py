"""
A support module to async mocks in Python versiosn prior to 3.8.
"""

import sys
from unittest import mock
if sys.version_info >= (3, 8, 0):
    # Since Python 3.8, AsyncMock is now part of the stdlib.
    # Python 3.8 also adds magic-mocking async iterators and async context managers.
    from unittest.mock import AsyncMock
else:
    from asynctest import CoroutineMock as AsyncMock  # type: ignore


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
