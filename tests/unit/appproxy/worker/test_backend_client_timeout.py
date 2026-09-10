from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from functools import partial

import aiohttp
import pytest
from aiohttp import web

from ai.backend.common.clients.http_client.client_pool import (
    ClientKey,
    ClientPool,
    tcp_client_session_factory,
)

UPSTREAM_DELAY = 0.3
"""How long the stub upstream holds a connection, in seconds."""


class TestBackendConnectTimeout:
    """``backend_connect_timeout`` bounds the wait for a free connector slot.

    With ``limit=1`` the second of two concurrent requests waits for the first to
    release its connection, and aiohttp charges that wait to ``ClientTimeout.connect``.
    """

    @pytest.fixture
    async def upstream_url(self) -> AsyncIterator[str]:
        async def slow_upstream(request: web.Request) -> web.Response:
            await asyncio.sleep(UPSTREAM_DELAY)
            return web.Response(text="ok")

        app = web.Application()
        app.router.add_get("/", slow_upstream)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        try:
            _, port = runner.addresses[0][:2]
            yield f"http://127.0.0.1:{port}"
        finally:
            await runner.cleanup()

    async def _fetch_twice(self, url: str, connect_timeout: float) -> list[int]:
        pool = ClientPool(
            partial(
                tcp_client_session_factory,
                timeout=aiohttp.ClientTimeout(
                    total=None,
                    connect=connect_timeout,
                    sock_connect=10.0,
                    sock_read=None,
                ),
                ssl=False,
                limit=1,
            ),
            cleanup_interval_seconds=600,
        )
        session = pool.load_client_session(ClientKey(endpoint=url, domain="test"))

        async def fetch() -> int:
            async with session.get("/") as resp:
                await resp.read()
                return resp.status

        try:
            return list(await asyncio.gather(fetch(), fetch()))
        finally:
            await pool.close()

    async def test_zero_leaves_pool_wait_unbounded(self, upstream_url: str) -> None:
        assert await self._fetch_twice(upstream_url, 0) == [200, 200]

    async def test_finite_value_fails_the_queued_request(self, upstream_url: str) -> None:
        with pytest.raises(aiohttp.ConnectionTimeoutError):
            await self._fetch_twice(upstream_url, UPSTREAM_DELAY / 2)
