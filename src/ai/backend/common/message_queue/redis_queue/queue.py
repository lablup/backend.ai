from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncGenerator, Mapping, Optional, Self, override

from ai.backend.common.types import RedisTarget

from ..abc import AbstractAnycaster, AbstractBroadcaster, AbstractConsumer, AbstractSubscriber
from ..abc.queue import AbstractMessageQueue
from ..types import BroadcastMessage, BroadcastPayload, MessageId, MQMessage
from .anycaster import RedisAnycaster
from .broadcaster import RedisBroadcaster
from .consumer import RedisConsumer, RedisConsumerArgs
from .subscriber import RedisSubscriber

_DEFAULT_AUTOCLAIM_IDLE_TIMEOUT = 300_000  # 5 minutes


@dataclass
class RedisMQArgs:
    # Required arguments
    anycast_stream_key: str
    broadcast_channel: str
    consume_stream_keys: Optional[set[str]]
    subscribe_channels: Optional[set[str]]
    group_name: str
    node_id: str
    db: int
    # Optional arguments
    autoclaim_idle_timeout: int = _DEFAULT_AUTOCLAIM_IDLE_TIMEOUT
    autoclaim_start_id: Optional[str] = None


class RedisQueue(AbstractMessageQueue):
    """
    Redis message queue implementation with composable components.

    This queue can contain any combination of the four components:
    - Anycaster: for point-to-point messaging
    - Broadcaster: for pub/sub broadcasting
    - Consumer: for consuming messages from streams
    - Subscriber: for receiving broadcast messages
    """

    _anycaster: AbstractAnycaster
    _broadcaster: AbstractBroadcaster
    _consumer: AbstractConsumer
    _subscriber: AbstractSubscriber

    def __init__(
        self,
        anycaster: AbstractAnycaster,
        broadcaster: AbstractBroadcaster,
        consumer: AbstractConsumer,
        subscriber: AbstractSubscriber,
    ) -> None:
        self._anycaster = anycaster
        self._broadcaster = broadcaster
        self._consumer = consumer
        self._subscriber = subscriber

    @classmethod
    async def create(cls, redis_target: RedisTarget, args: RedisMQArgs) -> Self:
        """
        Create a RedisQueue instance with all four components.
        """
        # Create anycaster
        anycaster = await RedisAnycaster.create(redis_target, args.anycast_stream_key, args.db)

        # Create broadcaster
        broadcaster = await RedisBroadcaster.create(redis_target, args.broadcast_channel, args.db)

        # Create consumer
        consume_stream_keys = args.consume_stream_keys or set()
        consumer = await RedisConsumer.create(
            redis_target,
            RedisConsumerArgs(
                consume_stream_keys,
                args.group_name,
                args.node_id,
                args.db,
                args.autoclaim_idle_timeout,
                args.autoclaim_start_id,
            ),
        )

        # Create subscriber
        subscribe_channels = args.subscribe_channels or set()
        subscriber = await RedisSubscriber.create(redis_target, subscribe_channels, args.db)

        return cls(anycaster, broadcaster, consumer, subscriber)

    # Anycaster methods

    @override
    async def send(self, payload: dict[bytes, bytes]) -> None:
        """
        Send a message to the anycast queue.
        If the queue is full, the oldest message will be removed.
        The new message will be added to the end of the queue.
        """
        await self._anycaster.anycast(payload)

    # Broadcaster methods

    @override
    async def broadcast(self, payload: Mapping[str, Any]) -> None:
        """
        Broadcast a message to all subscribers.
        The message will be delivered to all subscribers.
        """
        await self._broadcaster.broadcast(payload)

    @override
    async def broadcast_with_cache(self, cache_id: str, payload: Mapping[str, str]) -> None:
        """
        Broadcast a message to all subscribers with cache.
        The message will be delivered to all subscribers.
        """
        await self._broadcaster.broadcast_with_cache(cache_id, payload)

    @override
    async def fetch_cached_broadcast_message(self, cache_id: str) -> Optional[Mapping[str, str]]:
        """
        Fetch a cached broadcast message by cache_id.
        This method retrieves the cached message from the broadcast channel.
        """
        return await self._broadcaster.fetch_cached_broadcast_message(cache_id)

    @override
    async def broadcast_batch(self, events: list[BroadcastPayload]) -> None:
        """
        Broadcast multiple messages in a batch with optional caching.
        This method broadcasts multiple messages to all subscribers.
        """
        await self._broadcaster.broadcast_batch(events)

    # Consumer methods

    @override
    async def consume_queue(self) -> AsyncGenerator[MQMessage, None]:  # type: ignore
        """
        Consume messages from the queue.
        This method will block until a message is available.

        This is a normal queue, so the message will be delivered to one consumer.
        Messages are consumed only once by one consumer.

        Consumer should call `done` method to acknowledge the message when it is processed.
        If the consumer does not call `done`, the message will be re-delivered after the
        `autoclaim_idle_timeout` period.
        """
        async for message in self._consumer.consume_queue():  # type: ignore[attr-defined]
            yield message

    @override
    async def done(self, msg_id: MessageId) -> None:
        """
        Acknowledge that a message has been processed successfully.
        """
        await self._consumer.done(msg_id)

    # Subscriber methods

    @override
    async def subscribe_queue(self) -> AsyncGenerator[BroadcastMessage, None]:  # type: ignore
        """
        Subscribe to broadcast messages.
        """
        async for message in self._subscriber.subscribe_queue():  # type: ignore[attr-defined]
            yield message

    # Management methods

    @override
    async def close(self) -> None:
        """
        Close all components and cleanup resources.
        """
        await self._anycaster.close()
        await self._broadcaster.close()
        await self._consumer.close()
        await self._subscriber.close()

    # Component access methods (for future independent usage)
