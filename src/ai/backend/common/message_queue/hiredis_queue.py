import asyncio
import hashlib
import logging
import socket
from typing import AsyncGenerator, Mapping, Optional

import hiredis
from aiotools.server import process_index

from ai.backend.common.json import dump_json, load_json
from ai.backend.common.message_queue.redis_queue import RedisMQArgs
from ai.backend.common.redis_client import RedisConnection
from ai.backend.logging.utils import BraceStyleAdapter

from ..types import RedisTarget
from .queue import AbstractMessageQueue
from .types import BroadcastMessage, BroadcastPayload, MessageId, MQMessage

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_AUTOCLAIM_INTERVAL = 60_000
_DEFAULT_AUTOCLAIM_COUNT = 64
_DEFAULT_QUEUE_MAX_LEN = 128
_DEFAULT_AUTO_RECONNECT_INTERVAL = 5  # seconds


def _make_pieces(payload: dict[bytes, bytes]) -> list[bytes]:
    pieces = []
    for k, v in payload.items():
        pieces.append(k)
        pieces.append(v)
    return pieces


class HiRedisQueue(AbstractMessageQueue):
    _target: RedisTarget
    _db: int
    _consume_queue: asyncio.Queue[MQMessage]
    _subscribe_queue: asyncio.Queue[BroadcastMessage]
    _anycast_stream_key: str
    _broadcast_channel: str
    _group_name: str
    _consumer_id: str
    _closed: bool
    # loop tasks for consuming messages
    _loop_tasks: list[asyncio.Task]

    def __init__(self, target: RedisTarget, args: RedisMQArgs) -> None:
        self._target = target
        self._db = args.db
        self._consume_queue = asyncio.Queue()
        self._subscribe_queue = asyncio.Queue()
        self._anycast_stream_key = args.anycast_stream_key
        self._broadcast_channel = args.broadcast_channel
        self._consume_stream_keys = args.consume_stream_keys
        self._group_name = args.group_name
        self._consumer_id = _generate_consumer_id(args.node_id)
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
            self._loop_tasks.append(
                asyncio.create_task(self._read_broadcast_messages_loop(args.subscribe_channels))
            )

    async def send(self, payload: dict[bytes, bytes]) -> None:
        async with RedisConnection(self._target, db=self._db) as client:
            pieces = _make_pieces(payload)
            await client.execute([
                "XADD",
                self._anycast_stream_key,
                "MAXLEN",
                _DEFAULT_QUEUE_MAX_LEN,
                "*",
                *pieces,
            ])

    async def broadcast(self, payload: Mapping[str, str]) -> None:
        async with RedisConnection(self._target, db=self._db) as client:
            payload_bytes = dump_json(payload)
            await client.execute([
                "PUBLISH",
                self._broadcast_channel,
                payload_bytes,
            ])

    async def broadcast_with_cache(self, cache_id: str, payload: Mapping[str, str]) -> None:
        async with RedisConnection(self._target, db=self._db) as client:
            payload_bytes = dump_json(payload)
            await client.pipeline([
                [
                    "SET",
                    cache_id,
                    payload_bytes,
                ],
                [
                    "EXPIRE",
                    cache_id,
                    60,  # Set a default expiration time of 60 seconds
                ],
                [
                    "PUBLISH",
                    self._broadcast_channel,
                    payload_bytes,
                ],
            ])

    async def fetch_cached_broadcast_message(self, cache_id: str) -> Optional[Mapping[str, str]]:
        if self._closed:
            raise RuntimeError("Queue is closed")
        async with RedisConnection(self._target, db=self._db) as client:
            reply = await client.execute(["GET", cache_id])
            if reply is None:
                return None
            return load_json(reply)

    async def broadcast_batch(self, events: list[BroadcastPayload]) -> None:
        """
        Broadcast multiple messages in a batch with optional caching.
        This method broadcasts multiple messages to all subscribers.
        """
        if self._closed:
            raise RuntimeError("Queue is closed")
        if not events:
            return

        async with RedisConnection(self._target, db=self._db) as client:
            pipeline_commands: list[list[str | bytes | int]] = []
            for event in events:
                payload_bytes: bytes = dump_json(event.payload)
                # Only add cache commands if cache_id is provided
                if event.cache_id:
                    pipeline_commands.extend([
                        [
                            "SET",
                            event.cache_id,
                            payload_bytes,
                        ],
                        [
                            "EXPIRE",
                            event.cache_id,
                            60,  # Set a default expiration time of 60 seconds
                        ],
                    ])
                # Always publish the message
                pipeline_commands.append([
                    "PUBLISH",
                    self._broadcast_channel,
                    payload_bytes,
                ])
            await client.pipeline(pipeline_commands)

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
        async with RedisConnection(self._target, db=self._db) as client:
            await client.execute([
                "XACK",
                stream_key,
                self._group_name,
                msg_id,
            ])

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for task in self._loop_tasks:
            task.cancel()

    async def _auto_claim_loop(
        self, stream_key: str, autoclaim_start_id: str, autoclaim_idle_timeout: int
    ) -> None:
        log.info("Starting auto claim loop for stream {}", stream_key)
        while not self._closed:
            try:
                next_start_id, claimed = await self._auto_claim(
                    stream_key, autoclaim_start_id, autoclaim_idle_timeout
                )
                if claimed:
                    autoclaim_start_id = next_start_id
                    continue
            except hiredis.HiredisError as e:
                await self._failover_consumer(e)
            except Exception as e:
                log.error("Error while auto claiming messages: {}", e)
            await asyncio.sleep(_DEFAULT_AUTOCLAIM_INTERVAL / 1000)

    async def _auto_claim(
        self, stream_key: str, autoclaim_start_id: str, autoclaim_idle_timeout: int
    ) -> tuple[str, bool]:
        async with RedisConnection(self._target, db=self._db) as client:
            reply = await client.execute(
                [
                    "XAUTOCLAIM",
                    stream_key,
                    self._group_name,
                    self._consumer_id,
                    str(autoclaim_idle_timeout),
                    autoclaim_start_id,
                    "COUNT",
                    _DEFAULT_AUTOCLAIM_COUNT,
                ],
                command_timeout=(autoclaim_idle_timeout + 5_000) / 1000,
            )
            if reply is None or reply[0] == b"0-0":
                return autoclaim_start_id, False
            for stream_msg in reply.values():
                for msg_id, messages in stream_msg:
                    payload = {}
                    for i in range(0, len(messages), 2):
                        key = messages[i]
                        value = messages[i + 1]
                        payload[key] = value
                    msg = MQMessage(msg_id, payload)
                    if msg.retry():
                        await self._retry_message(stream_key, msg)
                    else:
                        # discard the message
                        await self._done(stream_key, msg_id)
        return autoclaim_start_id, True

    async def _retry_message(self, stream_key: str, message: MQMessage) -> None:
        pieces = _make_pieces(message.payload)
        async with RedisConnection(self._target, db=self._db) as client:
            await client.pipeline([
                [
                    "XACK",
                    stream_key,
                    self._group_name,
                    message.msg_id,
                ],
                [
                    "XADD",
                    stream_key,
                    "MAXLEN",
                    _DEFAULT_QUEUE_MAX_LEN,
                    "*",
                    *pieces,
                ],
            ])

    async def _read_messages_loop(self, stream_key: str) -> None:
        log.info("Starting message reading loop for stream {}", stream_key)
        while not self._closed:
            try:
                await self._read_messages(stream_key)
            except hiredis.HiredisError as e:
                await self._failover_consumer(e)
            except Exception as e:
                log.exception("Error while reading messages: {}", e)

    async def _read_messages(self, stream_key: str) -> None:
        log.debug("Reading messages from stream {}", stream_key)
        async with RedisConnection(self._target, db=self._db) as client:
            reply = await client.execute(
                [
                    "XREADGROUP",
                    "GROUP",
                    self._group_name,
                    self._consumer_id,
                    "COUNT",
                    1,
                    "BLOCK",
                    30_000,
                    "STREAMS",
                    stream_key,
                    ">",  # fetch messages not seen by other consumers
                ],
                command_timeout=5,
            )
            if reply is None:
                log.debug("No messages to read")
                return
            for stream_msg in reply.values():
                for msg_id, messages in stream_msg:
                    payload = {}
                    for i in range(0, len(messages), 2):
                        key = messages[i]
                        value = messages[i + 1]
                        payload[key] = value
                    msg = MQMessage(msg_id, payload)
                    await self._consume_queue.put(msg)

    async def _read_broadcast_messages_loop(self, subscribe_channels: set[str]) -> None:
        log.info("Starting broadcast messages reading loop for channels: {}", subscribe_channels)
        while not self._closed:
            try:
                await self._read_broadcast_messages(subscribe_channels)
            except hiredis.HiredisError as e:
                await self._failover_consumer(e)
            except Exception as e:
                log.error("Error while reading broadcast messages: {}", e)
                await asyncio.sleep(_DEFAULT_AUTO_RECONNECT_INTERVAL)

    async def _read_broadcast_messages(self, subscribe_channels: set[str]) -> None:
        async with RedisConnection(self._target, db=self._db) as client:
            for channel in subscribe_channels:
                await client.execute(["SUBSCRIBE", channel])
            async for reply in client.subscribe_reader():
                log.debug("Received reply from subscribe: {}", reply)
                if len(reply) < 3:
                    log.debug("Invalid reply from subscribe: {}", reply)
                    continue
                _, channel, payload_bytes = reply
                payload = load_json(payload_bytes)
                await self._subscribe_queue.put(
                    BroadcastMessage(
                        payload=payload,
                    )
                )

    async def _failover_consumer(self, e: hiredis.HiredisError) -> None:
        # If the group does not exist, create it
        # and start the auto claim loop again
        if not e.args[0].startswith("NOGROUP "):
            log.error("Unexpected error in consumer: {}", e)
            return
        try:
            async with RedisConnection(self._target, db=self._db) as client:
                await client.execute([
                    "XGROUP",
                    "CREATE",
                    self._anycast_stream_key,
                    self._group_name,
                    "$",
                    "MKSTREAM",
                ])
        except Exception as internal_e:
            log.error("Error while creating group: {}", internal_e)


def _generate_consumer_id(node_id: Optional[str]) -> str:
    h = hashlib.sha1()
    h.update(str(node_id or socket.getfqdn()).encode("utf8"))
    hostname_hash = h.hexdigest()
    h = hashlib.sha1()
    h.update(__file__.encode("utf8"))
    installation_path_hash = h.hexdigest()
    pidx = process_index.get(0)
    return f"{hostname_hash}:{installation_path_hash}:{pidx}"
