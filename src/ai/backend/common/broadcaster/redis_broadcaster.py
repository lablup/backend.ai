import asyncio
import logging
from typing import AsyncGenerator, Final, override

from ai.backend.common import redis_helper
from ai.backend.common.broadcaster.broadcaster import (
    AbstractBroadcaster,
    AbstractBroadcastSubscriber,
    BroadcastedMessage,
)
from ai.backend.common.types import RedisConnectionInfo
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

BROADCAST_EVENT_CHANNEL: Final[str] = "broadcast_event_channel"


class RedisBroadcaster(AbstractBroadcaster):
    _conn: RedisConnectionInfo
    _channel: str

    def __init__(self, conn: RedisConnectionInfo, channel: str) -> None:
        self._conn = conn
        self._channel = channel

    async def broadcast(self, b: bytes) -> None:
        return await redis_helper.execute(
            self._conn,
            lambda r: r.publish(self._channel, b),
        )


class RedisBroadcasterSubscriber(AbstractBroadcastSubscriber):
    _conn: RedisConnectionInfo
    _channels: list[str]
    _queue: asyncio.Queue[BroadcastedMessage]
    _closed: bool
    _read_broadcasted_messages_task: asyncio.Task[None]

    def __init__(self, conn: RedisConnectionInfo, channels: list[str]) -> None:
        self._conn = conn
        self._channels = channels
        self._queue = asyncio.Queue()
        self._closed = False
        self._read_broadcasted_messages_task = asyncio.create_task(
            self._read_broadcasted_messages_loop()
        )

    async def _read_broadcasted_messages_loop(self) -> None:
        while not self._closed:
            try:
                pubsub = self._conn.client.pubsub()
                await pubsub.subscribe(*self._channels)
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        await self._queue.put(BroadcastedMessage(message["data"]))
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.error("Error while reading broadcasted messages: %s", e)

    @override
    async def subscribe_queue(self) -> AsyncGenerator[BroadcastedMessage, None]:  # type: ignore
        while not self._closed:
            try:
                yield await self._queue.get()
            except asyncio.CancelledError:
                break

    @override
    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._conn.close()
