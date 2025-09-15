"""
Deprecated:
Use `ai.backend.common.message_queue.abc.{anycaster,broadcaster,consumer,subscriber}` instead.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Mapping, Optional

from ..types import BroadcastMessage, BroadcastPayload, MessageId, MQMessage


class AbstractMessageQueue(ABC):
    @abstractmethod
    async def send(
        self,
        payload: dict[bytes, bytes],
    ) -> None:
        """
        Send a message to the queue.

        If the queue is full, the oldest message will be removed.
        The new message will be added to the end of the queue.
        The message will be delivered to one consumer.
        """
        raise NotImplementedError

    @abstractmethod
    async def broadcast(
        self,
        payload: Mapping[str, Any],
    ) -> None:
        """
        Broadcast a message to all subscribers of the channel.
        The message will be delivered to all subscribers.
        Subscribers should call `done` method to acknowledge the message when it is processed.
        Messages are not guaranteed to be delivered.
        """
        raise NotImplementedError

    @abstractmethod
    async def broadcast_with_cache(
        self,
        cache_id: str,
        payload: Mapping[str, str],
    ) -> None:
        """
        Broadcast a message to all subscribers of the channel with cache.
        The message will be delivered to all subscribers.
        Subscribers should call `done` method to acknowledge the message when it is processed.
        Messages are not guaranteed to be delivered.
        The message will be cached with the given cache_id.
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_cached_broadcast_message(self, cache_id: str) -> Optional[Mapping[str, str]]:
        """
        Fetch a cached broadcast message by cache_id.
        This method retrieves the cached message from the broadcast channel.
        If the message is not found, it will return None.
        This is useful for subscribers to get the last message that was broadcasted
        when they were not online.
        """
        raise NotImplementedError

    @abstractmethod
    async def broadcast_batch(self, events: list[BroadcastPayload]) -> None:
        """
        Broadcast multiple messages in a batch with optional caching.
        This method broadcasts multiple messages to all subscribers.
        Each event contains a payload and optional cache_id.
        Messages are not guaranteed to be delivered.
        """
        raise NotImplementedError

    @abstractmethod
    async def consume_queue(
        self,
    ) -> AsyncGenerator[MQMessage, None]:
        """
        Consume messages from the queue.
        This method will block until a message is available.

        This is a normal queue, so the message will be delivered to one consumer.
        Messages are consumed only once by one consumer.
        """
        raise NotImplementedError

    @abstractmethod
    async def subscribe_queue(
        self,
    ) -> AsyncGenerator[BroadcastMessage, None]:
        """
        Subscribe to messages from the queue.
        This method will block until a message is available.

        This is a broadcast queue, so the message will be delivered to all subscribers.
        The subscriber should call `done` method to acknowledge the message when it is processed.
        """
        raise NotImplementedError

    @abstractmethod
    async def done(
        self,
        msg_id: MessageId,
    ) -> None:
        """
        Acknowledge the message.

        This method should be called after the message is processed.
        If the consumer does not call `done`, the message will be re-delivered after the
        some timeout period.
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """
        Close the message queue.

        This method should be called when the message queue is no longer needed.
        It will close all connections and stop all background tasks.
        """
        raise NotImplementedError
