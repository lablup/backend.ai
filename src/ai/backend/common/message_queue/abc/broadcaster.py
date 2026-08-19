from __future__ import annotations

from abc import ABC, abstractmethod

from ai.backend.common.message_queue.payload import (
    BroadcastMessagePayload,
    CachedBroadcastMessagePayload,
)


class AbstractBroadcaster(ABC):
    """
    Abstract interface for broadcasting messages to all subscribers.
    Messages are delivered to all active subscribers.
    """

    @abstractmethod
    async def broadcast(self, payload: BroadcastMessagePayload) -> None:
        """
        Broadcast a message to all subscribers.

        Args:
            payload: Message payload as a broadcast envelope

        Raises:
            RuntimeError: If the component is closed
        """
        raise NotImplementedError

    @abstractmethod
    async def broadcast_with_cache(self, cache_id: str, payload: BroadcastMessagePayload) -> None:
        """
        Broadcast a message with caching support.

        Args:
            cache_id: Unique identifier for caching the message
            payload: Message payload as a broadcast envelope

        Raises:
            RuntimeError: If the component is closed
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_cached_broadcast_message(self, cache_id: str) -> BroadcastMessagePayload | None:
        """
        Retrieve a cached broadcast message.

        Args:
            cache_id: Unique identifier of the cached message

        Returns:
            The cached message payload or None if not found

        Raises:
            RuntimeError: If the component is closed
        """
        raise NotImplementedError

    @abstractmethod
    async def broadcast_batch(self, events: list[CachedBroadcastMessagePayload]) -> None:
        """
        Broadcast multiple messages in a batch.

        Args:
            events: List of broadcast payloads, each optionally with cache_id

        Raises:
            RuntimeError: If the component is closed
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """
        Close the broadcaster and cleanup resources.
        """
        raise NotImplementedError
