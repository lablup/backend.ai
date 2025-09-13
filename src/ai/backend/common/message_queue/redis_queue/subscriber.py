from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from typing import AsyncGenerator, Optional, Self, override

import glide

from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.types import RedisTarget
from ai.backend.logging.utils import BraceStyleAdapter

from ..abc import AbstractSubscriber
from ..types import BroadcastMessage

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RedisSubscriber(AbstractSubscriber):
    """
    Redis-based subscriber implementation for receiving broadcast messages.

    This component handles subscribing to Redis pub/sub channels and receiving
    broadcast messages. Messages are delivered to all active subscribers.
    """

    _client: ValkeyStreamClient
    _subscribe_queue: asyncio.Queue[BroadcastMessage]
    _channels: set[str]
    _closed: bool
    _loop_task: Optional[asyncio.Task]

    def __init__(self, client: ValkeyStreamClient, channels: Iterable[str]) -> None:
        """
        Initialize the Redis subscriber.

        Args:
            client: ValkeyStreamClient configured with pub/sub channels
            channels: Set of Redis channels to subscribe to
        """
        self._client = client
        self._subscribe_queue = asyncio.Queue()
        self._channels = set(channels)
        self._closed = False

        # Start the background task to read broadcast messages
        self._loop_task = asyncio.create_task(self._read_broadcast_messages_loop())

    @classmethod
    async def create(cls, redis_target: RedisTarget, channels: set[str], db: int = 0) -> Self:
        """
        Create a new RedisSubscriber instance.

        Args:
            redis_target: Redis connection configuration
            channels: Set of Redis channels to subscribe to
            db: Redis database number (default: 0)

        Returns:
            Configured RedisSubscriber instance
        """
        client = await ValkeyStreamClient.create(
            redis_target.to_valkey_target(),
            human_readable_name="redis_subscriber",
            db_id=db,
            pubsub_channels=channels,
        )
        return cls(client, channels)

    @override
    async def subscribe_queue(self) -> AsyncGenerator[BroadcastMessage, None]:  # type: ignore[override]
        """
        Subscribe to broadcast messages.

        This method blocks until broadcast messages are available and yields them
        as they arrive. Unlike consumer messages, broadcast messages don't require
        acknowledgment.

        Yields:
            BroadcastMessage: Broadcast messages from subscribed channels

        Raises:
            RuntimeError: If the subscriber is closed
        """
        while not self._closed:
            try:
                yield await self._subscribe_queue.get()
            except asyncio.CancelledError:
                break

    @override
    async def close(self) -> None:
        """
        Close the subscriber and cleanup resources.

        This cancels the background task and closes the Redis client connection.
        """
        if self._closed:
            return

        self._closed = True

        # Cancel the background task
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                log.debug("Subscriber loop task cancelled")

        await self._client.close()
        log.debug("RedisSubscriber closed")

    async def _read_broadcast_messages_loop(self) -> None:
        """
        Background task to read broadcast messages from subscribed channels.
        """
        log.info("Starting read broadcast messages loop for channels {}", self._channels)

        while not self._closed:
            try:
                await self._read_broadcast_messages()
            except glide.ClosingError:
                log.info("Client connection closed, stopping read broadcast messages loop")
                break
            except Exception as e:
                log.error("Error while reading broadcast messages: {}", e)
                # Add a small delay to avoid tight error loops
                await asyncio.sleep(1.0)

    async def _read_broadcast_messages(self) -> None:
        """
        Read broadcast messages and put them in the subscribe queue.
        """
        payload = await self._client.receive_broadcast_message()
        msg = BroadcastMessage(payload)
        await self._subscribe_queue.put(msg)
