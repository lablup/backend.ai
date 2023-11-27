import pytest

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.request import Request
from ai.backend.client.session import AsyncSession, Session

pytestmark = pytest.mark.integration


def test_connection():
    with Session():
        request = Request("GET", "/")
        with request.fetch() as resp:
            assert "version" in resp.json()


def test_not_found():
    with Session():
        request = Request("GET", "/invalid-url-wow")
        with pytest.raises(BackendAPIError) as e:
            with request.fetch():
                pass
        assert e.value.status == 404
        request = Request("GET", "/auth/uh-oh")
        with pytest.raises(BackendAPIError) as e:
            with request.fetch():
                pass
        assert e.value.status == 404


@pytest.mark.asyncio
async def test_async_connection():
    async with AsyncSession():
        request = Request("GET", "/")
        async with request.fetch() as resp:
            assert "version" in await resp.json()
