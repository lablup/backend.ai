from __future__ import annotations

import asyncio
import inspect
import logging
import socket
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import aioredis
import aioredis.client
import aioredis.sentinel
import aioredis.exceptions
import yarl

from .logging import BraceStyleAdapter
from .types import EtcdRedisConfig, RedisConnectionInfo
from .validators import DelimiterSeperatedList, HostPortPair

__all__ = (
    'execute',
    'subscribe',
    'blpop',
    'read_stream',
    'read_stream_by_group',
    'get_redis_object',
)

_keepalive_options: MutableMapping[int, int] = {}

# macOS does not support several TCP_ options
# so check if socket package includes TCP options before adding it
if hasattr(socket, 'TCP_KEEPIDLE'):
    _keepalive_options[socket.TCP_KEEPIDLE] = 20

if hasattr(socket, 'TCP_KEEPINTVL'):
    _keepalive_options[socket.TCP_KEEPINTVL] = 5

if hasattr(socket, 'TCP_KEEPCNT'):
    _keepalive_options[socket.TCP_KEEPCNT] = 3


_default_conn_opts: Mapping[str, Any] = {
    'socket_timeout': 3.0,
    'socket_connect_timeout': 0.3,
    'socket_keepalive': True,
    'socket_keepalive_options': _keepalive_options,
}


_scripts: Dict[str, str] = {}

log = BraceStyleAdapter(logging.getLogger(__name__))


class ConnectionNotAvailable(Exception):
    pass


def _calc_delay_exp_backoff(initial_delay: float, retry_count: float, time_limit: float) -> float:
    if time_limit > 0:
        return min(initial_delay * (2 ** retry_count), time_limit / 2)
    return min(initial_delay * (2 ** retry_count), 30.0)


def _parse_stream_msg_id(msg_id: bytes) -> Tuple[int, int]:
    timestamp, _, sequence = msg_id.partition(b'-')
    return int(timestamp), int(sequence)


async def subscribe(
    channel: aioredis.client.PubSub,
    *,
    reconnect_poll_interval: float = 0.3,
) -> AsyncIterator[Any]:
    """
    An async-generator wrapper for pub-sub channel subscription.
    It automatically recovers from server shutdowns until explicitly cancelled.
    """
    async def _reset_chan():
        channel.connection = None
        try:
            await channel.ping()
        except aioredis.exceptions.ConnectionError:
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
            aioredis.exceptions.ConnectionError,
            aioredis.sentinel.MasterNotFoundError,
            aioredis.sentinel.SlaveNotFoundError,
            aioredis.exceptions.ReadOnlyError,
            aioredis.exceptions.ResponseError,
            ConnectionResetError,
            ConnectionNotAvailable,
        ):
            await asyncio.sleep(reconnect_poll_interval)
            await _reset_chan()
            continue
        except aioredis.exceptions.ResponseError as e:
            if e.args[0].startswith("NOREPLICAS "):
                await asyncio.sleep(reconnect_poll_interval)
                await _reset_chan()
                continue
            raise
        except (TimeoutError, asyncio.TimeoutError):
            continue
        except asyncio.CancelledError:
            raise
        finally:
            await asyncio.sleep(0)


