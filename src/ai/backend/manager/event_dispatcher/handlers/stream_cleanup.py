from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Final

from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.events.event_types.kernel.broadcast import (
    KernelTerminatingBroadcastEvent,
)
from ai.backend.common.types import AgentId
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.models.kernel.searchable_fields import KernelSearchableFields
from ai.backend.manager.models.kernel.searchers import KernelSearcher
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


class StreamCleanupEventHandler:
    _repository: SchedulerRepository
    _callbacks: list[Callable[[KernelInfo], Awaitable[None]]]

    def __init__(self, repository: SchedulerRepository) -> None:
        self._repository = repository
        self._callbacks = []

    def register_cleanup_callback(self, callback: Callable[[KernelInfo], Awaitable[None]]) -> None:
        self._callbacks.append(callback)

    async def handle_kernel_terminating_broadcast(
        self,
        _context: None,
        _source: AgentId,
        event: KernelTerminatingBroadcastEvent,
    ) -> None:
        result = await self._repository.search_kernels_for_handler(
            KernelSearcher(
                pagination=NoPagination(),
                conditions=[
                    KernelSearchableFields.own.id.filter.equals(
                        UUIDEqualMatchSpec(value=event.kernel_id, negated=False)
                    )
                ],
            )
        )
        if not result.items:
            return
        kernel = result.items[0]
        if kernel.cluster.cluster_role == DEFAULT_ROLE:
            coros = [callback(kernel) for callback in self._callbacks]
            await asyncio.gather(*coros, return_exceptions=True)
