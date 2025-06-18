import asyncio
import hashlib
import logging
import socket
from dataclasses import dataclass
from typing import AsyncGenerator, List, Mapping, Optional, Self

import redis
from aiotools.server import process_index
from glide import (
    GlideClient,
    StreamAddOptions,
    StreamGroupOptions,
    StreamReadGroupOptions,
    TrimByMaxLen,
)

from ai.backend.common.defs import RedisRole
from ai.backend.common.json import dump_json, load_json
from ai.backend.logging.utils import BraceStyleAdapter

from .. import redis_helper
from ..types import RedisConnectionInfo, RedisProfileTarget
from .queue import (
    AbstractMessageQueue,
    BroadcastChannel,
    BroadcastMessage,
    MessageId,
    MQMessage,
    QueueStream,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_AUTOCLAIM_IDLE_TIMEOUT = 300_000  # 5 minutes
_DEFAULT_AUTOCLAIM_INTERVAL = 60_000
_DEFAULT_AUTOCLAIM_COUNT = 64
_DEFAULT_QUEUE_MAX_LEN = 128


@dataclass
class RedisMQArgs:
    # Required arguments
    anycast_stream_key: QueueStream
    broadcast_channel: BroadcastChannel
    consume_stream_keys: list[QueueStream]
    subscribe_channels: list[BroadcastChannel]
    group_name: str
    node_id: str
    # Optional arguments
    autoclaim_idle_timeout: int = _DEFAULT_AUTOCLAIM_IDLE_TIMEOUT
    autoclaim_start_id: Optional[str] = None


class RedisQueue(AbstractMessageQueue):
    _conn: RedisConnectionInfo
    _consume_queue: asyncio.Queue[MQMessage]
    _subscribe_queue: asyncio.Queue[BroadcastMessage]
    _anycast_stream_key: QueueStream
    _broadcast_channel: BroadcastChannel
    _group_name: str
    _consumer_id: str
    _closed: bool
    # loop tasks for consuming messages
    _loop_taks: list[asyncio.Task]

    def __init__(self, conn: RedisConnectionInfo, args: RedisMQArgs) -> None:
        self._conn = conn
        self._consume_queue = asyncio.Queue()
        self._subscribe_queue = asyncio.Queue()
        self._anycast_stream_key = args.anycast_stream_key
        self._broadcast_channel = args.broadcast_channel
        self._group_name = args.group_name
        self._consumer_id = _generate_consumer_id(args.node_id)
        self._closed = False
        start_id = args.autoclaim_start_id or "0-0"
        self._loop_taks = []
        for consume_stream_key in args.consume_stream_keys:
            self._loop_taks.append(
                asyncio.create_task(
                    self._auto_claim_loop(consume_stream_key, start_id, args.autoclaim_idle_timeout)
                )
            )
            self._loop_taks.append(
                asyncio.create_task(self._read_messages_loop(consume_stream_key))
            )
        if args.subscribe_channels:
            self._loop_taks.append(
                asyncio.create_task(self._read_broadcast_messages_loop(args.subscribe_channels))
            )

    @classmethod
    async def start(
        cls,
        redis_profile_target: RedisProfileTarget,
        mq_args: RedisMQArgs,
    ) -> Self:
        stream_redis_target = redis_profile_target.profile_target(RedisRole.STREAM)
        stream_redis = await redis_helper.create_valkey_client(
            stream_redis_target,
            name="event_producer.stream",
            db=RedisRole.STREAM.db_index,
            pubsub_channels={channel.value for channel in mq_args.subscribe_channels},
        )
        return cls(stream_redis, mq_args)

    async def anycast(self, payload: dict[bytes, bytes]) -> None:
        """
        Send a message to the queue.
        If the queue is full, the oldest message will be removed.
        The new message will be added to the end of the queue.
        """
        if self._closed:
            raise RuntimeError("Queue is closed")
        payload_tuple = tuple((k, v) for k, v in payload.items())
        await self._conn.client.xadd(
            self._anycast_stream_key,
            payload_tuple,
            StreamAddOptions(trim=TrimByMaxLen(exact=True, threshold=_DEFAULT_QUEUE_MAX_LEN)),
        )

    async def broadcast(self, payload: dict[str, bytes]) -> None:
        """
        Broadcast a message to all subscribers of the queue.
        The message will be delivered to all subscribers.
        Broadcasted messages can be lost if there are no subscribers at the time of sending.
        """
        if self._closed:
            raise RuntimeError("Queue is closed")
        payload_bytes = dump_json(payload)
        await self._conn.client.publish(self._broadcast_channel, payload_bytes)

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
        await self._conn.client.xack(consume_stream_key, self._group_name, msg_id)

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._conn.close()
        for task in self._loop_taks:
            log.debug("Cancelling task {}", task)
            task.cancel()

    async def _auto_claim_loop(
        self, consume_stream_key: QueueStream, autoclaim_start_id: str, autoclaim_idle_timeout: int
    ) -> None:
        log.info("Starting auto claim loop for stream {}", consume_stream_key)
        while not self._closed:
            try:
                next_start_id, claimed = await self._auto_claim(
                    consume_stream_key, autoclaim_start_id, autoclaim_idle_timeout
                )
                if not claimed:
                    await asyncio.sleep(_DEFAULT_AUTOCLAIM_INTERVAL / 1000)
                    continue
                autoclaim_start_id = next_start_id
            except redis.exceptions.ResponseError as e:
                await self._failover_consumer(consume_stream_key, e)
            except Exception as e:
                log.exception("Error while auto claiming messages: {}", e)
        log.info("Auto claim loop stopped for stream {}", consume_stream_key)

    async def _auto_claim(
        self, consume_stream_key: QueueStream, autoclaim_start_id: str, autoclaim_idle_timeout: int
    ) -> tuple[str, bool]:
        async def auto_claim(cli: GlideClient):
            return await cli.xautoclaim(
                consume_stream_key,
                self._group_name,
                self._consumer_id,
                min_idle_time_ms=autoclaim_idle_timeout,
                start=autoclaim_start_id,
                count=_DEFAULT_AUTOCLAIM_COUNT,
            )

        reply = await redis_helper.execute(
            self._conn,
            auto_claim,
            command_timeout=autoclaim_idle_timeout / 1000,
        )
        if reply[0] == b"0-0":
            return autoclaim_start_id, False
        autoclaim_start_id = reply[0]
        for msg_id, msg_data_list in reply[1]:
            if msg_data_list is None:
                continue
            mst_data = {msg[0]: msg[1] for msg in msg_data_list}
            msg = MQMessage(msg_id, mst_data)
            if msg.retry():
                await self._retry_message(consume_stream_key, msg)
            else:
                # discard the message
                await self._done(consume_stream_key, msg_id)

        return autoclaim_start_id, True

    async def _retry_message(self, consume_stream_key: QueueStream, message: MQMessage) -> None:
        pipe = self._conn.client.pipeline(transaction=True)
        pipe.xack(consume_stream_key, self._group_name, message.msg_id)
        pipe.xadd(consume_stream_key, message.payload, maxlen=_DEFAULT_QUEUE_MAX_LEN)
        await pipe.execute()

    async def _read_messages_loop(self, consume_stream_key: QueueStream) -> None:
        log.info("Reading messages from stream {}", consume_stream_key)
        while not self._closed:
            try:
                await self._read_messages(consume_stream_key)
            except redis.exceptions.ResponseError as e:
                await self._failover_consumer(consume_stream_key, e)
            except Exception as e:
                log.exception("Error while reading messages: {}", e)
        log.info("consume messages loop stopped")

    async def _read_messages(self, consume_stream_key: QueueStream) -> None:
        async def read_group(cli: GlideClient):
            return await cli.xreadgroup(
                {consume_stream_key: ">"},
                self._group_name,
                self._consumer_id,
                options=StreamReadGroupOptions(
                    block_ms=30_000,  # 30 seconds
                    count=1,  # Read one message at a time
                ),
            )

        reply: Optional[
            Mapping[bytes, Mapping[bytes, Optional[List[List[bytes]]]]]
        ] = await redis_helper.execute(
            self._conn,
            read_group,
        )
        if not reply:
            log.debug("No messages to read")
            return
        for _, events in reply.items():
            for msg_id, msg_data_list in events.items():
                if msg_data_list is None:
                    continue
                msg_data = {msg[0]: msg[1] for msg in msg_data_list}
                msg = MQMessage(msg_id, msg_data)
                await self._consume_queue.put(msg)

    async def _read_broadcast_messages_loop(
        self, subscribe_channels: list[BroadcastChannel]
    ) -> None:
        log.info("Reading broadcast messages from channels {}", subscribe_channels)
        while not self._closed:
            try:
                await self._read_broadcast_messages()
            except Exception as e:
                log.exception("Error while reading broadcast messages: {}", e)
        log.info("Broadcast messages loop stopped")

    async def _read_broadcast_messages(self):
        while not self._closed:
            pubsub_msg = await self._conn.client.get_pubsub_message()
            payload = load_json(pubsub_msg.message)
            msg = BroadcastMessage(payload)
            await self._subscribe_queue.put(msg)

    async def _failover_consumer(
        self, consume_stream_key: QueueStream, e: redis.exceptions.ResponseError
    ) -> None:
        # If the group does not exist, create it
        # and start the auto claim loop again
        if "NOGROUP" in str(e):
            log.warning(
                "Consumer group does not exist. Creating group {} for stream {}",
                self._group_name,
                consume_stream_key,
            )
            try:

                async def create_group(cli: GlideClient):
                    return await cli.xgroup_create(
                        consume_stream_key,
                        self._group_name,
                        options=StreamGroupOptions(make_stream=True),
                    )

                await redis_helper.execute(
                    self._conn,
                    create_group,
                )
            except Exception as internal_exception:
                log.warning(
                    "Error while creating consumer group {} for stream {}: {}",
                    self._group_name,
                    consume_stream_key,
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
