import asyncio
import socket
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import partial
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from aiohttp import web
from aiohttp.typedefs import Handler
from multidict import CIMultiDict, CIMultiDictProxy

from ai.backend.common.clients.http_client.client_pool import ClientPool, tcp_client_session_factory
from ai.backend.common.endpoint_pool.exceptions import NoHealthyEndpointError
from ai.backend.common.endpoint_pool.pool import HealthyEndpointPool
from ai.backend.common.endpoint_pool.strategy import RoundRobinStrategy
from ai.backend.common.endpoint_pool.types import EndpointPoolSpec
from ai.backend.common.web.session import SESSION_KEY, STORAGE_KEY, Session
from ai.backend.web.errors import ManagerConnectionUnavailable
from ai.backend.web.proxy import (
    _direct_acquire,
    _run_proxy_request,
    web_handler,
    web_plugin_handler,
    websocket_handler,
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


async def test_proxy_converts_pool_unavailable_to_web_503(empty_pool: HealthyEndpointPool) -> None:
    request = MagicMock(spec=web.Request)
    with pytest.raises(ManagerConnectionUnavailable) as exc_info:
        await _run_proxy_request(
            request,
            endpoint_pool=empty_pool,
            path="/test",
            is_anonymous=True,
            http_headers_to_forward_extra=None,
            log_prefix="test",
        )
    error = exc_info.value
    assert error.status == 503
    assert isinstance(error.__cause__, NoHealthyEndpointError)
    assert error.extra_msg == error.__cause__.extra_msg


async def test_sticky_websocket_converts_pool_unavailable_to_web_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Session(None, data=None, new=True)
    session["api_endpoints"] = {"app1": "http://m1"}
    request = MagicMock(spec=web.Request)
    request.get = lambda key, default=None: {SESSION_KEY: session}.get(key, default)
    request.query = {"app": "app1"}
    async with _endpoint_pool(["http://m1"]) as endpoint_pool:
        # The saved endpoint passes the health check but is gone by the time it is acquired.
        monkeypatch.setattr(
            endpoint_pool,
            "acquire_sticky",
            MagicMock(side_effect=NoHealthyEndpointError("endpoint 'http://m1' is not healthy")),
        )
        with pytest.raises(ManagerConnectionUnavailable) as exc_info:
            await websocket_handler(request, endpoint_pool=endpoint_pool, is_anonymous=True)
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
            endpoint_pool=None,
            static_endpoint=str(upstream.make_url("/")),
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
    endpoint_pool.acquire = lambda *, exclude=(): _direct_acquire(upstream_url)
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


@dataclass
class _Upstream:
    url: str
    received: list[bytes] = field(default_factory=list)


@pytest.fixture
def refused_endpoint() -> str:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    return f"http://127.0.0.1:{port}/"


@pytest.fixture
async def ok_upstream(aiohttp_server: Any) -> _Upstream:
    upstream = _Upstream(url="")

    async def handler(request: web.Request) -> web.Response:
        upstream.received.append(await request.read())
        return web.json_response({})

    app = web.Application()
    app.router.add_route("*", "/{path:.*}", handler)
    server = await aiohttp_server(app)
    upstream.url = str(server.make_url("/"))
    return upstream


@pytest.fixture
async def failing_upstreams(aiohttp_server: Any) -> tuple[list[str], list[bytes]]:
    """Two upstreams that answer 500 and share one record of received requests."""
    received: list[bytes] = []

    async def handler(request: web.Request) -> web.Response:
        received.append(await request.read())
        return web.json_response({"title": "failed"}, status=500)

    urls: list[str] = []
    for _ in range(2):
        app = web.Application()
        app.router.add_route("*", "/{path:.*}", handler)
        server = await aiohttp_server(app)
        urls.append(str(server.make_url("/")))
    return urls, received


@pytest.fixture
async def disconnecting_upstreams() -> AsyncIterator[tuple[list[str], list[bytes]]]:
    """Two upstreams that read the request head and close without a response."""
    received: list[bytes] = []

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        received.append(await reader.readuntil(b"\r\n\r\n"))
        writer.close()

    servers = [await asyncio.start_server(handle, "127.0.0.1", 0) for _ in range(2)]
    try:
        yield [f"http://127.0.0.1:{s.sockets[0].getsockname()[1]}/" for s in servers], received
    finally:
        for server in servers:
            server.close()
            await server.wait_closed()


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


async def _proxy_client(
    aiohttp_client: Any, client_pool: ClientPool, endpoint_pool: HealthyEndpointPool
) -> Any:
    app = web.Application()
    app["config"] = MagicMock(
        api=MagicMock(domain="default", ssl_verify=False),
        service=MagicMock(enable_signup=True),
    )
    app["client_pool"] = client_pool
    app["stats"] = WebStats()
    app.router.add_route(
        "*",
        "/func/{path:.*$}",
        partial(web_handler, endpoint_pool=endpoint_pool, is_anonymous=True),
    )
    return await aiohttp_client(app)


class TestResendToAnotherEndpoint:
    async def test_refused_request_is_resent_with_its_body(
        self,
        aiohttp_client: Any,
        client_pool: ClientPool,
        refused_endpoint: str,
        ok_upstream: _Upstream,
    ) -> None:
        body = b"x" * (256 * 1024)
        async with _endpoint_pool([refused_endpoint, ok_upstream.url]) as endpoint_pool:
            client = await _proxy_client(aiohttp_client, client_pool, endpoint_pool)

            resp = await client.post("/func/folders", data=body)

            assert resp.status == 200
            assert ok_upstream.received == [body]
            assert not endpoint_pool.is_healthy(refused_endpoint)

    async def test_refused_request_without_another_endpoint_is_unreachable(
        self, aiohttp_client: Any, client_pool: ClientPool, refused_endpoint: str
    ) -> None:
        async with _endpoint_pool([refused_endpoint]) as endpoint_pool:
            client = await _proxy_client(aiohttp_client, client_pool, endpoint_pool)

            resp = await client.get("/func/folders")

            assert resp.status == 502

    async def test_error_response_is_passed_through_without_resend(
        self,
        aiohttp_client: Any,
        client_pool: ClientPool,
        failing_upstreams: tuple[list[str], list[bytes]],
    ) -> None:
        urls, received = failing_upstreams
        async with _endpoint_pool(urls) as endpoint_pool:
            client = await _proxy_client(aiohttp_client, client_pool, endpoint_pool)

            resp = await client.post("/func/folders", data=b"payload")

            assert resp.status == 500
            assert received == [b"payload"]

    async def test_disconnect_after_connect_is_not_resent(
        self,
        aiohttp_client: Any,
        client_pool: ClientPool,
        disconnecting_upstreams: tuple[list[str], list[bytes]],
    ) -> None:
        urls, received = disconnecting_upstreams
        async with _endpoint_pool(urls) as endpoint_pool:
            client = await _proxy_client(aiohttp_client, client_pool, endpoint_pool)

            resp = await client.post("/func/folders", data=b"payload")

            assert resp.status == 502
            assert len(received) == 1


@dataclass
class _SessionStore:
    session: Session
    saved: asyncio.Event


@pytest.fixture
async def ws_upstream(aiohttp_server: Any) -> _Upstream:
    """Echoes each websocket text message back once."""
    upstream = _Upstream(url="")

    async def handler(request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                upstream.received.append(msg.data.encode())
                await ws.send_str(msg.data)
        return ws

    app = web.Application()
    app.router.add_route("GET", "/{path:.*}", handler)
    server = await aiohttp_server(app)
    upstream.url = str(server.make_url("/"))
    return upstream


async def _ws_proxy_client(
    aiohttp_client: Any,
    client_pool: ClientPool,
    endpoint_pool: HealthyEndpointPool,
    store: _SessionStore,
) -> Any:
    storage = MagicMock()
    storage.save_session = AsyncMock(side_effect=lambda *_args: store.saved.set())

    @web.middleware
    async def session_middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
        request[SESSION_KEY] = store.session
        request[STORAGE_KEY] = storage
        return await handler(request)

    app = web.Application(middlewares=[session_middleware])
    app["config"] = MagicMock(
        api=MagicMock(domain="default", ssl_verify=False),
        service=MagicMock(enable_signup=True),
        session=MagicMock(login_session_extension_sec=None),
    )
    app["client_pool"] = client_pool
    app["stats"] = WebStats()
    app.router.add_route(
        "*",
        "/func/{path:.*$}",
        partial(web_handler, endpoint_pool=endpoint_pool, is_anonymous=True),
    )
    return await aiohttp_client(app)


class TestStickyWebsocket:
    async def test_refused_saved_endpoint_reconnects_to_another_and_saves_it(
        self,
        aiohttp_client: Any,
        client_pool: ClientPool,
        refused_endpoint: str,
        ws_upstream: _Upstream,
    ) -> None:
        session = Session(None, data=None, new=True)
        session["api_endpoints"] = {"app1": refused_endpoint}
        store = _SessionStore(session=session, saved=asyncio.Event())
        async with _endpoint_pool([refused_endpoint, ws_upstream.url]) as endpoint_pool:
            client = await _ws_proxy_client(aiohttp_client, client_pool, endpoint_pool, store)

            async with client.ws_connect("/func/stream?app=app1") as ws:
                await ws.send_str("ping")
                reply = await ws.receive_str()
            async with asyncio.timeout(5):
                await store.saved.wait()

            assert reply == "ping"
            assert ws_upstream.received == [b"ping"]
            assert session["api_endpoints"]["app1"] == ws_upstream.url
            assert not endpoint_pool.is_healthy(refused_endpoint)

    async def test_healthy_saved_endpoint_is_kept(
        self,
        aiohttp_client: Any,
        client_pool: ClientPool,
        refused_endpoint: str,
        ws_upstream: _Upstream,
    ) -> None:
        session = Session(None, data=None, new=True)
        session["api_endpoints"] = {"app1": ws_upstream.url}
        store = _SessionStore(session=session, saved=asyncio.Event())
        async with _endpoint_pool([refused_endpoint, ws_upstream.url]) as endpoint_pool:
            client = await _ws_proxy_client(aiohttp_client, client_pool, endpoint_pool, store)

            async with client.ws_connect("/func/stream?app=app1") as ws:
                await ws.send_str("ping")
                reply = await ws.receive_str()

            assert reply == "ping"
            assert ws_upstream.received == [b"ping"]
            assert not store.saved.is_set()
            assert endpoint_pool.is_healthy(refused_endpoint)
