import asyncio
import logging
import time
from collections import defaultdict
from collections.abc import AsyncIterable
from typing import Any

import hiredis
from aiomonitor.task import preserve_termination_log
from aiotools.taskgroup import PersistentTaskGroup
from aiotools.taskgroup.types import AsyncExceptionHandler

from . import msgpack
from .events import AbstractEvent, EventHandler, _generate_consumer_id
from .events import EventDispatcher as _EventDispatcher
from .logging import BraceStyleAdapter
from .redis_client import RedisClient, RedisConnection
from .types import AgentId, EtcdRedisConfig

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

__all__ = ("EventDispatcher",)


async def read_stream(
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


async def read_stream_by_group(
    client: RedisClient,
    stream_key: str,
    group_name: str,
    consumer_id: str,
    *,
    autoclaim_idle_timeout: int = 1_000,  # in msec
    block_timeout: int = 10_000,  # in msec
) -> AsyncIterable[tuple[bytes, dict[bytes, bytes]]]:
    """
    A high-level wrapper for the XREADGROUP command
    combined with XAUTOCLAIM and XGROUP_CREATE.
    """
    while True:
        try:
            messages = []
            autoclaim_start_id = b"0-0"
            while True:
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
                    continue

                for msg_id, msg_data_list in reply[1]:
                    msg_data = {}
                    for idx in range(0, len(msg_data_list), 2):
                        msg_data[msg_data_list[idx]] = msg_data_list[idx + 1]
                    messages.append((msg_id, msg_data))
                if reply[0] == b"0-0":
                    break
                autoclaim_start_id = reply[0]
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


class EventDispatcher(_EventDispatcher):
    redis_config: EtcdRedisConfig
    db: int
    consumers: defaultdict[str, set[EventHandler[Any, AbstractEvent]]]
    subscribers: defaultdict[str, set[EventHandler[Any, AbstractEvent]]]

    def __init__(
        self,
        redis_config: EtcdRedisConfig,
        db: int = 0,
        log_events: bool = False,
        *,
        consumer_group: str,
        service_name: str | None = None,
        stream_key: str = "events",
        node_id: str | None = None,
        consumer_exception_handler: AsyncExceptionHandler | None = None,
        subscriber_exception_handler: AsyncExceptionHandler | None = None,
    ) -> None:
        _redis_config = redis_config.copy()
        if service_name:
            _redis_config["service_name"] = service_name
        self.redis_config = redis_config.copy()
        self._log_events = True
        self.db = db
        self._closed = False
        self.consumers = defaultdict(set)
        self.subscribers = defaultdict(set)
        self._stream_key = stream_key
        self._consumer_group = consumer_group
        self._consumer_name = _generate_consumer_id(node_id)
        self.consumer_taskgroup = PersistentTaskGroup(
            name="consumer_taskgroup",
            exception_handler=consumer_exception_handler,
        )
        self.subscriber_taskgroup = PersistentTaskGroup(
            name="subscriber_taskgroup",
            exception_handler=subscriber_exception_handler,
        )

        self._log_events = log_events
        self.reconnect_poll_interval = 0.3

    def show_retry_warning(
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
                "Retrying due to interruption of Redis connection " "({}, retrying-for: {:.3f}s)",
                repr(e),
                now - first_trial,
            )
            retry_log_count += 1
            last_log_time = now

    @preserve_termination_log
    async def _subscribe_loop(self) -> None:
        first_trial = time.perf_counter()
        retry_log_count = 0
        last_log_time = first_trial

        while True:
            try:
                async with RedisConnection(self.redis_config, db=self.db) as client:
                    async for msg_id, msg_data in read_stream(
                        client,
                        self._stream_key,
                    ):
                        if self._closed:
                            return
                        if msg_data is None:
                            continue
                        try:
                            await self.dispatch_subscribers(
                                msg_data[b"name"].decode(),
                                AgentId(msg_data[b"source"].decode()),
                                msgpack.unpackb(msg_data[b"args"]),
                            )
                        except asyncio.CancelledError:
                            raise
            except hiredis.HiredisError as e:
                if "READONLY" in e.args[0]:
                    self.show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                    if self.reconnect_poll_interval:
                        await asyncio.sleep(self.reconnect_poll_interval)
                    continue
                elif "NOREPLICAS" in e.args[0]:
                    self.show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                    if self.reconnect_poll_interval:
                        await asyncio.sleep(self.reconnect_poll_interval)
                    continue
                else:
                    raise
            except asyncio.TimeoutError as e:
                self.show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                if self.reconnect_poll_interval:
                    await asyncio.sleep(self.reconnect_poll_interval)
                continue
            except (ConnectionError, EOFError) as e:
                self.show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                if self.reconnect_poll_interval:
                    await asyncio.sleep(self.reconnect_poll_interval)
                continue
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("EventDispatcher.subscribe(): unexpected-error")
                raise

    @preserve_termination_log
    async def _consume_loop(self) -> None:
        first_trial = time.perf_counter()
        retry_log_count = 0
        last_log_time = first_trial

        while True:
            try:
                async with RedisConnection(self.redis_config, db=self.db) as client:
                    async for msg_id, msg_data in read_stream_by_group(
                        client,
                        self._stream_key,
                        self._consumer_group,
                        self._consumer_name,
                    ):
                        if self._closed:
                            return
                        if msg_data is None:
                            continue
                        try:
                            await self.dispatch_consumers(
                                msg_data[b"name"].decode(),
                                AgentId(msg_data[b"source"].decode()),
                                msgpack.unpackb(msg_data[b"args"]),
                            )
                        except asyncio.CancelledError:
                            raise
            except hiredis.HiredisError as e:
                if "READONLY" in e.args[0]:
                    self.show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                    if self.reconnect_poll_interval:
                        await asyncio.sleep(self.reconnect_poll_interval)
                    continue
                elif "NOREPLICAS" in e.args[0]:
                    self.show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                    if self.reconnect_poll_interval:
                        await asyncio.sleep(self.reconnect_poll_interval)
                    continue
                else:
                    raise
            except asyncio.TimeoutError as e:
                self.show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                if self.reconnect_poll_interval:
                    await asyncio.sleep(self.reconnect_poll_interval)
                continue
            except (ConnectionError, EOFError) as e:
                self.show_retry_warning(e, first_trial, retry_log_count, last_log_time)
                if self.reconnect_poll_interval:
                    await asyncio.sleep(self.reconnect_poll_interval)
                continue
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("EventDispatcher.consume(): unexpected-error")
                raise

    async def close(self) -> None:
        self._closed = True
