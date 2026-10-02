from collections.abc import AsyncIterator
from functools import partial
from typing import Any
from unittest.mock import MagicMock

import pytest
from aiohttp import web

from ai.backend.common.clients.http_client.client_pool import ClientPool, tcp_client_session_factory
from ai.backend.web.proxy import _direct_acquire, web_handler, web_plugin_handler
from ai.backend.web.stats import WebStats


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
