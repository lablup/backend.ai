from collections.abc import AsyncIterator
from functools import partial
from typing import Any
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from multidict import CIMultiDict, CIMultiDictProxy

from ai.backend.common.clients.http_client.client_pool import ClientPool, tcp_client_session_factory
from ai.backend.web.proxy import _direct_acquire, _run_proxy_request
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
