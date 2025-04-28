import asyncio
import hashlib
import logging
import socket
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

import redis
from aiotools.server import process_index

from ai.backend.logging.utils import BraceStyleAdapter

from .. import redis_helper
from ..types import RedisConnectionInfo
from .queue import AbstractMessageQueue, MessageId, MQMessage

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_AUTOCLAIM_IDLE_TIMEOUT = 300_000  # 5 minutes
_DEFAULT_AUTOCLAIM_INTERVAL = 60_000
_DEFAULT_AUTOCLAIM_COUNT = 64
_DEFAULT_QUEUE_MAX_LEN = 128


@dataclass
class RedisMQArgs:
    # Required arguments
    stream_key: str
    group_name: str
    node_id: str
    # Optional arguments
    autoclaim_idle_timeout: int = _DEFAULT_AUTOCLAIM_IDLE_TIMEOUT
    autoclaim_start_id: Optional[str] = None


class RedisQueue(AbstractMessageQueue):
    _conn: RedisConnectionInfo
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

    def __init__(self, conn: RedisConnectionInfo, args: RedisMQArgs) -> None:
        self._conn = conn
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
        """
        Send a message to the queue.
        If the queue is full, the oldest message will be removed.
        The new message will be added to the end of the queue.
        """
        if self._closed:
            raise RuntimeError("Queue is closed")
        await self._conn.client.xadd(self._stream_key, payload, maxlen=_DEFAULT_QUEUE_MAX_LEN)

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
        await self._conn.client.xack(self._stream_key, self._group_name, msg_id)

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._conn.close()
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
            except redis.exceptions.ResponseError as e:
                await self._failover_consumer(e)
            except Exception as e:
                log.error("Error while auto claiming messages: {}", e)

    async def _auto_claim(
        self, autoclaim_start_id: str, autoclaim_idle_timeout: int
    ) -> tuple[str, bool]:
        reply = await redis_helper.execute(
            self._conn,
            lambda r: r.xautoclaim(
                self._stream_key,
                self._group_name,
                self._consumer_id,
                min_idle_time=autoclaim_idle_timeout,
                start_id=autoclaim_start_id,
                count=_DEFAULT_AUTOCLAIM_COUNT,
            ),
            command_timeout=autoclaim_idle_timeout / 1000,
        )
        if reply[0] == b"0-0":
            log.debug("No messages to claim")
            return autoclaim_start_id, False
        autoclaim_start_id = reply[0]
        for msg_id, msg_data in reply[1]:
            msg = MQMessage(msg_id, msg_data)
            if msg.retry():
                await self._retry_message(msg)
            else:
                # discard the message
                await self.done(msg_id)

        return autoclaim_start_id, True

    async def _retry_message(self, message: MQMessage) -> None:
        pipe = self._conn.client.pipeline(transaction=True)
        pipe.xack(self._stream_key, self._group_name, message.msg_id)
        pipe.xadd(self._stream_key, message.payload, maxlen=_DEFAULT_QUEUE_MAX_LEN)
        await pipe.execute()

    async def _read_messages_loop(self) -> None:
        log.debug("Reading messages from stream {}", self._stream_key)
        while not self._closed:
            try:
                await self._read_messages()
            except redis.exceptions.ResponseError as e:
                await self._failover_consumer(e)
            except Exception as e:
                log.error("Error while reading messages: {}", e)

    async def _read_messages(self) -> None:
        reply = await redis_helper.execute(
            self._conn,
            lambda r: r.xreadgroup(
                self._group_name,
                self._consumer_id,
                {self._stream_key: ">"},
                count=1,
                block=1000,
            ),
        )
        if not reply:
            log.debug("No messages to read")
            return
        for _, events in reply:
            for msg_id, msg_data in events:
                if msg_data is None:
                    continue
                msg = MQMessage(msg_id, msg_data)
                await self._consume_queue.put(msg)

    async def _read_broadcast_messages_loop(self) -> None:
        log.debug("Reading broadcast messages from stream {}", self._stream_key)
        last_msg_id = "$"
        while not self._closed:
            try:
                last_msg_id = await self._read_broadcast_messages(last_msg_id)
            except redis.exceptions.ResponseError as e:
                await self._failover_consumer(e)
                last_msg_id = "$"
            except Exception as e:
                log.error("Error while reading broadcast messages: {}", e)

    async def _read_broadcast_messages(self, last_msg_id: str) -> str:
        reply = await redis_helper.execute(
            self._conn,
            lambda r: r.xread(
                {self._stream_key: last_msg_id},
                count=1,
                block=1000,
            ),
        )
        if not reply:
            log.debug("No broadcast messages to read")
            return last_msg_id
        for _, events in reply:
            for msg_id, msg_data in events:
                if msg_data is None:
                    continue
                msg = MQMessage(msg_id, msg_data)
                await self._subscribe_queue.put(msg)
                last_msg_id = msg_id
        return last_msg_id

    async def _failover_consumer(self, e: redis.exceptions.ResponseError) -> None:
        # If the group does not exist, create it
        # and start the auto claim loop again
        if "NOGROUP" in str(e):
            log.warning(
                "Consumer group does not exist. Creating group {} for stream {}",
                self._group_name,
                self._stream_key,
            )
            try:
                await redis_helper.execute(
                    self._conn,
                    lambda r: r.xgroup_create(self._stream_key, self._group_name, mkstream=True),
                )
            except Exception as internal_exception:
                log.warning(
                    "Error while creating consumer group {} for stream {}: {}",
                    self._group_name,
                    self._stream_key,
                    internal_exception,
                )
        else:
            log.error("Error while reading messages: {}", e)


def _generate_consumer_id(node_id: Optional[str]) -> str:
    h = hashlib.sha1()
    h.update(str(node_id or socket.getfqdn()).encode("utf8"))
    hostname_hash = h.hexdigest()
    h = hashlib.sha1()
    h.update(__file__.encode("utf8"))
    installation_path_hash = h.hexdigest()
    pidx = process_index.get(0)
    return f"{hostname_hash}:{installation_path_hash}:{pidx}"
