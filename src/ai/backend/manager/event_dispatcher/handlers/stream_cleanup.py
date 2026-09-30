from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Final

import sqlalchemy as sa
from sqlalchemy.orm import noload

from ai.backend.common.events.event_types.kernel.broadcast import (
    KernelTerminatingBroadcastEvent,
)
from ai.backend.common.types import AgentId, KernelId
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine, execute_with_retry

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


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
            kernel = await self._fetch_kernel(event.kernel_id)
        except SessionNotFound:
            return
        if kernel.cluster_role == DEFAULT_ROLE:
            coros = [callback(kernel) for callback in self._callbacks]
            await asyncio.gather(*coros, return_exceptions=True)

    async def _fetch_kernel(self, kernel_id: KernelId) -> KernelRow:
        """Read the terminating kernel, in whatever status it is.

        The cleanup callbacks take the row itself, so the read stays here instead of
        going through a repository.
        """

        async def _query() -> KernelRow:
            async with self._db.begin_readonly_session() as db_sess:
                kernel = (
                    await db_sess.execute(
                        sa.select(KernelRow).where(KernelRow.id == kernel_id).options(noload("*"))
                    )
                ).scalar_one_or_none()
                if kernel is None:
                    raise SessionNotFound
                return kernel

        return await execute_with_retry(_query)
