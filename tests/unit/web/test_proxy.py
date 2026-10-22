from collections.abc import AsyncIterator
from functools import partial
from typing import Any
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from multidict import CIMultiDict, CIMultiDictProxy

from ai.backend.common.clients.http_client.client_pool import ClientPool, tcp_client_session_factory
from ai.backend.common.endpoint_pool.exceptions import NoHealthyEndpointError
from ai.backend.common.endpoint_pool.pool import HealthyEndpointPool
from ai.backend.common.endpoint_pool.strategy import RoundRobinStrategy
from ai.backend.common.endpoint_pool.types import EndpointPoolSpec
from ai.backend.web.errors import ManagerConnectionUnavailable
from ai.backend.web.proxy import (
    _direct_acquire,
    _run_proxy_request,
    web_handler,
    web_plugin_handler,
)
from ai.backend.web.stats import WebStats


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


@pytest.fixture
async def client_pool() -> AsyncIterator[ClientPool]:
    pool = ClientPool(
        partial(tcp_client_session_factory, ssl=False, limit=10, limit_per_host=5),
        cleanup_interval_seconds=100,
    )
    try:
        yield pool
    finally:
        await pool.close()


async def test_proxy_forwards_act_as_header_upstream(
    aiohttp_server: Any, aiohttp_client: Any, client_pool: ClientPool
) -> None:
    received: list[CIMultiDictProxy[str]] = []

    async def upstream_handler(request: web.Request) -> web.Response:
        received.append(request.headers)
        return web.json_response({})

    upstream_app = web.Application()
    upstream_app.router.add_route("*", "/{path:.*}", upstream_handler)
    upstream = await aiohttp_server(upstream_app)

    async def frontend_handler(request: web.Request) -> web.StreamResponse:
        return await _run_proxy_request(
            request,
            acquire_ctx=_direct_acquire(str(upstream.make_url("/"))),
            path=request.match_info["path"],
            is_anonymous=True,
            http_headers_to_forward_extra=None,
            log_prefix="test",
        )

    frontend_app = web.Application()
    frontend_app["config"] = MagicMock(api=MagicMock(domain="default", ssl_verify=False))
    frontend_app["client_pool"] = client_pool
    frontend_app["stats"] = WebStats()
    frontend_app.router.add_route("*", "/func/{path:.*}", frontend_handler)
    client = await aiohttp_client(frontend_app)

    act_as = "f38dea23-50fa-42a0-b5ae-338f5f4693f4"
    resp = await client.get("/func/admin/gql", headers=CIMultiDict({"X-BackendAI-Act-As": act_as}))

    assert resp.status == 200
    assert received[0]["X-BackendAI-Act-As"] == act_as


@pytest.fixture
async def signup_upstream(aiohttp_server: Any) -> AsyncIterator[tuple[str, list[str]]]:
    received: list[str] = []

    async def upstream_handler(request: web.Request) -> web.Response:
        received.append(request.path)
        return web.json_response({})

    upstream_app = web.Application()
    upstream_app.router.add_route("*", "/{path:.*}", upstream_handler)
    upstream = await aiohttp_server(upstream_app)
    yield str(upstream.make_url("/")), received


async def _signup_gated_client(
    aiohttp_client: Any, client_pool: ClientPool, upstream_url: str, *, enable_signup: bool
) -> Any:
    endpoint_pool = MagicMock()
    endpoint_pool.acquire = lambda: _direct_acquire(upstream_url)
    app = web.Application()
    app["config"] = MagicMock(
        api=MagicMock(domain="default", ssl_verify=False),
        service=MagicMock(enable_signup=enable_signup),
    )
    app["client_pool"] = client_pool
    app["stats"] = WebStats()
    app.router.add_route(
        "POST",
        "/func/{path:auth/signup}",
        partial(web_plugin_handler, endpoint_pool=endpoint_pool, is_anonymous=True),
    )
    app.router.add_route(
        "*",
        "/func/{path:.*$}",
        partial(web_handler, endpoint_pool=endpoint_pool, is_anonymous=True),
    )
    return await aiohttp_client(app)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/func/auth/signup"),
        ("POST", "/func/auth/signup/"),
        ("PUT", "/func/auth/signup"),
    ],
)
async def test_signup_is_rejected_when_disabled(
    aiohttp_client: Any,
    client_pool: ClientPool,
    signup_upstream: tuple[str, list[str]],
    method: str,
    path: str,
) -> None:
    upstream_url, received = signup_upstream
    client = await _signup_gated_client(
        aiohttp_client, client_pool, upstream_url, enable_signup=False
    )

    resp = await client.request(method, path, json={"email": "user@example.com"})

    assert resp.status == 403
    assert received == []


async def test_signup_is_forwarded_when_enabled(
    aiohttp_client: Any, client_pool: ClientPool, signup_upstream: tuple[str, list[str]]
) -> None:
    upstream_url, received = signup_upstream
    client = await _signup_gated_client(
        aiohttp_client, client_pool, upstream_url, enable_signup=True
    )

    resp = await client.post("/func/auth/signup", json={"email": "user@example.com"})

    assert resp.status == 200
    assert received == ["/auth/signup"]
