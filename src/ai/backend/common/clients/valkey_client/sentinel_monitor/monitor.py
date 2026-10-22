from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Sequence
from contextlib import aclosing
from typing import Final, override

from ai.backend.common.clients.valkey_client.sentinel_monitor.base import AbstractSentinelMonitor
from ai.backend.common.clients.valkey_client.sentinel_monitor.pool import SentinelPool
from ai.backend.common.clients.valkey_client.sentinel_monitor.types import (
    SentinelConnectionConfig,
)
from ai.backend.common.types import HostPortPair

_DEFAULT_POLL_INTERVAL: Final[float] = 60.0
_DEFAULT_QUERY_MIN_INTERVAL: Final[float] = 1.0


class SentinelMonitor(AbstractSentinelMonitor):
    """Tracks the master address of one service watched by a set of Sentinels."""

    _pool: SentinelPool
    _query_min_interval: float
    _query_lock: asyncio.Lock
    _queried_at: float

    def __init__(
        self,
        sentinel_addresses: Sequence[HostPortPair],
        service_name: str,
        *,
        password: str | None = None,
        use_tls: bool = False,
        tls_skip_verify: bool = False,
        poll_interval: float = _DEFAULT_POLL_INTERVAL,
        query_min_interval: float = _DEFAULT_QUERY_MIN_INTERVAL,
    ) -> None:
        config = SentinelConnectionConfig(
            password=password, use_tls=use_tls, tls_skip_verify=tls_skip_verify
        )
        self._pool = SentinelPool(sentinel_addresses, service_name, config, poll_interval)
        self._query_min_interval = query_min_interval
        self._query_lock = asyncio.Lock()
        self._queried_at = float("-inf")

    @override
    async def start(self) -> None:
        await self._pool.start()

    @override
    async def close(self) -> None:
        await self._pool.close()

    @override
    async def get_master(self) -> HostPortPair:
        known = self._pool.master()
        if known is not None:
            return known.address
        return await self._query()

    @override
    async def watch_master(self) -> AsyncGenerator[HostPortPair]:
        await self.get_master()
        last: HostPortPair | None = None
        async with aclosing(self._pool.watch()) as masters:
            async for master in masters:
                if master.address != last:
                    last = master.address
                    yield last

    @override
    async def check_master(self, address: HostPortPair) -> HostPortPair:
        known = self._pool.master()
        if known is not None and known.address != address:
            return known.address
        return await self._query()

    async def _query(self) -> HostPortPair:
        """Callers within the minimum interval of the last query get its result."""
        async with self._query_lock:
            loop = asyncio.get_running_loop()
            known = self._pool.master()
            if known is not None and loop.time() - self._queried_at < self._query_min_interval:
                return known.address
            master = await self._pool.query()
            self._queried_at = loop.time()
            return master.address
