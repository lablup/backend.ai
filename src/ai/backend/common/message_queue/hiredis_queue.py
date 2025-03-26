import asyncio
import hashlib
import logging
import socket
import time
from dataclasses import dataclass
from typing import AsyncGenerator, AsyncIterable, Optional

import hiredis
from aiotools.server import process_index

from ai.backend.common.redis_client import RedisClient, RedisConnection
from ai.backend.logging.utils import BraceStyleAdapter

from ..types import RedisConfig
from .queue import AbstractMessageQueue, MessageId, MQMessage

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_AUTOCLAIM_IDLE_TIMEOUT = 1_000
_DEFAULT_AUTOCLAIM_INTERVAL = 60_000
_DEFAULT_AUTOCLAIM_COUNT = 64


async def _read_stream(
    client: RedisClient,
    stream_key: str,
    *,
    block_timeout: int = 10_000,  # in msec
) -> AsyncIterable[tuple[bytes, dict[bytes, bytes]]]:
    """
    A high-level wrapper for the XREAD command.
    """
    last_id = b"$"
    while True:
        try:
            reply = await client.execute(
                ["XREAD", "BLOCK", block_timeout, "STREAMS", stream_key, last_id],
                command_timeout=(block_timeout + 5_000) / 1000,
            )
            if not reply:
                continue
            # Keep some latest messages so that other manager
            # processes to have chances of fetching them.
            await client.execute([
                "XTRIM",
                stream_key,
                "MAXLEN",
                "~",
                128,
            ])
            for msg_id, msg_data_list in reply[stream_key.encode()]:
                try:
                    msg_data = {}
                    for idx in range(0, len(msg_data_list), 2):
                        msg_data[msg_data_list[idx]] = msg_data_list[idx + 1]
                    yield msg_id, msg_data
                finally:
                    last_id = msg_id
        except asyncio.CancelledError:
            raise


async def _autoclaim(
    client: RedisClient,
    stream_key: str,
    group_name: str,
    consumer_id: str,
    *,
    autoclaim_idle_timeout: int = 1_000,  # in msec
) -> AsyncIterable[tuple[bytes, dict[bytes, bytes]]]:
    """
    A high-level wrapper for the XAUTOCLAIM command
    combined with XGROUP_CREATE.
    """
    autoclaim_start_id = b"0-0"
    while True:
        try:
            reply = await client.execute(
                [
                    "XAUTOCLAIM",
                    stream_key,
                    group_name,
                    consumer_id,
                    str(autoclaim_idle_timeout),
                    autoclaim_start_id,
                ],
                command_timeout=(autoclaim_idle_timeout + 5_000) / 1000,
            )
            if not reply:
                await asyncio.sleep(_DEFAULT_AUTOCLAIM_INTERVAL / 1000)
                continue
            autoclaim_start_id = reply[0]
            for data in reply[1]:
                if data is None:
                    continue
                msg_id, msg_data_list = data
                msg_data = {}
                for idx in range(0, len(msg_data_list), 2):
                    msg_data[msg_data_list[idx]] = msg_data_list[idx + 1]
                yield msg_id, msg_data
        except asyncio.CancelledError:
            raise
        except hiredis.HiredisError as e:
            if e.args[0].startswith("NOGROUP "):
                try:
                    await client.execute([
                        "XGROUP",
                        "CREATE",
                        stream_key,
                        group_name,
                        "$",
                        "MKSTREAM",
                    ])
                except hiredis.HiredisError as e:
                    if e.args[0].startswith("BUSYGROUP "):
                        pass
                    else:
                        raise
                continue
            raise


