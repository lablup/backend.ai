from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

from ai.backend.common.clients.valkey_client.sentinel_monitor.types import SentinelMaster


class MasterStore:
    """The latest master and a watch on its changes."""

    _master: SentinelMaster | None
    # Set and replaced whenever the master changes.
    _changed: asyncio.Event
    _closed: bool

    def __init__(self) -> None:
        self._master = None
        self._changed = asyncio.Event()
        self._closed = False

    def get(self) -> SentinelMaster | None:
        return self._master

    def set(self, master: SentinelMaster) -> None:
        if self._master == master:
            return
        self._master = master
        changed = self._changed
        self._changed = asyncio.Event()
        changed.set()

    async def watch(self) -> AsyncGenerator[SentinelMaster]:
        """Yield the current master, then the latest one after each change, until closed."""
        last: SentinelMaster | None = None
        while not self._closed:
            # Taken before yielding, so a change while the consumer is busy is not missed.
            changed = self._changed
            master = self._master
            if master is not None and master != last:
                last = master
                yield master
            await changed.wait()

    def close(self) -> None:
        self._closed = True
        self._changed.set()
