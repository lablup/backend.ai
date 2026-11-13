import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import partial
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
import yarl
from aiohttp import web
from aiohttp.typedefs import Handler
from multidict import CIMultiDict, CIMultiDictProxy

from ai.backend.common.clients.http_client.client_pool import ClientPool, tcp_client_session_factory
from ai.backend.common.web.session import SESSION_KEY, Session
from ai.backend.web.clients.endpoint_pool import (
    EndpointPoolSpec,
    HealthyEndpointPool,
    RoundRobinStrategy,
)
from ai.backend.web.proxy import (
    _direct_acquire,
    _run_proxy_request,
    web_handler,
    web_plugin_handler,
)
from ai.backend.web.server import client_ctx


@asynccontextmanager
async def _endpoint_pool(endpoints: list[str]) -> AsyncIterator[HealthyEndpointPool]:
    pool = HealthyEndpointPool(
        endpoints=endpoints,
        spec=EndpointPoolSpec("/readyz", 3600, 3, 60, 1),
        strategy=RoundRobinStrategy(),
        probe_session_factory=lambda _endpoint: MagicMock(close=AsyncMock()),
    )
    try:
        yield pool
    finally:
        await pool.close()


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


@pytest.fixture
async def server_client_pool() -> AsyncIterator[ClientPool]:
    config = MagicMock(api=MagicMock(ssl_verify=False, connection_limit=10))
    async with client_ctx(config, web.Application()) as pool:
        try:
            yield pool
        finally:
            await pool.close()


@pytest.fixture
async def cookie_upstream(aiohttp_server: Any) -> tuple[str, list[str | None]]:
    """Records each request's Cookie header and sets a cookie on every response."""
    received: list[str | None] = []

    async def handler(request: web.Request) -> web.Response:
        received.append(request.headers.get("Cookie"))
        resp = web.json_response({})
        resp.set_cookie("upstream", "set-by-manager")
        return resp

    app = web.Application()
    app.router.add_route("*", "/{path:.*}", handler)
    server = await aiohttp_server(app)
    return str(server.make_url("/")), received


async def _cookie_proxy_client(
    aiohttp_client: Any,
    client_pool: ClientPool,
    upstream_url: str,
    *,
    is_anonymous: bool,
) -> Any:
    session = Session(None, data=None, new=True)
    session["authenticated"] = True
    session["token"] = {"type": "keypair", "access_key": "AKTEST", "secret_key": "SKTEST"}

    @web.middleware
    async def session_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
        request[SESSION_KEY] = session
        return await handler(request)

    endpoint_pool = MagicMock()
    endpoint_pool.acquire = lambda: _direct_acquire(upstream_url)
    app = web.Application(middlewares=[session_middleware])
    app["config"] = MagicMock(
        api=MagicMock(domain="default", ssl_verify=False),
        service=MagicMock(enable_signup=True),
    )
    app["client_pool"] = client_pool
    app.router.add_route(
        "*",
        "/func/{path:.*$}",
        partial(web_handler, endpoint_pool=endpoint_pool, is_anonymous=is_anonymous),
    )
    app.router.add_route(
        "*",
        "/pipeline/{path:.*$}",
        partial(web_plugin_handler, endpoint_pool=endpoint_pool, is_anonymous=is_anonymous),
    )
    return await aiohttp_client(app, cookie_jar=aiohttp.DummyCookieJar())


@pytest.mark.parametrize("prefix", ["/func", "/pipeline"])
@pytest.mark.parametrize("is_anonymous", [True, False])
class TestRequestCookieForwarding:
    async def test_each_request_carries_only_its_own_cookie(
        self,
        aiohttp_client: Any,
        server_client_pool: ClientPool,
        cookie_upstream: tuple[str, list[str | None]],
        prefix: str,
        is_anonymous: bool,
    ) -> None:
        endpoint, received = cookie_upstream
        client = await _cookie_proxy_client(
            aiohttp_client, server_client_pool, endpoint, is_anonymous=is_anonymous
        )
        sent = ["a=1", "b=2; c=3", "d=4"]
        for cookie in sent:
            resp = await client.get(f"{prefix}/test", headers={"Cookie": cookie})
            assert resp.status == 200

        assert received == sent

    async def test_cookieless_request_carries_no_cookie_after_cookie_requests(
        self,
        aiohttp_client: Any,
        server_client_pool: ClientPool,
        cookie_upstream: tuple[str, list[str | None]],
        prefix: str,
        is_anonymous: bool,
    ) -> None:
        endpoint, received = cookie_upstream
        client = await _cookie_proxy_client(
            aiohttp_client, server_client_pool, endpoint, is_anonymous=is_anonymous
        )
        for idx in range(3):
            await client.get(f"{prefix}/test", headers={"Cookie": f"user{idx}=secret{idx}"})
        resp = await client.get(f"{prefix}/test")

        assert resp.status == 200
        assert received[-1] is None