async def _read_stream_by_group(
    client: RedisClient,
    stream_key: str,
    group_name: str,
    consumer_id: str,
    *,
    block_timeout: int = 10_000,  # in msec
) -> AsyncIterable[tuple[bytes, dict[bytes, bytes]]]:
    """
    A high-level wrapper for the XREADGROUP command
    combined with XAUTOCLAIM and XGROUP_CREATE.
    """
    while True:
        try:
            messages = []
            reply = await client.execute(
                [
                    "XREADGROUP",
                    "GROUP",
                    group_name,
                    consumer_id,
                    "BLOCK",
                    block_timeout,
                    "STREAMS",
                    stream_key,
                    ">",  # fetch messages not seen by other consumers
                ],
                command_timeout=(block_timeout + 5_000) / 1000,
            )
            if not reply:
                continue
            for msg_id, msg_data_list in reply[stream_key.encode()]:
                msg_data = {}
                for idx in range(0, len(msg_data_list), 2):
                    msg_data[msg_data_list[idx]] = msg_data_list[idx + 1]

                messages.append((msg_id, msg_data))
            await client.execute([
                "XACK",
                stream_key,
                group_name,
                *(msg_id for msg_id, msg_data in reply[stream_key.encode()]),
            ])
            for msg_id, msg_data in messages:
                yield msg_id, msg_data
        except asyncio.CancelledError:
            raise
        except hiredis.HiredisError as e:
            if not e.args[0].startswith("NOGROUP "):
                raise
            try:
                await client.execute([
                    "XGROUP",
                    "CREATE",
                    stream_key,
                    group_name,
                    "$",
                    "MKSTREAM",
                ])
            except hiredis.HiredisError as e:
                if not e.args[0].startswith("BUSYGROUP "):
                    raise
            continue


@dataclass
class HiRedisMQArgs:
    # Required arguments
    stream_key: str
    group_name: str
    node_id: str
    db: int
    # Optional arguments
    autoclaim_idle_timeout: int = _DEFAULT_AUTOCLAIM_IDLE_TIMEOUT
    reconnect_poll_interval: float = 0.3


