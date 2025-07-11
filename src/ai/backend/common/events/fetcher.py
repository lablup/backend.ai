from typing import Optional

from ai.backend.common.events.types import AbstractBroadcastEvent
from ai.backend.common.message_queue.queue import AbstractMessageQueue
from ai.backend.common.message_queue.types import MessagePayload


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
        payload = await self._msg_queue.fetch_cached_broadcast_message(cache_id)
        if payload is None:
            return None
        message_payload = MessagePayload.from_broadcast(payload)
        return AbstractBroadcastEvent.deserialize_from_wrapper(message_payload)
