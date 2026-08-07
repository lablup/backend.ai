from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from functools import partial

import aiohttp
import pytest
from aiohttp import web

from ai.backend.appproxy.worker.proxy.backend.http import BACKEND_CLIENT_TIMEOUT
from ai.backend.common.clients.http_client.client_pool import (
    ClientKey,
    ClientPool,
    tcp_client_session_factory,
)

UPSTREAM_DELAY = 0.3
"""How long the stub upstream holds a connection, in seconds."""


async def _slow_upstream(request: web.Request) -> web.Response:
    await asyncio.sleep(UPSTREAM_DELAY)
    return web.Response(text="ok")


@pytest.fixture
async def upstream_url() -> AsyncIterator[str]:
    app = web.Application()
    app.router.add_get("/", _slow_upstream)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    try:
        _, port = runner.addresses[0][:2]
        yield f"http://127.0.0.1:{port}"
    finally:
        await runner.cleanup()


def _make_pool(url: str, timeout: aiohttp.ClientTimeout) -> ClientPool:
    return ClientPool(
        partial(
            tcp_client_session_factory,
            timeout=timeout,
            auto_decompress=False,
            ssl=False,
            limit=1,  # saturate the connector with the second concurrent request
        ),
        cleanup_interval_seconds=600,
    )


async def _fetch_concurrently(pool: ClientPool, url: str, count: int) -> list[int]:
    session = pool.load_client_session(ClientKey(endpoint=url, domain="test"))

    async def fetch() -> int:
        async with session.get("/") as resp:
            await resp.read()
            return resp.status

    return await asyncio.gather(*(fetch() for _ in range(count)))


async def test_pool_wait_is_not_bounded_by_connect_timeout(upstream_url: str) -> None:
    """Requests queued behind a saturated connector must complete, not time out.

    With ``limit=1`` the second request waits for the first to release its
    connection. aiohttp charges that wait to ``ClientTimeout.connect``, so the
    production timeout must leave ``connect`` unset for the wait to be unbounded.
    """
    assert BACKEND_CLIENT_TIMEOUT.connect is None
    pool = _make_pool(upstream_url, BACKEND_CLIENT_TIMEOUT)
    try:
        statuses = await _fetch_concurrently(pool, upstream_url, 2)
    finally:
        await pool.close()
    assert statuses == [200, 200]


async def test_finite_connect_timeout_fails_the_queued_request(upstream_url: str) -> None:
    """Pins the regression: a finite ``connect`` budget kills the queued request.

    This is the pre-fix configuration. It asserts the failure is caused by pool
    queueing rather than by an unreachable upstream, so the fix above is not
    merely masking a slow connect.
    """
    doomed_timeout = aiohttp.ClientTimeout(
        total=None,
        connect=UPSTREAM_DELAY / 2,
        sock_connect=10.0,
        sock_read=None,
    )
    pool = _make_pool(upstream_url, doomed_timeout)
    try:
        with pytest.raises(aiohttp.ConnectionTimeoutError):
            await _fetch_concurrently(pool, upstream_url, 2)
    finally:
        await pool.close()
