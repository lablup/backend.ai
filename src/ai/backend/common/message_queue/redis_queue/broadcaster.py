from __future__ import annotations

import logging
from typing import Any, Mapping, Optional, Self, override

from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.types import RedisTarget
from ai.backend.logging.utils import BraceStyleAdapter

from ..abc import AbstractBroadcaster
from ..types import BroadcastPayload
from .exceptions import MessageQueueClosedError

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RedisBroadcaster(AbstractBroadcaster):
    """
    Redis-based broadcaster implementation for sending messages to all subscribers.

    This component handles pub/sub messaging where messages are delivered to all
    active subscribers. Supports message caching and batch broadcasting.
    """

    _client: ValkeyStreamClient
    _channel: str
    _closed: bool

    def __init__(self, client: ValkeyStreamClient, channel: str) -> None:
        """
        Initialize the Redis broadcaster.

        Args:
            client: ValkeyStreamClient for Redis operations
            channel: The Redis channel to broadcast messages to
        """
        self._client = client
        self._channel = channel
        self._closed = False

    @classmethod
    async def create(cls, redis_target: RedisTarget, channel: str, db: int = 0) -> Self:
        """
        Create a new RedisBroadcaster instance.

        Args:
            redis_target: Redis connection configuration
            channel: The Redis channel to broadcast messages to
            db: Redis database number (default: 0)

        Returns:
            Configured RedisBroadcaster instance
        """
        client = await ValkeyStreamClient.create(
            redis_target.to_valkey_target(),
            human_readable_name="redis_broadcaster",
            db_id=db,
        )
        return cls(client, channel)

    @override
    async def broadcast(self, payload: Mapping[str, Any]) -> None:
        """
        Broadcast a message to all subscribers.

        The message will be delivered to all active subscribers of the channel.
        Messages are not guaranteed to be delivered (fire-and-forget).

        Args:
            payload: Message payload as a mapping

        Raises:
            MessageQueueClosedError: If the broadcaster is closed
        """
        if self._closed:
            raise MessageQueueClosedError("Broadcaster is closed")

        await self._client.broadcast(self._channel, payload)
        log.debug("Message broadcasted to channel {}", self._channel)

    @override
    async def broadcast_with_cache(self, cache_id: str, payload: Mapping[str, str]) -> None:
        """
        Broadcast a message with caching support.

        The message will be cached with the given cache_id, allowing late subscribers
        to retrieve it using fetch_cached_broadcast_message().

        Args:
            cache_id: Unique identifier for caching the message
            payload: Message payload as string mapping

        Raises:
            MessageQueueClosedError: If the broadcaster is closed
        """
        if self._closed:
            raise MessageQueueClosedError("Broadcaster is closed")

        await self._client.broadcast_with_cache(self._channel, cache_id, payload)
        log.debug(
            "Cached message broadcasted to channel {} with cache_id {}", self._channel, cache_id
        )

    @override
    async def fetch_cached_broadcast_message(self, cache_id: str) -> Optional[Mapping[str, str]]:
        """
        Retrieve a cached broadcast message.

        This allows retrieving messages that were broadcast with a cache_id,
        useful for subscribers that missed the original broadcast.

        Args:
            cache_id: Unique identifier of the cached message

        Returns:
            The cached message payload or None if not found

        Raises:
            MessageQueueClosedError: If the broadcaster is closed
        """
        if self._closed:
            raise MessageQueueClosedError("Broadcaster is closed")

        message = await self._client.fetch_cached_broadcast_message(cache_id)
        log.debug(
            "Fetched cached message for cache_id {}: {}",
            cache_id,
            "found" if message else "not found",
        )
        return message

    @override
    async def broadcast_batch(self, events: list[BroadcastPayload]) -> None:
        """
        Broadcast multiple messages in a batch.

        Each event can optionally have a cache_id for caching support.
        This is more efficient than sending individual broadcast messages.

        Args:
            events: List of broadcast payloads, each optionally with cache_id

        Raises:
            MessageQueueClosedError: If the broadcaster is closed
        """
        if self._closed:
            raise MessageQueueClosedError("Broadcaster is closed")

        await self._client.broadcast_batch(self._channel, events)
        log.debug("Batch of {} messages broadcasted to channel {}", len(events), self._channel)

    @override
    async def close(self) -> None:
        """
        Close the broadcaster and cleanup resources.

        After closing, no more messages can be broadcast through this broadcaster.
        """
        if self._closed:
            return

        self._closed = True
        await self._client.close()
        log.debug("RedisBroadcaster closed")
