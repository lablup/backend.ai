import asyncio
from contextlib import aclosing
from dataclasses import dataclass
import logging
from typing import AsyncGenerator, Self

from ai.backend.common import redis_helper
from ai.backend.logging.utils import BraceStyleAdapter

from .base import AbstractMessageQueue, MQMessage, AbstractMQMessagePayload
from ai.backend.common.types import RedisConnectionInfo


log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class RedisMQOptions:
    autoclaim_idle_timeout: int
    autoclaim_start_id: str
    consumer_id: str
    group_name: str
    stream_key: str


class RedisQueue(AbstractMessageQueue):
    _conn: RedisConnectionInfo
    _consume_queue: asyncio.Queue[MQMessage]
    _subscribe_queue: asyncio.Queue[MQMessage]
    _closed: bool
    _options: RedisMQOptions
    _autoclaim_start_id: str
    # loop tasks for consuming messages
    _auto_claim_loop_task: asyncio.Task
    _read_messages_task: asyncio.Task
    _read_broadcast_messages_task: asyncio.Task
    def __init__(self, conn: RedisConnectionInfo, opts: RedisMQOptions) -> None:
        self._consume_queue = asyncio.Queue()
        self._subscribe_queue = asyncio.Queue()
        self._conn = conn
        self._closed = False
        self._options = opts
        self._autoclaim_start_id = opts.autoclaim_start_id
        self._auto_claim_loop_task = asyncio.create_task(self._auto_claim_loop())
        self._read_messages_task = asyncio.create_task(self._read_messages())
        self._read_broadcast_messages_task = asyncio.create_task(self._read_broadcast_messages())

    @classmethod
    async def create(cls, conn: RedisConnectionInfo, opts: RedisMQOptions) -> Self:
        self = cls(conn, opts)
        return self
    
    async def send(self, key: str, msg: AbstractMQMessagePayload) -> None:
        if self._closed:
            raise RuntimeError("Redis Queue is already closed")
        raw_event = msg.serialize()
        await redis_helper.execute(
            self._conn,
            lambda r: r.xadd(key, raw_event),  # type: ignore # aio-libs/aioredis-py#1182
        )
    
    async def consume_queue(self) -> AsyncGenerator[MQMessage, None]:
        while not self._closed:
            try:
                yield await self._consume_queue.get()
            except asyncio.CancelledError:
                break
    
    async def subscribe_queue(self) -> AsyncGenerator[MQMessage, None]:
        while not self._closed:
            try:
                yield await self._subscribe_queue.get()
            except asyncio.CancelledError:
                break
    
    async def _put_consume_queue(self, msg_id: str, msg_data: dict[bytes, bytes]) -> None:
        payload = AbstractMQMessagePayload.deserialize(msg_data)
        msg = MQMessage(msg_id, payload)
        await self._consume_queue.put(msg)
    
    async def _put_subscribe_queue(self, msg_id: str, msg_data: dict[bytes, bytes]) -> None:
        payload = AbstractMQMessagePayload.deserialize(msg_data)
        msg = MQMessage(msg_id, payload)
        await self._subscribe_queue.put(msg)

    async def _auto_claim_loop(self) -> None:
        while not self._closed:
            reply = await redis_helper.execute(
                self._conn,
                lambda r: r.execute_command(
                    "XAUTOCLAIM",
                    self._options.stream_key,
                    self._options.group_name,
                    self._options.consumer_id,
                    str(self._options.autoclaim_idle_timeout),
                    self._autoclaim_start_id,
                ),
                command_timeout=self._options.autoclaim_idle_timeout / 1000,
            )
            for msg_id, msg_data in reply[1]:
                await self._put_consume_queue(msg_id, msg_data)
            if reply[0] == b"0-0":
                log.debug("No messages to claim")
                continue
            self._autoclaim_start_id = reply[0]

    async def _read_messages(self) -> None:
        while not self._closed:
            reply = await redis_helper.execute(
                self._conn,
                lambda r: r.xreadgroup(
                    self._options.group_name,
                    self._options.consumer_id,
                    {self._options.stream_key: ">"},
                    count=1,
                    block=1000,
                ),
            )
            for _, events in reply:
                for msg_id, msg_data in events:
                    if msg_data == None:
                        continue
                    await self._put_consume_queue(msg_id, msg_data)

    async def _read_broadcast_messages(self) -> None:
        while not self._closed:
            async with aclosing(
                redis_helper.read_stream(
                    self.redis_client,
                    self._stream_key,
                )
            ) as agen:
                async for msg_id, msg_data in agen:
                    if msg_data == None:
                        continue
                    await self._put_subscribe_queue(msg_id, msg_data)

    async def done(self, key: str, msg_id: str) -> None:
        if self._closed:
            raise RuntimeError("Queue is closed")
        await redis_helper.execute(
            self._conn,
            lambda r: r.xack(key, self.group_name, msg_id),
        )
    
    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._conn.close()
        self._auto_claim_loop_task.cancel()
        self._read_messages_task.cancel()
        self._read_broadcast_messages_task.cancel()
        