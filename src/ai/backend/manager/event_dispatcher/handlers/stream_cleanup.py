from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Final

from ai.backend.common.events.event_types.kernel.broadcast import (
    KernelTerminatingBroadcastEvent,
)
from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class StreamCleanupEventHandler:
    _db: ExtendedAsyncSAEngine
    _callbacks: list[Callable[[KernelRow], Awaitable[None]]]

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
        self._callbacks = []

    def register_cleanup_callback(self, callback: Callable[[KernelRow], Awaitable[None]]) -> None:
        self._callbacks.append(callback)

    async def handle_kernel_terminating_broadcast(
        self,
        _context: None,
        _source: AgentId,
        event: KernelTerminatingBroadcastEvent,
    ) -> None:
        try:
            kernel = await KernelRow.get_kernel(
                self._db,
                event.kernel_id,
                allow_stale=True,
            )
        except SessionNotFound:
            return
        if kernel.cluster_role == DEFAULT_ROLE:
            coros = [callback(kernel) for callback in self._callbacks]
            await asyncio.gather(*coros, return_exceptions=True)
