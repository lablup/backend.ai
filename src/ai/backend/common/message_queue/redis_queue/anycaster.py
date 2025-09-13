from __future__ import annotations

import logging
from typing import Self, override

from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.types import RedisTarget
from ai.backend.logging.utils import BraceStyleAdapter

from ..abc import AbstractAnycaster
from .exceptions import MessageQueueClosedError

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class RedisAnycaster(AbstractAnycaster):
    """
    Redis-based anycaster implementation for sending messages to streams.

    This component handles point-to-point message delivery using Redis streams.
    Messages are sent to a specific stream key and will be consumed by exactly
    one consumer from the consumer group.
    """

    _client: ValkeyStreamClient
    _stream_key: str
    _closed: bool

    def __init__(self, client: ValkeyStreamClient, stream_key: str) -> None:
        """
        Initialize the Redis anycaster.

        Args:
            client: ValkeyStreamClient for Redis operations
            stream_key: The Redis stream key to send messages to
        """
        self._client = client
        self._stream_key = stream_key
        self._closed = False

    @classmethod
    async def create(cls, redis_target: RedisTarget, stream_key: str, db: int = 0) -> Self:
        """
        Create a new RedisAnycaster instance.

        Args:
            redis_target: Redis connection configuration
            stream_key: The Redis stream key to send messages to
            db: Redis database number (default: 0)

        Returns:
            Configured RedisAnycaster instance
        """
        client = await ValkeyStreamClient.create(
            redis_target.to_valkey_target(),
            human_readable_name="redis_anycaster",
            db_id=db,
        )
        return cls(client, stream_key)

    @override
    async def anycast(self, payload: dict[bytes, bytes]) -> None:
        """
        Send a message to the anycast stream.

        The message will be delivered to exactly one consumer from the consumer group.
        If the stream is full, the oldest message will be removed and the new
        message will be added to the end of the stream.

        Args:
            payload: Message payload as a dictionary of bytes

        Raises:
            MessageQueueClosedError: If the anycaster is closed
        """
        if self._closed:
            raise MessageQueueClosedError("Anycaster is closed")

        await self._client.enqueue_stream_message(self._stream_key, payload)
        log.debug("Message sent to stream {}", self._stream_key)

    @override
    async def close(self) -> None:
        """
        Close the anycaster and cleanup resources.

        After closing, no more messages can be sent through this anycaster.
        """
        if self._closed:
            return

        self._closed = True
        await self._client.close()
        log.debug("RedisAnycaster closed")
