from __future__ import annotations

import asyncio
import inspect
import logging
import time
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Optional,
)

import redis.exceptions
from redis import Connection
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline
from redis.asyncio.sentinel import MasterNotFoundError, SlaveNotFoundError

from ai.backend.common.message_queue.base import AbstractMessageQueue, MQMessage
from ai.backend.common.types import RedisConnectionInfo
from ai.backend.logging import BraceStyleAdapter


class RedisMessageQueue(AbstractMessageQueue):
    def __init__(self, redis_connection_info: RedisConnectionInfo):
        self.connection_info = redis_connection_info
        self._log = BraceStyleAdapter(logging.getLogger(__spec__.name))
        self.connection: Optional[Connection] = None

    async def receive(
        self,
        stream_key: str,
        *,
        block_timeout: int = 10_000,  # in msec
    ) -> AsyncGenerator[MQMessage, None]:
        """
        A high-level wrapper for the XREAD command.
        """

        async def generator():
            last_id = b"$"
            while True:
                try:
                    reply = await self._execute(
                        self.connection_info,
                        lambda r: r.xread(
                            {stream_key: last_id},
                            block=block_timeout,
                        ),
                        command_timeout=block_timeout / 1000,
                    )
                    if not reply:
                        continue
                    # Keep some latest messages so that other manager
                    # processes to have chances of fetching them.
                    await self._execute(
                        self.connection_info,
                        lambda r: r.xtrim(
                            stream_key,
                            maxlen=128,
                            approximate=True,
                        ),
                    )
                    for msg_id, msg_data in reply[0][1]:
                        try:
                            message = MQMessage(
                                topic=stream_key,
                                payload=msg_data,
                                metadata={
                                    "message_id": msg_id.decode()
                                },  # store msg_id in metadata
                            )
                            yield message
                        finally:
                            last_id = msg_id
                except asyncio.CancelledError:
                    raise

        return generator()

    async def receive_group(
        self,
        stream_key: str,
        group_name: str,
        consumer_id: str,
        *,
        autoclaim_idle_timeout: int = 1_000,  # in msec
        block_timeout: int = 10_000,  # in msec
    ) -> AsyncGenerator[MQMessage, None]:
        async def generator():
            while True:
                try:
                    messages = []
                    autoclaim_start_id = b"0-0"
                    while True:
                        reply = await self._execute(
                            self.connection_info,
                            lambda r: r.execute_command(
                                "XAUTOCLAIM",
                                stream_key,
                                group_name,
                                consumer_id,
                                str(autoclaim_idle_timeout),
                                autoclaim_start_id,
                            ),
                            command_timeout=autoclaim_idle_timeout / 1000,
                        )
                        for msg_id, msg_data in reply[1]:
                            messages.append((msg_id, msg_data))
                        if reply[0] == b"0-0":
                            break
                        autoclaim_start_id = reply[0]
                    reply = await self._execute(
                        self.connection_info,
                        lambda r: r.xreadgroup(
                            group_name,
                            consumer_id,
                            {stream_key: b">"},  # fetch messages not seen by other consumers
                            block=block_timeout,
                        ),
                        command_timeout=block_timeout / 1000,
                    )
                    if len(reply) == 0:
                        continue
                    assert reply[0][0].decode() == stream_key
                    for msg_id, msg_data in reply[0][1]:
                        messages.append((msg_id, msg_data))
                    await self._execute(
                        self.connection_info,
                        lambda r: r.xack(
                            stream_key,
                            group_name,
                            *(msg_id for msg_id, msg_data in reply[0][1]),
                        ),
                    )
                    for msg_id, msg_data in messages:
                        message = MQMessage(
                            topic=stream_key,
                            payload=msg_data,
                            metadata={"message_id": msg_id.decode()},  # store msg_id in metadata
                        )
                        yield message
                except asyncio.CancelledError:
                    raise
                except redis.exceptions.ResponseError as e:
                    if e.args[0].startswith("NOGROUP "):
                        try:
                            await self._execute(
                                self.connection_info,
                                lambda r: r.xgroup_create(
                                    stream_key,
                                    group_name,
                                    "$",
                                    mkstream=True,
                                ),
                            )
                        except redis.exceptions.ResponseError as e:
                            if e.args[0].startswith("BUSYGROUP "):
                                pass
                            else:
                                raise
                        continue
                    raise

        return generator()

    async def _execute(
        self,
        redis_obj: RedisConnectionInfo,
        func: Callable[[Redis], Awaitable[Any]],
        *,
        service_name: Optional[str] = None,
        encoding: Optional[str] = None,
        command_timeout: Optional[float] = None,
    ) -> Any:
        """
        Executes a function that issues Redis commands or returns a pipeline/transaction of commands,
        with automatic retries upon temporary connection failures.

        Note that when retried, the given function may be executed *multiple* times, so the caller
        should take care of side-effects of it.
        """
        redis_client = redis_obj.client
        service_name = service_name or redis_obj.service_name
        reconnect_poll_interval = redis_obj.redis_helper_config.get("reconnect_poll_timeout", 0.0)

        first_trial = time.perf_counter()
        retry_log_count = 0
        last_log_time = first_trial

        def show_retry_warning(e: Exception, warn_on_first_attempt: bool = True) -> None:
            nonlocal retry_log_count, last_log_time
            now = time.perf_counter()
            if (warn_on_first_attempt and retry_log_count == 0) or now - last_log_time >= 10.0:
                self._log.warning(
                    "Retrying due to interruption of Redis connection "
                    "({}, conn-pool: {}, retrying-for: {:.3f}s)",
                    repr(e),
                    redis_obj.name,
                    now - first_trial,
                )
                retry_log_count += 1
                last_log_time = now

        while True:
            try:
                async with redis_client:
                    if callable(func):
                        aw_or_pipe = func(redis_client)
                    else:
                        raise TypeError(
                            "The func must be a function or a coroutinefunction with no arguments."
                        )
                    if isinstance(aw_or_pipe, Pipeline):
                        async with aw_or_pipe:
                            result = await aw_or_pipe.execute()
                    elif inspect.isawaitable(aw_or_pipe):
                        result = await aw_or_pipe
                    else:
                        raise TypeError(
                            "The return value must be an awaitable"
                            "or redis.asyncio.client.Pipeline object"
                        )
                    if isinstance(result, Pipeline):
                        # This happens when func is an async function that returns a pipeline.
                        async with result:
                            result = await result.execute()
                    if encoding:
                        if isinstance(result, bytes):
                            return result.decode(encoding)
                        elif isinstance(result, dict):
                            newdict = {}
                            for k, v in result.items():
                                newdict[k.decode(encoding)] = v.decode(encoding)
                            return newdict
                    else:
                        return result
            except (
                MasterNotFoundError,
                SlaveNotFoundError,
                redis.exceptions.ReadOnlyError,
                redis.exceptions.ConnectionError,
                ConnectionResetError,
            ) as e:
                warn_on_first_attempt = True
                if (
                    isinstance(e, redis.exceptions.ConnectionError)
                    and "Too many connections" in e.args[0]
                ):  # connection pool is full
                    warn_on_first_attempt = False
                show_retry_warning(e, warn_on_first_attempt)
                await asyncio.sleep(reconnect_poll_interval)
                continue
            except (
                redis.exceptions.TimeoutError,
                asyncio.TimeoutError,
            ) as e:
                if command_timeout is not None:
                    now = time.perf_counter()
                    if now - first_trial >= command_timeout + 1.0:
                        show_retry_warning(e)
                    first_trial = now
                continue
            except redis.exceptions.ResponseError as e:
                if "NOREPLICAS" in e.args[0]:
                    show_retry_warning(e)
                    await asyncio.sleep(reconnect_poll_interval)
                    continue
                raise
            except asyncio.CancelledError:
                raise
            finally:
                await asyncio.sleep(0)

    async def send(
        self,
        msg: MQMessage,
        *,
        is_flush: bool = False,
        service_name: Optional[str] = None,
        encoding: Optional[str] = None,
        command_timeout: Optional[float] = None,
    ) -> Any:
        if is_flush:
            func = (lambda r: r.flushdb(),)
        else:
            func = (lambda r: r.xadd(self._stream_key, msg.payload),)  # type: ignore # aio-libs/aioredis-py#1182

        redis_client = self.connection_info.client
        service_name = service_name or self.connection_info.service_name
        reconnect_poll_interval = self.connection_info.redis_helper_config.get(
            "reconnect_poll_timeout", 0.0
        )

        first_trial = time.perf_counter()
        retry_log_count = 0
        last_log_time = first_trial

        def show_retry_warning(e: Exception, warn_on_first_attempt: bool = True) -> None:
            nonlocal retry_log_count, last_log_time
            now = time.perf_counter()
            if (warn_on_first_attempt and retry_log_count == 0) or now - last_log_time >= 10.0:
                self._log.warning(
                    "Retrying due to interruption of Redis connection "
                    "({}, conn-pool: {}, retrying-for: {:.3f}s)",
                    repr(e),
                    self.connection_info.name,
                    now - first_trial,
                )
                retry_log_count += 1
                last_log_time = now

        while True:
            try:
                async with redis_client:
                    if callable(func):
                        aw_or_pipe = func(redis_client)
                    else:
                        raise TypeError(
                            "The func must be a function or a coroutinefunction with no arguments."
                        )
                    if isinstance(aw_or_pipe, Pipeline):
                        async with aw_or_pipe:
                            result = await aw_or_pipe.execute()
                    elif inspect.isawaitable(aw_or_pipe):
                        result = await aw_or_pipe
                    else:
                        raise TypeError(
                            "The return value must be an awaitable"
                            "or redis.asyncio.client.Pipeline object"
                        )
                    if isinstance(result, Pipeline):
                        # This happens when func is an async function that returns a pipeline.
                        async with result:
                            result = await result.execute()
                    if encoding:
                        if isinstance(result, bytes):
                            return result.decode(encoding)
                        elif isinstance(result, dict):
                            newdict = {}
                            for k, v in result.items():
                                newdict[k.decode(encoding)] = v.decode(encoding)
                            return newdict
                    else:
                        return result
            except (
                MasterNotFoundError,
                SlaveNotFoundError,
                redis.exceptions.ReadOnlyError,
                redis.exceptions.ConnectionError,
                ConnectionResetError,
            ) as e:
                warn_on_first_attempt = True
                if (
                    isinstance(e, redis.exceptions.ConnectionError)
                    and "Too many connections" in e.args[0]
                ):  # connection pool is full
                    warn_on_first_attempt = False
                show_retry_warning(e, warn_on_first_attempt)
                await asyncio.sleep(reconnect_poll_interval)
                continue
            except (
                redis.exceptions.TimeoutError,
                asyncio.TimeoutError,
            ) as e:
                if command_timeout is not None:
                    now = time.perf_counter()
                    if now - first_trial >= command_timeout + 1.0:
                        show_retry_warning(e)
                    first_trial = now
                continue
            except redis.exceptions.ResponseError as e:
                if "NOREPLICAS" in e.args[0]:
                    show_retry_warning(e)
                    await asyncio.sleep(reconnect_poll_interval)
                    continue
                raise
            except asyncio.CancelledError:
                raise
            finally:
                await asyncio.sleep(0)

    async def close(self, close_connection_pool: Optional[bool] = None) -> None:
        conn = self.connection
        if conn:
            self.connection = None
            await self.connection_info.client.connection_pool.release(conn)
        if close_connection_pool or (
            close_connection_pool is None and self.connection_info.client.auto_close_connection_pool
        ):
            await self.connection_info.client.connection_pool.disconnect()
