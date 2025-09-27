from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from ...events.dispatcher import EventProducer
from ...events.event_types.bgtask.broadcast import BgtaskUpdatedEvent
from ...events.types import EventCacheDomain
from .base import AbstractTaskHook, TaskContext


class EventProducerHook(AbstractTaskHook):
    """Hook for producing task events."""

    def __init__(self, event_producer: EventProducer):
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