class HiRedisQueue(AbstractMessageQueue):
    _conf: RedisConfig
    _db: int
    _consume_queue: asyncio.Queue[MQMessage]
    _subscribe_queue: asyncio.Queue[MQMessage]
    _stream_key: str
    _group_name: str
    _consumer_id: str
    _closed: bool
    _reconnect_poll_interval: float
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
        self._reconnect_poll_interval = args.reconnect_poll_interval
        self._auto_claim_loop_task = asyncio.create_task(
            self._auto_claim_loop(args.autoclaim_idle_timeout)
        )
        self._read_messages_task = asyncio.create_task(self._read_messages())
        self._read_broadcast_messages_task = asyncio.create_task(self._read_broadcast_messages())

    async def send(self, payload: dict[bytes, bytes]) -> None:
        raise NotImplementedError("send() is not implemented for HiRedisQueue")

    async def consume_queue(self) -> AsyncGenerator[MQMessage, None]:  # type: ignore
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

    async def _auto_claim_loop(self, autoclaim_idle_timeout: int) -> None:
        first_trial = time.perf_counter()
        retry_log_count = 0
        last_log_time = first_trial

        while not self._closed:
            try:
                async with RedisConnection(self._conf, db=self._db) as client:
                    async for msg_id, msg_data in _autoclaim(
                        client,
                        self._stream_key,
                        self._group_name,
                        self._consumer_id,
                        autoclaim_idle_timeout=autoclaim_idle_timeout,
                    ):
                        if self._closed:
                            return
                        if msg_data is None:
                            continue
                        msg = MQMessage(msg_id, msg_data)
                        await self._consume_queue.put(msg)
            except hiredis.HiredisError as e:
                if "READONLY" in e.args[0]:
                    self._show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                    if self._reconnect_poll_interval:
                        await asyncio.sleep(self._reconnect_poll_interval)
                    continue
                elif "NOREPLICAS" in e.args[0]:
                    self._show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                    if self._reconnect_poll_interval:
                        await asyncio.sleep(self._reconnect_poll_interval)
                    continue
                else:
                    raise
            except asyncio.TimeoutError as e:
                self._show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                if self._reconnect_poll_interval:
                    await asyncio.sleep(self._reconnect_poll_interval)
                continue
            except (ConnectionError, EOFError) as e:
                self._show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                if self._reconnect_poll_interval:
                    await asyncio.sleep(self._reconnect_poll_interval)
                continue
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("EventDispatcher.autoclaim(): unexpected-error")
                raise

    async def _read_messages(self) -> None:
        first_trial = time.perf_counter()
        retry_log_count = 0
        last_log_time = first_trial

        while not self._closed:
            try:
                async with RedisConnection(self._conf, db=self._db) as client:
                    async for msg_id, msg_data in _read_stream_by_group(
                        client,
                        self._stream_key,
                        self._group_name,
                        self._consumer_id,
                    ):
                        if self._closed:
                            return
                        if msg_data is None:
                            continue
                        msg = MQMessage(msg_id, msg_data)
                        await self._consume_queue.put(msg)
            except hiredis.HiredisError as e:
                if "READONLY" in e.args[0]:
                    self._show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                    if self._reconnect_poll_interval:
                        await asyncio.sleep(self._reconnect_poll_interval)
                    continue
                elif "NOREPLICAS" in e.args[0]:
                    self._show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                    if self._reconnect_poll_interval:
                        await asyncio.sleep(self._reconnect_poll_interval)
                    continue
                else:
                    raise
            except asyncio.TimeoutError as e:
                self._show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                if self._reconnect_poll_interval:
                    await asyncio.sleep(self._reconnect_poll_interval)
                continue
            except (ConnectionError, EOFError) as e:
                self._show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                if self._reconnect_poll_interval:
                    await asyncio.sleep(self._reconnect_poll_interval)
                continue
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("EventDispatcher.consume(): unexpected-error")
                raise

    async def _read_broadcast_messages(self) -> None:
        first_trial = time.perf_counter()
        retry_log_count = 0
        last_log_time = first_trial

        while not self._closed:
            try:
                async with RedisConnection(self._conf, db=self._db) as client:
                    async for msg_id, msg_data in _read_stream(
                        client,
                        self._stream_key,
                    ):
                        if self._closed:
                            return
                        if msg_data is None:
                            continue
                        msg = MQMessage(msg_id, msg_data)
                        await self._subscribe_queue.put(msg)
            except hiredis.HiredisError as e:
                if "READONLY" in e.args[0]:
                    self._show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                    if self._reconnect_poll_interval:
                        await asyncio.sleep(self._reconnect_poll_interval)
                    continue
                elif "NOREPLICAS" in e.args[0]:
                    self._show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                    if self._reconnect_poll_interval:
                        await asyncio.sleep(self._reconnect_poll_interval)
                    continue
                else:
                    raise
            except asyncio.TimeoutError as e:
                self._show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                if self._reconnect_poll_interval:
                    await asyncio.sleep(self._reconnect_poll_interval)
                continue
            except (ConnectionError, EOFError) as e:
                self._show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                if self._reconnect_poll_interval:
                    await asyncio.sleep(self._reconnect_poll_interval)
                continue
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("EventDispatcher.subscribe(): unexpected-error")
                raise

    def _show_retry_warning(
        self,
        e: Exception,
        first_trial: float,
        retry_log_count: int,
        last_log_time: float,
        warn_on_first_attempt: bool = True,
    ) -> None:
        now = time.perf_counter()
        if (warn_on_first_attempt and retry_log_count == 0) or now - last_log_time >= 10.0:
            log.warning(
                "Retrying due to interruption of Redis connection ({}, retrying-for: {:.3f}s)",
                repr(e),
                now - first_trial,
            )
            retry_log_count += 1
            last_log_time = now


def _generate_consumer_id(node_id: Optional[str]) -> str:
    h = hashlib.sha1()
    h.update(str(node_id or socket.getfqdn()).encode("utf8"))
    hostname_hash = h.hexdigest()
    h = hashlib.sha1()
    h.update(__file__.encode("utf8"))
    installation_path_hash = h.hexdigest()
    pidx = process_index.get(0)
    return f"{hostname_hash}:{installation_path_hash}:{pidx}"
