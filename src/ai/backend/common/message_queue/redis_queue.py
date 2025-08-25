import asyncio
import hashlib
import logging
import socket
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Final, Mapping, Optional, Self

import glide
from aiotools.server import process_index

from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.defs import REDIS_STREAM_DB
from ai.backend.common.types import RedisTarget
from ai.backend.logging.utils import BraceStyleAdapter

from .queue import AbstractMessageQueue
from .types import BroadcastMessage, BroadcastPayload, MessageId, MQMessage

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_AUTOCLAIM_IDLE_TIMEOUT = 300_000  # 5 minutes
_DEFAULT_AUTOCLAIM_INTERVAL = 60_000
_DEFAULT_READ_BLOCK_MS: Final[int] = 10_000  # 10 second
_DEFAULT_READ_COUNT = 64


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
    _client: ValkeyStreamClient
    _consume_queue: asyncio.Queue[MQMessage]
    _subscribe_queue: asyncio.Queue[BroadcastMessage]
    _anycast_stream_key: str
    _broadcast_channel: str
    _group_name: str
    _consumer_id: str
    _redis_target: RedisTarget
    _closed: bool
    # loop tasks for consuming messages
    _loop_tasks: list[asyncio.Task]

    def __init__(
        self, client: ValkeyStreamClient, redis_target: RedisTarget, args: RedisMQArgs
    ) -> None:
        self._client = client
        self._consume_queue = asyncio.Queue()
        self._subscribe_queue = asyncio.Queue()
        self._anycast_stream_key = args.anycast_stream_key
        self._broadcast_channel = args.broadcast_channel
        self._group_name = args.group_name
        self._consumer_id = _generate_consumer_id(args.node_id)
        self._redis_target = redis_target
        self._closed = False
        start_id = args.autoclaim_start_id or "0-0"
        self._loop_tasks = []
        if args.consume_stream_keys:
            for stream_key in args.consume_stream_keys:
                self._loop_tasks.append(asyncio.create_task(self._read_messages_loop(stream_key)))
                self._loop_tasks.append(
                    asyncio.create_task(
                        self._auto_claim_loop(stream_key, start_id, args.autoclaim_idle_timeout)
                    )
                )
        if args.subscribe_channels:
            self._loop_tasks.append(asyncio.create_task(self._read_broadcast_messages_loop()))

    @classmethod
    async def create(cls, redis_target: RedisTarget, args: RedisMQArgs) -> Self:
        client = await ValkeyStreamClient.create(
            redis_target.to_valkey_target(),
            human_readable_name="event_producer.stream",
            db_id=args.db,
            pubsub_channels=args.subscribe_channels,
        )
        try:
            # Create consumer group if not exists
            await client.make_consumer_group(args.anycast_stream_key, args.group_name)
        except Exception:
            # Group may already exist
            pass
        return cls(client, redis_target, args)

    async def send(self, payload: dict[bytes, bytes]) -> None:
        """
        Send a message to the queue.
        If the queue is full, the oldest message will be removed.
        The new message will be added to the end of the queue.
        """
        if self._closed:
            raise RuntimeError("Queue is closed")
        await self._client.enqueue_stream_message(self._anycast_stream_key, payload)

    async def broadcast(self, payload: Mapping[str, Any]) -> None:
        """
        Broadcast a message to all subscribers.
        The message will be delivered to all subscribers.
        """
        if self._closed:
            raise RuntimeError("Queue is closed")
        await self._client.broadcast(self._broadcast_channel, payload)

    async def broadcast_with_cache(self, cache_id: str, payload: Mapping[str, str]) -> None:
        """
        Broadcast a message to all subscribers with cache.
        The message will be delivered to all subscribers.
        """
        if self._closed:
            raise RuntimeError("Queue is closed")
        await self._client.broadcast_with_cache(self._broadcast_channel, cache_id, payload)

    async def fetch_cached_broadcast_message(self, cache_id: str) -> Optional[Mapping[str, str]]:
        """
        Fetch a cached broadcast message by cache_id.
        This method retrieves the cached message from the broadcast channel.
        """
        if self._closed:
            raise RuntimeError("Queue is closed")
        return await self._client.fetch_cached_broadcast_message(cache_id)

    async def broadcast_batch(self, events: list[BroadcastPayload]) -> None:
        """
        Broadcast multiple messages in a batch with optional caching.
        This method broadcasts multiple messages to all subscribers.
        """
        if self._closed:
            raise RuntimeError("Queue is closed")
        await self._client.broadcast_batch(self._broadcast_channel, events)

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
        while not self._closed:
            try:
                yield await self._consume_queue.get()
            except asyncio.CancelledError:
                break

    async def subscribe_queue(self) -> AsyncGenerator[BroadcastMessage, None]:  # type: ignore
        while not self._closed:
            try:
                yield await self._subscribe_queue.get()
            except asyncio.CancelledError:
                break

    async def done(self, msg_id: MessageId) -> None:
        await self._done(self._anycast_stream_key, msg_id)

    async def _done(self, stream_key: str, msg_id: MessageId) -> None:
        await self._client.done_stream_message(stream_key, self._group_name, msg_id)

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for task in self._loop_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                log.debug("Task {} cancelled", task.get_name())
        await self._client.close()

    async def _auto_claim_loop(
        self, stream_key: str, autoclaim_start_id: str, autoclaim_idle_timeout: int
    ) -> None:
        log.debug("Starting auto claim loop for stream {}", stream_key)
        while not self._closed:
            try:
                next_start_id, claimed = await self._auto_claim(
                    stream_key, autoclaim_start_id, autoclaim_idle_timeout
                )
                if claimed:
                    autoclaim_start_id = next_start_id
                    continue
            except glide.TimeoutError:
                # If the auto claim times out, we just continue to the next iteration
                pass
            except glide.ClosingError:
                log.info(
                    "Client connection closed, stopping auto claim loop for stream {}", stream_key
                )
                break
            except glide.GlideError as e:
                await self._failover_consumer(stream_key, e)
            except Exception as e:
                log.exception("Error while auto claiming messages: {}", e)
            await asyncio.sleep(_DEFAULT_AUTOCLAIM_INTERVAL / 1000)

    async def _auto_claim(
        self, stream_key: str, autoclaim_start_id: str, autoclaim_idle_timeout: int
    ) -> tuple[str, bool]:
        message = await self._client.auto_claim_stream_message(
            stream_key,
            self._group_name,
            self._consumer_id,
            autoclaim_start_id,
            autoclaim_idle_timeout,
        )
        if message is None:
            return autoclaim_start_id, False
        for msg in message.messages:
            mq_msg = MQMessage(msg.msg_id, {**msg.payload})
            if mq_msg.retry():
                await self._retry_message(stream_key, mq_msg)
                continue
            # discard the message
            await self._done(stream_key, mq_msg.msg_id)
        return autoclaim_start_id, len(message.messages) > 0

    async def _retry_message(self, stream_key: str, message: MQMessage) -> None:
        await self._client.reque_stream_message(
            stream_key, self._group_name, message.msg_id, message.payload
        )

    async def _read_messages_loop(self, stream_key: str) -> None:
        log.info("Starting read messages loop for stream {}", stream_key)
        target = self._redis_target.to_valkey_target()
        # Set the request timeout to be longer than the read block time
        target.request_timeout = (_DEFAULT_READ_BLOCK_MS // 1000) + 1  # add 1 second buffer
        client = await ValkeyStreamClient.create(
            target,
            human_readable_name="event_producer.stream",
            db_id=REDIS_STREAM_DB,
        )
        while not self._closed:
            try:
                await self._read_messages(client, stream_key)
            except glide.ClosingError:
                log.info(
                    "Client connection closed, stopping read messages loop for stream {}",
                    stream_key,
                )
                break
            except glide.GlideError as e:
                await self._failover_consumer(stream_key, e)
            except Exception as e:
                log.error("Error while reading messages: {}", e)

    async def _read_messages(self, client: ValkeyStreamClient, stream_key: str) -> None:
        payload = await client.read_consumer_group(
            stream_key,
            self._group_name,
            self._consumer_id,
            count=_DEFAULT_READ_COUNT,
            block_ms=_DEFAULT_READ_BLOCK_MS,
        )
        if not payload:
            return
        for msg in payload:
            mq_msg = MQMessage(msg_id=msg.msg_id, payload={**msg.payload})
            await self._consume_queue.put(mq_msg)

    async def _read_broadcast_messages_loop(self) -> None:
        log.info("Starting read broadcast messages loop")
        while not self._closed:
            try:
                await self._read_broadcast_messages()
            except glide.ClosingError:
                log.info("Client connection closed, stopping read broadcast messages loop")
                break
            except Exception as e:
                log.error("Error while reading broadcast messages: {}", e)

    async def _read_broadcast_messages(self) -> None:
        payload = await self._client.receive_broadcast_message()
        msg = BroadcastMessage(payload)
        await self._subscribe_queue.put(msg)

    async def _failover_consumer(self, stream_key: str, e: Exception) -> None:
        # If the group does not exist, create it
        # and start the auto claim loop again
        if "NOGROUP" in str(e):
            log.warning(
                "Consumer group does not exist. Creating group {} for stream {}",
                self._group_name,
                stream_key,
            )
            try:
                await self._client.make_consumer_group(
                    stream_key,
                    self._group_name,
                )
            except Exception as internal_exception:
                log.exception(
                    "Error while creating consumer group {} for stream {}: {}",
                    self._group_name,
                    stream_key,
                    internal_exception,
                )
        else:
            log.exception("Error while reading messages: {}", e)


def _generate_consumer_id(node_id: Optional[str]) -> str:
    h = hashlib.sha1()
    h.update(str(node_id or socket.getfqdn()).encode("utf8"))
    hostname_hash = h.hexdigest()
    h = hashlib.sha1()
    h.update(__file__.encode("utf8"))
    installation_path_hash = h.hexdigest()
    pidx = process_index.get(0)
    return f"{hostname_hash}:{installation_path_hash}:{pidx}"
