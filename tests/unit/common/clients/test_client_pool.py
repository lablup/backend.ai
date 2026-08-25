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

CLEANUP_INTERVAL = 0.2
STREAM_CHUNKS = 6
CHUNK_DELAY = 0.1
READ_DEADLINE = 5.0


async def _slow_stream(request: web.Request) -> web.StreamResponse:
    response = web.StreamResponse()
    await response.prepare(request)
    for index in range(STREAM_CHUNKS):
        await response.write(f"chunk-{index}\n".encode())
        await asyncio.sleep(CHUNK_DELAY)
    await response.write_eof()
    return response


async def _read_stream(pool: ClientPool, upstream_url: str) -> list[bytes]:
    session = pool.load_client_session(ClientKey(endpoint=upstream_url, domain="test"))
    chunks: list[bytes] = []
    async with asyncio.timeout(READ_DEADLINE):
        async with session.get("/stream") as response:
            async for line in response.content:
                chunks.append(line)
    return chunks


async def _wait_closed(session: aiohttp.ClientSession) -> None:
    async with asyncio.timeout(READ_DEADLINE):
        while not session.closed:
            await asyncio.sleep(CLEANUP_INTERVAL / 4)


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
        keep_inflight_sessions=True,
    )
    try:
        yield client_pool
    finally:
        await client_pool.close()


@pytest.fixture
async def legacy_pool() -> AsyncIterator[ClientPool]:
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
    chunks = await _read_stream(pool, streaming_upstream_url)

    assert len(chunks) == STREAM_CHUNKS
    assert chunks[-1] == f"chunk-{STREAM_CHUNKS - 1}\n".encode()


async def test_idle_session_is_still_evicted(
    pool: ClientPool,
    streaming_upstream_url: str,
) -> None:
    key = ClientKey(endpoint=streaming_upstream_url, domain="test")
    session = pool.load_client_session(key)
    async with asyncio.timeout(READ_DEADLINE):
        async with session.get("/stream") as response:
            await response.read()

    await _wait_closed(session)

    assert pool.load_client_session(key) is not session


async def test_flag_off_keeps_time_based_eviction(
    legacy_pool: ClientPool,
    streaming_upstream_url: str,
) -> None:
    session = legacy_pool.load_client_session(
        ClientKey(endpoint=streaming_upstream_url, domain="test")
    )
    reader = asyncio.create_task(_read_stream(legacy_pool, streaming_upstream_url))
    try:
        await _wait_closed(session)
    finally:
        reader.cancel()

    assert session.closed
