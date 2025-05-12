import asyncio
import logging
import uuid
from typing import AsyncIterator, Optional

from ai.backend.common.events.dispatcher import AbstractEvent
from ai.backend.logging.utils import BraceStyleAdapter

from ..hub import EventPropagator

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AsyncBypassPropagator(EventPropagator):
    """
    A simple event propagator that uses an asyncio queue to propagate events.
    """

    _id: uuid.UUID
    _queue: asyncio.Queue[Optional[AbstractEvent]]
    _closed: bool = False

    def __init__(self) -> None:
        self._id = uuid.uuid4()
        self._queue = asyncio.Queue()
        self._closed = False

    def id(self) -> uuid.UUID:
        """
        Get the unique identifier for the propagator.
        """
        return self._id

    async def receive(self) -> AsyncIterator[AbstractEvent]:
        """
        Receive events from the queue.
        This method is a generator that yields events until the queue is closed.
        """
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
