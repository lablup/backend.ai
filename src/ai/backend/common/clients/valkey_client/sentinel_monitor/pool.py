from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator, Sequence

from aiotools import cancel_and_wait

from ai.backend.common.clients.valkey_client.sentinel_monitor.client import SentinelClient
from ai.backend.common.clients.valkey_client.sentinel_monitor.store import MasterStore
from ai.backend.common.clients.valkey_client.sentinel_monitor.types import (
    SentinelConnectionConfig,
    SentinelMaster,
)
from ai.backend.common.exception import ValkeySentinelMasterNotFound
from ai.backend.common.types import HostPortPair
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


class SentinelPool:
    """The clients of one Sentinel set. Their answers are merged by config epoch."""

    _service_name: str
    _clients: list[SentinelClient]
    _store: MasterStore
    _poll_interval: float
    # The poll task and one task per client merging what the client answers.
    _tasks: list[asyncio.Task[None]]

    def __init__(
        self,
        sentinel_addresses: Sequence[HostPortPair],
        service_name: str,
        config: SentinelConnectionConfig,
        poll_interval: float,
    ) -> None:
        if not sentinel_addresses:
            raise ValkeySentinelMasterNotFound("No Sentinel address is configured")
        self._service_name = service_name
        self._clients = [
            SentinelClient(address, service_name, config) for address in sentinel_addresses
        ]
        self._store = MasterStore()
        self._poll_interval = poll_interval
        self._tasks = []

    async def start(self) -> None:
        await asyncio.gather(*(client.start() for client in self._clients))
        self._tasks = [asyncio.create_task(self._follow(client)) for client in self._clients]
        self._tasks.append(asyncio.create_task(self._poll_loop()))

    async def close(self) -> None:
        for task in self._tasks:
            await cancel_and_wait(task)
        for client in self._clients:
            await client.close()
        self._store.close()

    def master(self) -> SentinelMaster | None:
        return self._store.get()

    def watch(self) -> AsyncGenerator[SentinelMaster]:
        """The master of the highest config epoch among the clients."""
        return self._store.watch()

    async def query(self) -> SentinelMaster:
        """Query every healthy Sentinel and return the master of the highest config epoch."""
        healthy_clients = [client for client in self._clients if client.healthy]
        results = await asyncio.gather(*(client.query() for client in healthy_clients))
        for master in results:
            if master is not None:
                self._merge(master)
        known = self._store.get()
        if known is None:
            raise ValkeySentinelMasterNotFound(
                f"Cannot find master for service '{self._service_name}'"
            )
        return known

    async def _follow(self, client: SentinelClient) -> None:
        async for master in client.watch():
            self._merge(master)

    def _merge(self, master: SentinelMaster) -> None:
        """An answer from an older config epoch is ignored."""
        known = self._store.get()
        if known is not None and master.config_epoch <= known.config_epoch:
            return
        if known is not None and known.address != master.address:
            log.info(
                "valkey master changed",
                service_name=self._service_name,
                previous_master=str(known.address),
                master=str(master.address),
            )
        self._store.set(master)

    async def _poll_loop(self) -> None:
        while True:
            await asyncio.sleep(self._poll_interval)
            try:
                await self.query()
            except ValkeySentinelMasterNotFound as e:
                log.warning(
                    "valkey master poll failed", exc_info=e, service_name=self._service_name
                )