async def blpop(
    redis: RedisConnectionInfo | aioredis.Redis | aioredis.sentinel.Sentinel,
    key: str,
    *,
    service_name: str = None,
    reconnect_poll_interval: float = 0.3,
) -> AsyncIterator[Any]:
    """
    An async-generator wrapper for blpop (blocking left pop).
    It automatically recovers from server shutdowns until explicitly cancelled.
    """
    _conn_opts = {
        **_default_conn_opts,
        'socket_connect_timeout': reconnect_poll_interval,
    }
    if isinstance(redis, RedisConnectionInfo):
        redis_client = redis.client
        service_name = service_name or redis.service_name
    else:
        redis_client = redis

    if isinstance(redis_client, aioredis.sentinel.Sentinel):
        assert service_name is not None
        r = redis_client.master_for(
            service_name,
            redis_class=aioredis.Redis,
            connection_pool_class=aioredis.sentinel.SentinelConnectionPool,
            **_conn_opts,
        )
    else:
        r = redis_client
    while True:
        try:
            raw_msg = await r.blpop(key, timeout=10.0)
            if not raw_msg:
                continue
            yield raw_msg[1]
        except (
            aioredis.exceptions.ConnectionError,
            aioredis.sentinel.MasterNotFoundError,
            aioredis.exceptions.ReadOnlyError,
            aioredis.exceptions.ResponseError,
            ConnectionResetError,
        ):
            await asyncio.sleep(reconnect_poll_interval)
            continue
        except aioredis.exceptions.ResponseError as e:
            if e.args[0].startswith("NOREPLICAS "):
                await asyncio.sleep(reconnect_poll_interval)
                continue
            raise
        except (TimeoutError, asyncio.TimeoutError):
            continue
        except asyncio.CancelledError:
            raise
        finally:
            await asyncio.sleep(0)


async def execute(
    redis: RedisConnectionInfo | aioredis.Redis | aioredis.sentinel.Sentinel,
    func: Callable[[aioredis.Redis], Awaitable[Any]],
    *,
    service_name: str = None,
    read_only: bool = False,
    reconnect_poll_interval: float = 0.3,
    encoding: Optional[str] = None,
) -> Any:
    """
    Executes a function that issues Redis commands or returns a pipeline/transaction of commands,
    with automatic retries upon temporary connection failures.

    Note that when retried, the given function may be executed *multiple* times, so the caller
    should take care of side-effects of it.
    """
    _conn_opts = {
        **_default_conn_opts,
        'socket_connect_timeout': reconnect_poll_interval,
    }
    if isinstance(redis, RedisConnectionInfo):
        redis_client = redis.client
        service_name = service_name or redis.service_name
    else:
        redis_client = redis

    if isinstance(redis_client, aioredis.sentinel.Sentinel):
        assert service_name is not None
        if read_only:
            r = redis_client.slave_for(
                service_name,
                redis_class=aioredis.Redis,
                connection_pool_class=aioredis.sentinel.SentinelConnectionPool,
                **_conn_opts,
            )
        else:
            r = redis_client.master_for(
                service_name,
                redis_class=aioredis.Redis,
                connection_pool_class=aioredis.sentinel.SentinelConnectionPool,
                **_conn_opts,
            )
    else:
        r = redis_client
    while True:
        try:
            async with r:
                if callable(func):
                    aw_or_pipe = func(r)
                else:
                    raise TypeError('The func must be a function or a coroutinefunction '
                                    'with no arguments.')
                if isinstance(aw_or_pipe, aioredis.client.Pipeline):
                    result = await aw_or_pipe.execute()
                elif inspect.isawaitable(aw_or_pipe):
                    result = await aw_or_pipe
                else:
                    raise TypeError('The return value must be an awaitable'
                                    'or aioredis.commands.Pipeline object')
                if isinstance(result, aioredis.client.Pipeline):
                    # This happens when func is an async function that returns a pipeline.
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
            aioredis.sentinel.MasterNotFoundError,
            aioredis.sentinel.SlaveNotFoundError,
            aioredis.exceptions.ReadOnlyError,
            ConnectionResetError,
        ):
            await asyncio.sleep(reconnect_poll_interval)
            continue
        except aioredis.exceptions.ConnectionError as e:
            log.exception(f'execute(): Connecting to redis failed: {e}')
            await asyncio.sleep(reconnect_poll_interval)
            continue
        except aioredis.exceptions.ResponseError as e:
            if "NOREPLICAS" in e.args[0]:
                await asyncio.sleep(reconnect_poll_interval)
                continue
            raise
        except (TimeoutError, asyncio.TimeoutError):
            continue
        except asyncio.CancelledError:
            raise
        finally:
            await asyncio.sleep(0)


