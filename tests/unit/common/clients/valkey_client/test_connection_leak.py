"""
Regression test for the reconnect connection leak.

The injected fault is the production fingerprint: a listener that completes the TCP
handshake and then never speaks the Valkey protocol, so every connection reaches
ESTABLISHED but the server never sees a command. A round of failed `connect()` calls
must leave no socket behind on the server side.
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Final, Self

import pytest
from glide import ClosingError

from ai.backend.common.clients.valkey_client.client import (
    ValkeyStandaloneClient,
    ValkeyStandaloneTarget,
)

# One round mirrors a reconnect cycle of three MonitoringValkeyClients
# (operation + monitor client each). The leak only shows from the second round on.
_CLIENTS_PER_ROUND: Final[int] = 6
_ROUNDS: Final[int] = 3
_REQUEST_TIMEOUT: Final[int] = 300
_SETTLE_TIMEOUT: Final[float] = 2.0
_SETTLE_POLL_INTERVAL: Final[float] = 0.05


class _StallServer:
    """Accept connections and never answer, tracking how many are still open."""

    live: int
    port: int

    def __init__(self) -> None:
        self.live = 0
        self.port = 0
        self._server: asyncio.Server | None = None

    async def start(self) -> Self:
        self._server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        self.port = self._server.sockets[0].getsockname()[1]
        return self

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.live += 1
        try:
            while await reader.read(65536):
                pass
        except OSError:
            pass
        finally:
            self.live -= 1
            writer.close()

    async def settled_live_count(self) -> int:
        """Wait for the abandoned sockets to close, then report what is still open."""
        loop = asyncio.get_running_loop()
        deadline = loop.time() + _SETTLE_TIMEOUT
        while self.live > 0 and loop.time() < deadline:
            await asyncio.sleep(_SETTLE_POLL_INTERVAL)
        return self.live


@asynccontextmanager
async def _stall_server() -> AsyncIterator[_StallServer]:
    server = await _StallServer().start()
    try:
        yield server
    finally:
        await server.stop()


async def _failing_connect(target: ValkeyStandaloneTarget, name: str) -> None:
    client = ValkeyStandaloneClient(target, 0, name)
    with pytest.raises(ClosingError):
        await client.connect()
    await client.disconnect()


async def test_failed_connect_leaves_no_open_connection() -> None:
    async with _stall_server() as server:
        target = ValkeyStandaloneTarget(
            address=f"127.0.0.1:{server.port}",
            request_timeout=_REQUEST_TIMEOUT,
        )
        live_counts: list[int] = []
        for round_idx in range(_ROUNDS):
            await asyncio.gather(*[
                _failing_connect(target, f"leak-probe-{round_idx}-{client_idx}")
                for client_idx in range(_CLIENTS_PER_ROUND)
            ])
            live_counts.append(await server.settled_live_count())

        assert live_counts == [0] * _ROUNDS
