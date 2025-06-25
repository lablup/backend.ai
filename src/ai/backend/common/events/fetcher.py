from typing import Optional

from ai.backend.common.events.types import AbstractBroadcastEvent
from ai.backend.common.message_queue.queue import AbstractMessageQueue


class EventFetcher:
    _msg_queue: AbstractMessageQueue

    def __init__(self, msg_queue: AbstractMessageQueue) -> None:
        self._msg_queue = msg_queue

    async def fetch_cached_event(
        self,
        cache_id: str,
    ) -> Optional[AbstractBroadcastEvent]:
        """
        Fetch a cached event from the message queue.
        Returns None if no cached event is found.
        """
        raw_event = await self._msg_queue.fetch_cached_broadcast_message(cache_id)
        if raw_event is None:
            return None
        return AbstractBroadcastEvent.deserialize_from_wrapper(raw_event)
