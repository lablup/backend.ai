from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from functools import partial

import pytest
from aiohttp import web

from ai.backend.common.clients.http_client.client_pool import (
    ClientKey,
    ClientPool,
    tcp_client_session_factory,
)

CLEANUP_INTERVAL = 0.2
"""Cleanup cadence for the pool under test, in seconds."""

STREAM_CHUNKS = 6
"""Chunks emitted by the stub upstream, spaced so the response outlives the interval."""

CHUNK_DELAY = 0.1
"""Delay between streamed chunks, in seconds."""

READ_DEADLINE = 5.0
"""Bound on the streamed read.

An evicted session stalls the read rather than raising, so without this the
regression hangs until the pytest timeout instead of failing.
"""


async def _slow_stream(request: web.Request) -> web.StreamResponse:
    response = web.StreamResponse()
    await response.prepare(request)
    for index in range(STREAM_CHUNKS):
        await response.write(f"chunk-{index}\n".encode())
        await asyncio.sleep(CHUNK_DELAY)
    await response.write_eof()
    return response


@pytest.fixture
async def streaming_upstream_url() -> AsyncIterator[str]:
    app = web.Application()
    app.router.add_get("/stream", _slow_stream)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    try:
        _, port = runner.addresses[0][:2]
        yield f"http://127.0.0.1:{port}"
    finally:
        await runner.cleanup()


@pytest.fixture
async def pool() -> AsyncIterator[ClientPool]:
    client_pool = ClientPool(
        partial(tcp_client_session_factory, ssl=False),
        cleanup_interval_seconds=CLEANUP_INTERVAL,
    )
    try:
        yield client_pool
    finally:
        await client_pool.close()


async def test_streaming_response_survives_a_cleanup_pass(
    pool: ClientPool,
    streaming_upstream_url: str,
) -> None:
    """A response outliving the cleanup interval must not have its session closed.

    `last_used` is stamped only when a session is acquired, so a single long request
    on an otherwise idle route looks idle to the cleanup loop. The loop must consult
    the connector rather than the timestamp alone.
    """
    session = pool.load_client_session(ClientKey(endpoint=streaming_upstream_url, domain="test"))

    chunks = []
    async with asyncio.timeout(READ_DEADLINE):
        async with session.get("/stream") as response:
            async for line in response.content:
                chunks.append(line)

    # The read spans STREAM_CHUNKS * CHUNK_DELAY, comfortably past CLEANUP_INTERVAL.
    assert len(chunks) == STREAM_CHUNKS
    assert chunks[-1] == f"chunk-{STREAM_CHUNKS - 1}\n".encode()


async def test_idle_session_is_still_evicted(
    pool: ClientPool,
    streaming_upstream_url: str,
) -> None:
    """The in-flight guard must not disable cleanup for genuinely idle sessions."""
    key = ClientKey(endpoint=streaming_upstream_url, domain="test")
    session = pool.load_client_session(key)
    async with session.get("/stream") as response:
        await response.read()

    await asyncio.sleep(CLEANUP_INTERVAL * 3)

    assert session.closed
    assert pool.load_client_session(key) is not session
