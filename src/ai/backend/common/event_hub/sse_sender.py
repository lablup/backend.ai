import asyncio
import logging
from typing import Optional

from aiohttp_sse import EventSourceResponse

from ai.backend.common.event_hub.user_event_hub import UserEvent, UserEventSender
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SSEUserEventSender(UserEventSender):
    _event_source: EventSourceResponse
    # None is used to indicate that the queue is closed
    _queue: asyncio.Queue[Optional[UserEvent]]
    _closed: bool = False

    def __init__(self, event_source: EventSourceResponse) -> None:
        self._event_source = event_source
        self._queue = asyncio.Queue()
        self._closed = False

    async def run(self) -> None:
        if self._closed:
            raise RuntimeError("SSEUserEventSender is closed")
        await self._send_event_loop()

    async def _send_event_loop(self) -> None:
        while not self._closed:
            event = await self._queue.get()
            if event is None:
                break
            try:
                await self._event_source.send(
                    event.serialize_user_event(),
                    event=event.event_name(),
                    retry=event.retry_count(),
                )
            except Exception as e:
                log.error("Error sending event: {}", e)

    async def send_event(self, event: UserEvent) -> None:
        if self._closed:
            raise RuntimeError("SSEUserEventSender is closed")
        await self._queue.put(event)

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._queue.put(None)
