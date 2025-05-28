import asyncio
import logging
import uuid
from typing import AsyncIterator, Optional, Protocol

from ai.backend.common.bgtask.bgtask import BgTaskInfo
from ai.backend.logging.utils import BraceStyleAdapter

from ...bgtask import BgtaskAlreadyDoneEvent
from ...dispatcher import AbstractEvent
from ..hub import EventPropagator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class BgtaskLastDoneEventFetcher(Protocol):
    async def fetch_bgtask_info(
        self,
        task_id: uuid.UUID,
    ) -> BgTaskInfo:
        """
        Fetch the background task information for a given task ID.
        This method is used to retrieve the last status of a background task.
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
        bgtask_info = await self._last_done_event_fetcher.fetch_bgtask_info(task_id)
        if bgtask_info.status.finished():
            log.debug(
                "Yielding already finished event: {}",
                bgtask_info,
            )
            yield BgtaskAlreadyDoneEvent(
                task_id=task_id,
                message=bgtask_info.msg,
                task_status=bgtask_info.status,
                current=bgtask_info.current,
                total=bgtask_info.total,
            )
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
