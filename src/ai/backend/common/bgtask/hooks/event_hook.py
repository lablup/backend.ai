from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.bgtask.broadcast import BgtaskUpdatedEvent
from ai.backend.common.events.types import EventCacheDomain

from .base import AbstractTaskHook, TaskContext


class EventProducerHook(AbstractTaskHook):
    """Hook for producing task events."""

    def __init__(self, event_producer: EventProducer) -> None:
        self._event_producer = event_producer

    @asynccontextmanager
    async def apply(self, context: TaskContext) -> AsyncIterator[TaskContext]:
        # Pre-execution: send task started event
        cache_id = EventCacheDomain.BGTASK.cache_id(str(context.task_id))
        await self._event_producer.broadcast_event_with_cache(
            cache_id,
            BgtaskUpdatedEvent(
                task_id=context.task_id,
                message="Task started",
                current_progress=0,
                total_progress=0,
            ),
        )

        try:
            yield context
        finally:
            # Post-execution: send task completion event
            if context.result:
                event = context.result.to_broadcast_event(context.task_id)
                await self._event_producer.broadcast_event_with_cache(cache_id, event)
