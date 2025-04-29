import asyncio
import hashlib
import logging
import socket
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

import hiredis
from aiotools.server import process_index

from ai.backend.common.redis_client import RedisConnection
from ai.backend.logging.utils import BraceStyleAdapter

from ..types import RedisConfig
from .queue import AbstractMessageQueue, MessageId, MQMessage

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_AUTOCLAIM_IDLE_TIMEOUT = 300_000  # 5 minutes
_DEFAULT_AUTOCLAIM_INTERVAL = 60_000
_DEFAULT_AUTOCLAIM_COUNT = 64
_DEFAULT_QUEUE_MAX_LEN = 128


def _make_pieces(payload: dict[bytes, bytes]) -> list[bytes]:
    pieces = []
    for k, v in payload.items():
        pieces.append(k)
        pieces.append(v)
    return pieces


@dataclass
class HiRedisMQArgs:
    # Required arguments
    stream_key: str
    group_name: str
    node_id: str
    db: int
    # Optional arguments
    autoclaim_idle_timeout: int = _DEFAULT_AUTOCLAIM_IDLE_TIMEOUT
    autoclaim_start_id: Optional[str] = None


class HiRedisQueue(AbstractMessageQueue):
    _conf: RedisConfig
    _db: int
    _consume_queue: asyncio.Queue[MQMessage]
    _subscribe_queue: asyncio.Queue[MQMessage]
    _stream_key: str
    _group_name: str
    _consumer_id: str
    _closed: bool
    # loop tasks for consuming messages
    _auto_claim_loop_task: asyncio.Task
    _read_messages_task: asyncio.Task
    _read_broadcast_messages_task: asyncio.Task

    def __init__(self, conf: RedisConfig, args: HiRedisMQArgs) -> None:
        self._conf = conf
        self._db = args.db
        self._consume_queue = asyncio.Queue()
        self._subscribe_queue = asyncio.Queue()
        self._stream_key = args.stream_key
        self._group_name = args.group_name
        self._consumer_id = _generate_consumer_id(args.node_id)
        self._closed = False
        start_id = args.autoclaim_start_id or "0-0"
        self._auto_claim_loop_task = asyncio.create_task(
            self._auto_claim_loop(start_id, args.autoclaim_idle_timeout)
        )
        self._read_messages_task = asyncio.create_task(self._read_messages_loop())
        self._read_broadcast_messages_task = asyncio.create_task(
            self._read_broadcast_messages_loop()
        )

    async def send(self, payload: dict[bytes, bytes]) -> None:
        async with RedisConnection(self._conf, db=self._db) as client:
            pieces = _make_pieces(payload)
            await client.execute([
                "XADD",
                self._stream_key,
                "MAXLEN",
                _DEFAULT_QUEUE_MAX_LEN,
                "*",
                *pieces,
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

    async def subscribe_queue(self) -> AsyncGenerator[MQMessage, None]:  # type: ignore
        while not self._closed:
            try:
                yield await self._subscribe_queue.get()
            except asyncio.CancelledError:
                break

    async def done(self, msg_id: MessageId) -> None:
        async with RedisConnection(self._conf, db=self._db) as client:
            await client.execute([
                "XACK",
                self._stream_key,
                self._group_name,
                msg_id,
            ])

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._auto_claim_loop_task.cancel()
        self._read_messages_task.cancel()
        self._read_broadcast_messages_task.cancel()

    async def _auto_claim_loop(self, autoclaim_start_id: str, autoclaim_idle_timeout: int) -> None:
        log.debug("Starting auto claim loop for stream {}", self._stream_key)
        while not self._closed:
            try:
                next_start_id, claimed = await self._auto_claim(
                    autoclaim_start_id, autoclaim_idle_timeout
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
        self, autoclaim_start_id: str, autoclaim_idle_timeout: int
    ) -> tuple[str, bool]:
        async with RedisConnection(self._conf, db=self._db) as client:
            reply = await client.execute(
                [
                    "XAUTOCLAIM",
                    self._stream_key,
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
                log.debug("No messages to claim")
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
                        await self.done(msg_id)
        return autoclaim_start_id, True

    async def _retry_message(self, message: MQMessage) -> None:
        pieces = _make_pieces(message.payload)
        async with RedisConnection(self._conf, db=self._db) as client:
            await client.pipeline([
                [
                    "XACK",
                    self._stream_key,
                    self._group_name,
                    message.msg_id,
                ],
                [
                    "XADD",
                    self._stream_key,
                    "MAXLEN",
                    _DEFAULT_QUEUE_MAX_LEN,
                    "*",
                    *pieces,
                ],
            ])

    async def _read_messages_loop(self) -> None:
        log.debug("Reading messages from stream {}", self._stream_key)
        while not self._closed:
            try:
                await self._read_messages()
            except hiredis.HiredisError as e:
                await self._failover_consumer(e)
            except Exception as e:
                log.error("Error while reading messages: {}", e)

    async def _read_messages(self) -> None:
        log.debug("Reading messages from stream {}", self._stream_key)
        async with RedisConnection(self._conf, db=self._db) as client:
            reply = await client.execute(
                [
                    "XREADGROUP",
                    "GROUP",
                    self._group_name,
                    self._consumer_id,
                    "COUNT",
                    1,
                    "BLOCK",
                    1000,
                    "STREAMS",
                    self._stream_key,
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

    async def _read_broadcast_messages_loop(self) -> None:
        log.debug("Reading broadcast messages from stream {}", self._stream_key)
        last_msg_id = b"$"
        while not self._closed:
            try:
                last_msg_id = await self._read_broadcast_messages(last_msg_id)
            except hiredis.HiredisError as e:
                await self._failover_consumer(e)
                last_msg_id = b"$"
            except Exception as e:
                log.error("Error while reading broadcast messages: {}", e)

    async def _read_broadcast_messages(self, last_msg_id: bytes) -> bytes:
        async with RedisConnection(self._conf, db=self._db) as client:
            reply = await client.execute(
                ["XREAD", "BLOCK", "1000", "STREAMS", self._stream_key, last_msg_id],
                command_timeout=5,
            )
            if reply is None:
                log.debug("No messages to read")
                return last_msg_id
            for stream_msg in reply.values():
                for msg_id, messages in stream_msg:
                    payload = {}
                    for i in range(0, len(messages), 2):
                        key = messages[i]
                        value = messages[i + 1]
                        payload[key] = value
                    msg = MQMessage(msg_id, payload)
                    await self._subscribe_queue.put(msg)
                    last_msg_id = msg_id
        return last_msg_id

    async def _failover_consumer(self, e: hiredis.HiredisError) -> None:
        # If the group does not exist, create it
        # and start the auto claim loop again
        if not e.args[0].startswith("NOGROUP "):
            log.error("Error while auto claiming messages: {}", e)
            return
        try:
            async with RedisConnection(self._conf, db=self._db) as client:
                await client.execute([
                    "XGROUP",
                    "CREATE",
                    self._stream_key,
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