async def execute_script(
    redis: RedisConnectionInfo | aioredis.Redis | aioredis.sentinel.Sentinel,
    script_id: str,
    script: str,
    keys: Sequence[str],
    args: Sequence[Union[bytes, memoryview, str, int, float]],  # aioredis.connection.EncodableT
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
    script_hash = _scripts.get(script_id, 'x')
    while True:
        try:
            ret = await execute(redis, lambda r: r.evalsha(
                script_hash,
                len(keys),
                *keys, *args,
            ))
            break
        except aioredis.exceptions.NoScriptError:
            # Redis may have been restarted.
            script_hash = await execute(redis, lambda r: r.script_load(script))
            _scripts[script_id] = script_hash
        except aioredis.exceptions.ResponseError as e:
            if 'NOSCRIPT' in e.args[0]:
                # Redis may have been restarted.
                script_hash = await execute(redis, lambda r: r.script_load(script))
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
) -> AsyncIterator[Tuple[bytes, bytes]]:
    """
    A high-level wrapper for the XREAD command.
    """
    last_id = b'$'
    while True:
        try:
            reply = await execute(
                r,
                lambda r: r.xread(
                    {stream_key: last_id},
                    block=block_timeout,
                ),
            )
            if reply is None:
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
) -> AsyncIterator[Tuple[bytes, bytes]]:
    """
    A high-level wrapper for the XREADGROUP command
    combined with XAUTOCLAIM and XGROUP_CREATE.
    """
    while True:
        try:
            messages = []
            autoclaim_start_id = b'0-0'
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
                )
                for msg_id, msg_data in aioredis.client.parse_stream_list(reply[1]):
                    messages.append((msg_id, msg_data))
                if reply[0] == b'0-0':
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
        except aioredis.exceptions.ResponseError as e:
            if e.args[0].startswith("NOGROUP "):
                try:
                    await execute(
                        r,
                        lambda r: r.xgroup_create(
                            stream_key,
                            group_name,
                            b"$",
                            mkstream=True,
                        ),
                    )
                except aioredis.exceptions.ResponseError as e:
                    if e.args[0].startswith("BUSYGROUP "):
                        pass
                    else:
                        raise
                continue
            raise


def get_redis_object(
    redis_config: EtcdRedisConfig,
    db: int = 0,
    **kwargs,
) -> RedisConnectionInfo:
    if _sentinel_addresses := redis_config.get('sentinel'):
        sentinel_addresses: Any = None
        if isinstance(_sentinel_addresses, str):
            sentinel_addresses = DelimiterSeperatedList(HostPortPair).check_and_return(_sentinel_addresses)
        else:
            sentinel_addresses = _sentinel_addresses

        assert redis_config.get('service_name') is not None
        sentinel = aioredis.sentinel.Sentinel(
            [(str(host), port) for host, port in sentinel_addresses],
            password=redis_config.get('password'),
            db=str(db),
            sentinel_kwargs={
                **kwargs,
            },
        )
        return RedisConnectionInfo(
            client=sentinel,
            service_name=redis_config.get('service_name'),
        )
    else:
        redis_url = redis_config.get('addr')
        assert redis_url is not None
        url = (
            yarl.URL('redis://host')
            .with_host(str(redis_url[0]))
            .with_port(redis_url[1])
            .with_password(redis_config.get('password')) / str(db)
        )
        return RedisConnectionInfo(
            client=aioredis.Redis.from_url(str(url), **kwargs),
            service_name=None,
        )


async def ping_redis_connection(client: aioredis.client.Redis):
    try:
        _ = await client.time()
    except aioredis.exceptions.ConnectionError as e:
        log.exception(f'ping_redis_connection(): Connecting to redis failed: {e}')
        raise e
