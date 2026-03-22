from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any
from unittest.mock import MagicMock

import aiohttp
import pytest
from aioresponses import aioresponses


@asynccontextmanager
async def _mock_metrics_client_pool(
    responses: dict[str, str | Exception],
) -> AsyncGenerator[tuple[MagicMock, aioresponses], None]:
    """Set up aioresponses mocks and a mock ClientPool for metrics endpoint scraping.

    Args:
        responses: mapping of endpoint base URL (e.g. "http://10.0.0.1:8080")
                   to response body text or Exception to raise.

    Yields:
        (client_pool, mocked) where client_pool has load_client_session configured
        and mocked is the aioresponses instance for request assertion.
    """
    with aioresponses() as mocked:
        for endpoint, response in responses.items():
            url = f"{endpoint}/metrics"
            if isinstance(response, Exception):
                mocked.get(url, exception=response)
            else:
                mocked.get(url, body=response)

        async with AsyncExitStack() as stack:
            sessions: dict[str, aiohttp.ClientSession] = {}
            for endpoint in responses:
                session = await stack.enter_async_context(aiohttp.ClientSession(base_url=endpoint))
                sessions[endpoint] = session

            client_pool = MagicMock()
            client_pool.load_client_session = lambda key: sessions[key.endpoint]
            yield client_pool, mocked


@pytest.fixture
def mock_metrics_client_pool() -> Any:
    """Factory fixture: returns an async context manager for mock metrics ClientPool setup."""
    return _mock_metrics_client_pool
