from __future__ import annotations

import asyncio
import inspect
import logging
import socket
import time
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Union,
    cast,
)

import redis.exceptions
import yarl
from redis.asyncio import ConnectionPool, Redis
from redis.asyncio.client import Pipeline, PubSub
from redis.asyncio.sentinel import MasterNotFoundError, Sentinel, SlaveNotFoundError
from redis.backoff import ExponentialBackoff
from redis.retry import Retry

from .logging import BraceStyleAdapter
from .types import EtcdRedisConfig, RedisConnectionInfo, RedisHelperConfig
from .validators import DelimiterSeperatedList, HostPortPair

__all__ = (
    "execute",
    "subscribe",
    "blpop",
    "read_stream",
    "read_stream_by_group",
    "get_redis_object",
)

_keepalive_options: MutableMapping[int, int] = {}

# macOS does not support several TCP_ options
# so check if socket package includes TCP options before adding it
if (_TCP_KEEPIDLE := getattr(socket, "TCP_KEEPIDLE", None)) is not None:
    _keepalive_options[_TCP_KEEPIDLE] = 20

if (_TCP_KEEPINTVL := getattr(socket, "TCP_KEEPINTVL", None)) is not None:
    _keepalive_options[_TCP_KEEPINTVL] = 5

if (_TCP_KEEPCNT := getattr(socket, "TCP_KEEPCNT", None)) is not None:
    _keepalive_options[_TCP_KEEPCNT] = 3


_default_conn_opts: Mapping[str, Any] = {
    "socket_keepalive": True,
    "socket_keepalive_options": _keepalive_options,
    "retry": Retry(ExponentialBackoff(), 10),
    "retry_on_error": [
        redis.exceptions.ConnectionError,
        redis.exceptions.TimeoutError,
    ],
}
_default_conn_pool_opts: Mapping[str, Any] = {
    "max_connections": 16,
    # "timeout": 20.0,  # for redis-py 5.0+
}

_scripts: dict[str, str] = {}

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class ConnectionNotAvailable(Exception):
    pass


async def subscribe(
    channel: PubSub,
    *,
    reconnect_poll_interval: float = 0.3,
) -> AsyncGenerator[Any, None]:
    """
    An async-generator wrapper for pub-sub channel subscription.
    It automatically recovers from server shutdowns until explicitly cancelled.
    """

    async def _reset_chan():
        channel.connection = None
        try:
            await channel.ping()
        except redis.exceptions.ConnectionError:
            pass
        else:
            assert channel.connection is not None
            await channel.on_connect(channel.connection)

    while True:
        try:
            if not channel.connection:
                raise ConnectionNotAvailable
            message = await channel.get_message(ignore_subscribe_messages=True, timeout=10.0)
            if message is not None:
                yield message["data"]
        except (
            MasterNotFoundError,
            SlaveNotFoundError,
            redis.exceptions.ConnectionError,
            redis.exceptions.ReadOnlyError,
            ConnectionResetError,
            ConnectionNotAvailable,
        ):
            await asyncio.sleep(reconnect_poll_interval)
            await _reset_chan()
            continue
        except redis.exceptions.ResponseError as e:
            if len(e.args) > 0 and e.args[0].upper().startswith("NOREPLICAS "):
                await asyncio.sleep(reconnect_poll_interval)
                await _reset_chan()
                continue
            raise
        except (redis.exceptions.TimeoutError, asyncio.TimeoutError):
            continue
        except asyncio.CancelledError:
            raise
        finally:
            await asyncio.sleep(0)


async def blpop(
    redis_obj: RedisConnectionInfo,
    key: str,
    *,
    service_name: Optional[str] = None,
) -> AsyncGenerator[bytes, None]:
    """
    An async-generator wrapper for blpop (blocking left pop).
    It automatically recovers from server shutdowns until explicitly cancelled.
    """

    redis_client = redis_obj.client
    service_name = service_name or redis_obj.service_name
    reconnect_poll_interval = float(
        cast(str, redis_obj.redis_helper_config.get("reconnect_poll_timeout"))
    )

    while True:
        try:
            raw_msg = await redis_client.blpop(key, timeout=10.0)
            if not raw_msg:
                continue
            yield raw_msg[1]
        except (
            MasterNotFoundError,
            SlaveNotFoundError,
            redis.exceptions.ConnectionError,
            redis.exceptions.ReadOnlyError,
            ConnectionResetError,
        ):
            await asyncio.sleep(reconnect_poll_interval)
            continue
        except redis.exceptions.ResponseError as e:
            if e.args[0].upper().startswith("NOREPLICAS "):
                await asyncio.sleep(reconnect_poll_interval)
                continue
            raise
        except (redis.exceptions.TimeoutError, asyncio.TimeoutError):
            continue
        except asyncio.CancelledError:
            raise
        finally:
            await asyncio.sleep(0)