class TestDotSegmentPath:
    @pytest.mark.parametrize(
        "url",
        [
            "/func/cloud/..%2Fauth%2Fauthorize",
            "/func/v2/x/public/%2E%2E%2F%2E%2E%2F%2E%2E%2Fadmin%2Fgql",
            "/func/cloud/.%2Fauth",
            "/pipeline/cloud/..%2Fauth%2Fauthorize",
        ],
    )
    async def test_dot_segment_is_rejected_before_upstream(
        self,
        aiohttp_client: Any,
        server_client_pool: ClientPool,
        cookie_upstream: tuple[str, list[str | None]],
        url: str,
    ) -> None:
        endpoint, received = cookie_upstream
        client = await _cookie_proxy_client(
            aiohttp_client, server_client_pool, endpoint, is_anonymous=True
        )
        resp = await client.get(yarl.URL(url, encoded=True))

        assert resp.status == 400
        assert received == []

    @pytest.mark.parametrize(
        "url", ["/func/cloud/signup", "/func/v2/x/public/y", "/pipeline/folders/a..b"]
    )
    async def test_path_without_dot_segment_is_proxied(
        self,
        aiohttp_client: Any,
        server_client_pool: ClientPool,
        cookie_upstream: tuple[str, list[str | None]],
        url: str,
    ) -> None:
        endpoint, received = cookie_upstream
        client = await _cookie_proxy_client(
            aiohttp_client, server_client_pool, endpoint, is_anonymous=True
        )
        resp = await client.get(url)

        assert resp.status == 200
        assert len(received) == 1


@pytest.fixture
async def streaming_upstream(aiohttp_server: Any) -> str:
    """An upstream that keeps streaming the response body until its peer closes."""

    async def handler(request: web.Request) -> web.StreamResponse:
        resp = web.StreamResponse()
        await resp.prepare(request)
        while True:
            await resp.write(b"x" * 1024)
            await asyncio.sleep(0.01)

    app = web.Application()
    app.router.add_route("*", "/{path:.*}", handler)
    server = await aiohttp_server(app)
    return str(server.make_url("/"))


class TestClientDisconnect:
    async def test_client_disconnect_is_not_counted_against_upstream(
        self,
        aiohttp_client: Any,
        server_client_pool: ClientPool,
        streaming_upstream: str,
    ) -> None:
        finished: asyncio.Queue[None] = asyncio.Queue()

        @web.middleware
        async def notify_finished(request: web.Request, handler: Handler) -> web.StreamResponse:
            try:
                return await handler(request)
            finally:
                finished.put_nowait(None)

        async with _endpoint_pool([streaming_upstream]) as endpoint_pool:
            app = web.Application(middlewares=[notify_finished])
            app["config"] = MagicMock(
                api=MagicMock(domain="default", ssl_verify=False),
                service=MagicMock(enable_signup=True),
            )
            app["client_pool"] = server_client_pool
            app.router.add_route(
                "*",
                "/func/{path:.*$}",
                partial(web_handler, endpoint_pool=endpoint_pool, is_anonymous=True),
            )
            client = await aiohttp_client(app)

            # The failure threshold is 3, so 3 disconnects would mark the endpoint unhealthy.
            for _ in range(3):
                resp = await client.get("/func/folders")
                await resp.content.readany()
                resp.close()
                await asyncio.wait_for(finished.get(), timeout=5)

            assert endpoint_pool.is_healthy(streaming_upstream)
