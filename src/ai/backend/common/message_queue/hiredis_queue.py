import asyncio
import hashlib
import logging
import socket
from typing import AsyncGenerator, Optional, Self

import hiredis
from aiotools.server import process_index

from ai.backend.common.defs import RedisRole
from ai.backend.common.json import dump_json, load_json
from ai.backend.common.message_queue.redis_queue import RedisMQArgs
from ai.backend.common.redis_client import RedisConnection
from ai.backend.logging.utils import BraceStyleAdapter

from ..types import RedisProfileTarget, RedisTarget
from .queue import (
    AbstractMessageQueue,
    BroadcastChannel,
    BroadcastMessage,
    MessageId,
    MQMessage,
    QueueStream,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_AUTOCLAIM_INTERVAL = 60_000
_DEFAULT_AUTOCLAIM_COUNT = 64
_DEFAULT_QUEUE_MAX_LEN = 128


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
    _anycast_stream_key: QueueStream
    _broadcast_channel: BroadcastChannel
    _group_name: str
    _consumer_id: str
    _closed: bool
    # loop tasks for consuming messages
    _loop_tasks: list[asyncio.Task]

    def __init__(self, target: RedisTarget, args: RedisMQArgs) -> None:
        self._target = target
        self._db = RedisRole.STREAM.db_index
        self._consume_queue = asyncio.Queue()
        self._subscribe_queue = asyncio.Queue()
        self._anycast_stream_key = args.anycast_stream_key
        self._broadcast_channel = args.broadcast_channel
        self._group_name = args.group_name
        self._consumer_id = _generate_consumer_id(args.node_id)
        self._closed = False
        start_id = args.autoclaim_start_id or "0-0"
        self._loop_tasks = []
        for consume_stream_key in args.consume_stream_keys:
            self._loop_tasks.append(
                asyncio.create_task(
                    self._auto_claim_loop(consume_stream_key, start_id, args.autoclaim_idle_timeout)
                )
            )
            self._loop_tasks.append(
                asyncio.create_task(self._read_messages_loop(consume_stream_key))
            )
        if args.subscribe_channels:
            self._loop_tasks.append(
                asyncio.create_task(self._read_broadcast_messages_loop(args.subscribe_channels))
            )

    @classmethod
    def start(
        cls,
        redis_profile_target: RedisProfileTarget,
        mq_args: RedisMQArgs,
    ) -> Self:
        stream_redis_target = redis_profile_target.profile_target(RedisRole.STREAM)
        return cls(
            stream_redis_target,
            mq_args,
        )

    async def anycast(self, payload: dict[bytes, bytes]) -> None:
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

    async def broadcast(self, payload: dict[str, bytes]) -> None:
        async with RedisConnection(self._target, db=self._db) as client:
            payload_bytes = dump_json(payload)
            await client.execute([
                "PUBLISH",
                self._broadcast_channel,
                payload_bytes,
            ])

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

    async def _done(self, consume_stream_key: QueueStream, msg_id: MessageId) -> None:
        async with RedisConnection(self._target, db=self._db) as client:
            await client.execute([
                "XACK",
                consume_stream_key,
                self._group_name,
                msg_id,
            ])

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for task in self._loop_tasks:
            log.debug("Cancelling task {}", task.get_name())
            task.cancel()

    async def _auto_claim_loop(
        self, consume_stream_key: QueueStream, autoclaim_start_id: str, autoclaim_idle_timeout: int
    ) -> None:
        log.debug("Starting auto claim loop for stream {}", consume_stream_key)
        while not self._closed:
            try:
                next_start_id, claimed = await self._auto_claim(
                    consume_stream_key, autoclaim_start_id, autoclaim_idle_timeout
                )
                if not claimed:
                    await asyncio.sleep(_DEFAULT_AUTOCLAIM_INTERVAL / 1000)
                    continue
                autoclaim_start_id = next_start_id
            except hiredis.HiredisError as e:
                await self._failover_consumer(e)
            except Exception as e:
                log.error("Error while auto claiming messages: {}", e)

    async def _auto_claim(
        self, consume_stream_key: QueueStream, autoclaim_start_id: str, autoclaim_idle_timeout: int
    ) -> tuple[str, bool]:
        async with RedisConnection(self._target, db=self._db) as client:
            reply = await client.execute(
                [
                    "XAUTOCLAIM",
                    consume_stream_key,
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
                        await self._retry_message(msg)
                    else:
                        # discard the message
                        await self._done(consume_stream_key, msg_id)
        return autoclaim_start_id, True

    async def _retry_message(self, message: MQMessage) -> None:
        pieces = _make_pieces(message.payload)
        async with RedisConnection(self._target, db=self._db) as client:
            await client.pipeline([
                [
                    "XACK",
                    self._anycast_stream_key,
                    self._group_name,
                    message.msg_id,
                ],
                [
                    "XADD",
                    self._anycast_stream_key,
                    "MAXLEN",
                    _DEFAULT_QUEUE_MAX_LEN,
                    "*",
                    *pieces,
                ],
            ])

    async def _read_messages_loop(self, consume_stream_key: QueueStream) -> None:
        log.info("Reading messages from stream {}", consume_stream_key)
        while not self._closed:
            try:
                await self._read_messages(consume_stream_key)
            except hiredis.HiredisError as e:
                await self._failover_consumer(e)
            except Exception as e:
                log.error("Error while reading messages: {}", e)

    async def _read_messages(self, consume_stream_key: str) -> None:
        log.debug("Reading messages from stream {}", consume_stream_key)
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
                    consume_stream_key,
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

    async def _read_broadcast_messages_loop(
        self, subscribe_channels: list[BroadcastChannel]
    ) -> None:
        log.debug("Reading broadcast messages from stream {}", subscribe_channels)
        while not self._closed:
            try:
                await self._read_broadcast_messages(subscribe_channels)
            except Exception as e:
                log.exception("Error while reading broadcast messages: {}", e)

    async def _read_broadcast_messages(self, subscribe_channels: list[BroadcastChannel]) -> None:
        async with RedisConnection(self._target, db=self._db) as client:
            for channel in subscribe_channels:
                await client.execute(["SUBSCRIBE", channel])
            async for reply in client.subscribe_reader():
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