async def execute(
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
            log.warning(
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


async def execute_script(
    redis_obj: RedisConnectionInfo,
    script_id: str,
    script: str,
    keys: Sequence[str],
    args: Sequence[
        Union[bytes, memoryview, str, int, float]
    ],  # redis.asyncio.connection.EncodableT
) -> Any:
    """
    Auto-load and execute the given script.
    It uses the hash keys for scripts so that it does not send the whole
    script every time but only at the first time.

    Args:
        conn: A Redis connection or pool with the commands mixin.
        script_id: A human-readable identifier for the script.
            This can be arbitrary string but must be unique for each script.
        script: The script content.
        keys: The Redis keys that will be passed to the script.
        args: The arguments that will be passed to the script.
    """
    script_hash = _scripts.get(script_id, "x")
    while True:
        try:
            ret = await execute(
                redis_obj,
                lambda r: r.evalsha(
                    script_hash,
                    len(keys),
                    *keys,
                    *args,
                ),
            )
            break
        except redis.exceptions.NoScriptError:
            # Redis may have been restarted.
            script_hash = await execute(redis_obj, lambda r: r.script_load(script))
            _scripts[script_id] = script_hash
        except redis.exceptions.ResponseError as e:
            if "NOSCRIPT" in e.args[0]:
                # Redis may have been restarted.
                script_hash = await execute(redis_obj, lambda r: r.script_load(script))
                _scripts[script_id] = script_hash
            else:
                raise
            continue
    return ret


async def read_stream(
    r: RedisConnectionInfo,
    stream_key: str,
    *,
    block_timeout: int = 10_000,  # in msec
) -> AsyncGenerator[tuple[bytes, bytes], None]:
    """
    A high-level wrapper for the XREAD command.
    """
    last_id = b"$"
    while True:
        try:
            reply = await execute(
                r,
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
            await execute(
                r,
                lambda r: r.xtrim(
                    stream_key,
                    maxlen=128,
                    approximate=True,
                ),
            )
            for msg_id, msg_data in reply[0][1]:
                try:
                    yield msg_id, msg_data
                finally:
                    last_id = msg_id
        except asyncio.CancelledError:
            raise


async def read_stream_by_group(
    r: RedisConnectionInfo,
    stream_key: str,
    group_name: str,
    consumer_id: str,
    *,
    autoclaim_idle_timeout: int = 1_000,  # in msec
    block_timeout: int = 10_000,  # in msec
) -> AsyncGenerator[tuple[bytes, Any], None]:
    """
    A high-level wrapper for the XREADGROUP command
    combined with XAUTOCLAIM and XGROUP_CREATE.
    """
    while True:
        try:
            messages = []
            autoclaim_start_id = b"0-0"
            while True:
                reply = await execute(
                    r,
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
            reply = await execute(
                r,
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
            await execute(
                r,
                lambda r: r.xack(
                    stream_key,
                    group_name,
                    *(msg_id for msg_id, msg_data in reply[0][1]),
                ),
            )
            for msg_id, msg_data in messages:
                yield msg_id, msg_data
        except asyncio.CancelledError:
            raise
        except redis.exceptions.ResponseError as e:
            if e.args[0].startswith("NOGROUP "):
                try:
                    await execute(
                        r,
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


def get_redis_object(
    redis_config: EtcdRedisConfig,
    *,
    name: str,
    db: int = 0,
    **kwargs,
) -> RedisConnectionInfo:
    redis_helper_config: RedisHelperConfig = cast(
        RedisHelperConfig, redis_config.get("redis_helper_config")
    )
    conn_opts = {
        **_default_conn_opts,
        **kwargs,
        # "lib_name": None,  # disable implicit "CLIENT SETINFO" (for redis-py 5.0+)
        # "lib_version": None,  # disable implicit "CLIENT SETINFO" (for redis-py 5.0+)
    }
    conn_pool_opts = {
        **_default_conn_pool_opts,
    }
    if socket_timeout := redis_helper_config.get("socket_timeout"):
        conn_opts["socket_timeout"] = float(socket_timeout)
    if socket_connect_timeout := redis_helper_config.get("socket_connect_timeout"):
        conn_opts["socket_connect_timeout"] = float(socket_connect_timeout)
    if max_connections := redis_helper_config.get("max_connections"):
        conn_pool_opts["max_connections"] = int(max_connections)
    # for redis-py 5.0+
    # if connection_ready_timeout := redis_helper_config.get("connection_ready_timeout"):
    #     conn_pool_opts["timeout"] = float(connection_ready_timeout)
    if _sentinel_addresses := redis_config.get("sentinel"):
        sentinel_addresses: Any = None
        if isinstance(_sentinel_addresses, str):
            sentinel_addresses = DelimiterSeperatedList(HostPortPair).check_and_return(
                _sentinel_addresses
            )
        else:
            sentinel_addresses = _sentinel_addresses

        service_name = redis_config.get("service_name")
        password = redis_config.get("password")
        assert (
            service_name is not None
        ), "config/redis/service_name is required when using Redis Sentinel"

        sentinel = Sentinel(
            [(str(host), port) for host, port in sentinel_addresses],
            password=password,
            db=str(db),
            sentinel_kwargs={
                "password": password,
                **kwargs,
            },
        )
        return RedisConnectionInfo(
            client=sentinel.master_for(
                service_name=service_name,
                password=password,
                **conn_opts,
            ),
            sentinel=sentinel,
            name=name,
            service_name=service_name,
            redis_helper_config=redis_helper_config,
        )
    else:
        redis_url = redis_config.get("addr")
        assert redis_url is not None
        url = yarl.URL("redis://host").with_host(str(redis_url[0])).with_port(
            redis_url[1]
        ).with_password(redis_config.get("password")) / str(db)
        return RedisConnectionInfo(
            # In redis-py 5.0.1+, we should migrate to `Redis.from_pool()` API
            client=Redis(
                connection_pool=ConnectionPool.from_url(
                    str(url),
                    **conn_pool_opts,
                ),
                **conn_opts,
                auto_close_connection_pool=True,
            ),
            sentinel=None,
            name=name,
            service_name=None,
            redis_helper_config=redis_helper_config,
        )


async def ping_redis_connection(redis_client: Redis) -> bool:
    try:
        return await redis_client.ping()
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        log.exception(f"ping_redis_connection(): Connecting to redis failed: {e}")
        raise e
