from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from ai.backend.appproxy.common.types import ProxyProtocol, RouteInfo
from ai.backend.appproxy.worker.proxy.backend.tcp import TCPBackend


@pytest.fixture
def root_context() -> MagicMock:
    root_ctx = MagicMock()
    root_ctx.last_used_time_marker_redis_queue = asyncio.Queue()
    root_ctx.request_counter_redis_queue = asyncio.Queue()
    return root_ctx


@pytest.fixture
async def upstream_port() -> AsyncIterator[int]:
    async def hold_open(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            await reader.read()
        finally:
            writer.close()

    server = await asyncio.start_server(hold_open, "127.0.0.1", 0)
    try:
        yield server.sockets[0].getsockname()[1]
    finally:
        server.close()
        await server.wait_closed()


class TestTCPBackendClose:
    async def test_close_ends_live_connections(
        self, root_context: MagicMock, upstream_port: int
    ) -> None:
        routes = [
            RouteInfo(
                route_id=uuid4(),
                session_id=uuid4(),
                session_name=None,
                kernel_host="127.0.0.1",
                kernel_port=upstream_port,
                protocol=ProxyProtocol.TCP,
                traffic_ratio=1.0,
            )
        ]
        backend = TCPBackend(routes, root_context, MagicMock(id=uuid4()))
        bound = asyncio.Event()

        async def proxy(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            bound.set()
            await backend.bind(reader, writer)

        proxy_server = await asyncio.start_server(proxy, "127.0.0.1", 0)
        client_reader, client_writer = await asyncio.open_connection(
            "127.0.0.1", proxy_server.sockets[0].getsockname()[1]
        )
        try:
            await asyncio.wait_for(bound.wait(), timeout=5)
            async with asyncio.timeout(5):
                while not backend._live_writers:
                    await asyncio.sleep(0.01)

            await backend.close()

            assert await asyncio.wait_for(client_reader.read(), timeout=5) == b""
            async with asyncio.timeout(5):
                while backend._live_writers:
                    await asyncio.sleep(0.01)
        finally:
            client_writer.close()
            proxy_server.close()
            await proxy_server.wait_closed()
