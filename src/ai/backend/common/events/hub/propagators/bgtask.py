import asyncio
import logging
import uuid
from typing import AsyncIterator, Optional, Protocol

from ai.backend.logging.utils import BraceStyleAdapter

from ...bgtask import BaseBgtaskEvent
from ...dispatcher import AbstractEvent
from ..hub import EventPropagator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class BgtaskLastDoneEventFetcher(Protocol):
    async def fetch_last_finished_event(
        self,
        task_id: uuid.UUID,
    ) -> Optional[BaseBgtaskEvent]:
        """
        Fetch the last finished event for a given task ID.
        This method should be implemented by the class that uses this protocol.
        """
        ...


class BgtaskPropagator(EventPropagator):
    """
    Background task propagator that uses an asyncio queue to propagate events.
    This propagator is used to handle events related to background tasks.
    """

    _id: uuid.UUID
    _last_done_event_fetcher: BgtaskLastDoneEventFetcher
    _queue: asyncio.Queue[Optional[AbstractEvent]]
    _closed: bool = False

    def __init__(self, last_done_event_fetcher: BgtaskLastDoneEventFetcher) -> None:
        self._id = uuid.uuid4()
        self._last_done_event_fetcher = last_done_event_fetcher
        self._queue = asyncio.Queue()
        self._closed = False

    def id(self) -> uuid.UUID:
        """
        Get the unique identifier for the propagator.
        """
        return self._id

    async def receive(self, task_id: uuid.UUID) -> AsyncIterator[AbstractEvent]:
        """
        Receive background task events from the queue.
        First, it fetches the last finished event for a given task ID.
        If the last event is not None, it yields that event.
        Then, it enters a loop to receive events from the queue until closed.
        """
        last_event = await self._last_done_event_fetcher.fetch_last_finished_event(task_id)
        if last_event is not None:
            log.debug(
                "Yielding last finished event: {}",
                last_event,
            )
            yield last_event
            return
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
