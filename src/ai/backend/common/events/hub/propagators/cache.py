import asyncio
import logging
import uuid
from typing import AsyncIterator, Optional

from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.logging.utils import BraceStyleAdapter

from ...dispatcher import AbstractEvent
from ..hub import EventPropagator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class WithCachePropagator(EventPropagator):
    """
    WithCachePropagator is an event propagator that handles broadcast events.
    It fetches the last event for a given task ID from the cache and propagates events
    to a queue for broadcasted events.
    It allows to prevent timing issues by ensuring that the last event is fetched before yielding new events.
    """

    _id: uuid.UUID
    _event_fetcher: EventFetcher
    _queue: asyncio.Queue[Optional[AbstractEvent]]
    _closed: bool = False

    def __init__(self, event_fetcher: EventFetcher) -> None:
        self._id = uuid.uuid4()
        self._event_fetcher = event_fetcher
        self._queue = asyncio.Queue()
        self._closed = False

    def id(self) -> uuid.UUID:
        """
        Get the unique identifier for the propagator.
        """
        return self._id

    async def receive(self, cache_id: str) -> AsyncIterator[AbstractEvent]:
        """
        First, it fetches the last event for a given cache ID using the event fetcher.
        If the last event is not None, it yields that event.
        Then, it enters a loop to receive events from the queue until closed.
        """
        cached_event = await self._event_fetcher.fetch_cached_event(cache_id)
        if cached_event is not None:
            yield cached_event
        while not self._closed:
            event = await self._queue.get()
            try:
                if event is None:
                    break
                yield event
            except Exception as e:
                log.error("Error propagating event: {}", e)

    async def propagate_event(self, event: AbstractEvent) -> None:
        await self._queue.put(event)

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._queue.put(None)
