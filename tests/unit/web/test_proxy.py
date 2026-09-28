from collections.abc import AsyncIterator
from unittest.mock import MagicMock

import pytest
from aiohttp import web

from ai.backend.common.endpoint_pool.exceptions import NoHealthyEndpointError
from ai.backend.common.endpoint_pool.pool import HealthyEndpointPool
from ai.backend.common.endpoint_pool.strategy import RoundRobinStrategy
from ai.backend.common.endpoint_pool.types import EndpointPoolSpec
from ai.backend.web.errors import ManagerConnectionUnavailable
from ai.backend.web.proxy import _run_proxy_request


@pytest.fixture
async def empty_pool() -> AsyncIterator[HealthyEndpointPool]:
    pool = HealthyEndpointPool(
        endpoints=[],
        spec=EndpointPoolSpec("/readyz", 3600, 3, 60, 1),
        strategy=RoundRobinStrategy(),
        probe_session_factory=MagicMock(),
    )
    try:
        yield pool
    finally:
        await pool.close()


@pytest.mark.parametrize("sticky", [False, True])
async def test_proxy_converts_pool_unavailable_to_web_503(
    empty_pool: HealthyEndpointPool, sticky: bool
) -> None:
    request = MagicMock(spec=web.Request)
    context = empty_pool.acquire_sticky("http://missing") if sticky else empty_pool.acquire()
    with pytest.raises(ManagerConnectionUnavailable) as exc_info:
        await _run_proxy_request(
            request,
            acquire_ctx=context,
            path="/test",
            is_anonymous=True,
            http_headers_to_forward_extra=None,
            log_prefix="test",
        )
    error = exc_info.value
    assert error.status == 503
    assert isinstance(error.__cause__, NoHealthyEndpointError)
    assert error.extra_msg == error.__cause__.extra_msg
