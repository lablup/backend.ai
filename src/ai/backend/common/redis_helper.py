from __future__ import annotations

import asyncio
import inspect
import logging
import socket
import time

# Import ValkeyStatClient with TYPE_CHECKING to avoid circular imports
from typing import (
    Any,
    Awaitable,
    Callable,
    Mapping,
    MutableMapping,
    Optional,
    Union,
    cast,
)

import redis.exceptions
import yarl
from glide import (
    AdvancedGlideClientConfiguration,
    GlideClient,
    GlideClientConfiguration,
    NodeAddress,
    ServerCredentials,
    TlsAdvancedConfiguration,
)
from redis.asyncio import ConnectionPool, Redis
from redis.asyncio.client import Pipeline
from redis.asyncio.sentinel import MasterNotFoundError, Sentinel, SlaveNotFoundError
from redis.backoff import ExponentialBackoff
from redis.retry import Retry

from ai.backend.common.utils import addr_to_hostport_pair
from ai.backend.logging import BraceStyleAdapter

from .types import RedisConnectionInfo, RedisHelperConfig, RedisTarget, ValkeyTarget
from .validators import DelimiterSeperatedList, HostPortPair

__all__ = (
    "execute",
    "get_redis_object",
)

_keepalive_options: MutableMapping[int, int] = {}


SSL_CERT_NONE = "none"
SSL_CERT_REQUIRED = "required"

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

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


# Leaving it as is since the CLI is still using redis-py version 4.x
async def execute(
    redis_obj: RedisConnectionInfo,
    func: Callable[[Union[Redis, Any]], Awaitable[Any]],
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

    if not callable(func):
        raise TypeError("The func must be a function or a coroutinefunction with no arguments.")

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
                aw_or_pipe = func(redis_client)
                if isinstance(aw_or_pipe, Pipeline):
                    async with aw_or_pipe:
                        result = await aw_or_pipe.execute()
                elif inspect.isawaitable(aw_or_pipe):
                    result = await aw_or_pipe
                else:
                    raise ValueError(
                        "The redis execute's return value must be an awaitable"
                        " or redis.asyncio.client.Pipeline object"
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
            TypeError,  # 4.5.5 version of redis.py raises a TypeError when the Connection is closed.
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


def _get_redis_url_schema(redis_target: RedisTarget) -> str:
    """
    Returns the Redis URL schema based on the Redis target configuration.
    """
    if redis_target.use_tls:
        return "rediss"
    return "redis"


def _parse_redis_url(redis_target: RedisTarget, db: int) -> yarl.URL:
    redis_url = redis_target.addr
    if redis_url is None:
        raise ValueError("Redis URL is not provided in the configuration.")

    schema = _get_redis_url_schema(redis_target)
    url = yarl.URL(f"{schema}://host").with_host(str(redis_url[0])).with_port(
        redis_url[1]
    ).with_password(redis_target.get("password")) / str(db)
    return url


def get_redis_object(
    redis_target: RedisTarget,
    *,
    name: str,
    db: int = 0,
    **kwargs,
) -> RedisConnectionInfo:
    redis_helper_config: RedisHelperConfig = cast(
        RedisHelperConfig, redis_target.redis_helper_config
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
    if _sentinel_addresses := redis_target.get("sentinel"):
        sentinel_addresses: Any = None
        if isinstance(_sentinel_addresses, str):
            sentinel_addresses = DelimiterSeperatedList(HostPortPair).check_and_return(
                _sentinel_addresses
            )
        else:
            sentinel_addresses = _sentinel_addresses

        service_name = redis_target.get("service_name")
        password = redis_target.get("password")
        assert service_name is not None, (
            "config/redis/service_name is required when using Redis Sentinel"
        )

        kwargs = {
            "password": password,
            "ssl": redis_target.use_tls,
            "ssl_cert_reqs": SSL_CERT_NONE if redis_target.tls_skip_verify else SSL_CERT_REQUIRED,
        }
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
        redis_url = redis_target.addr
        if redis_url is None:
            raise ValueError("Redis URL is not provided in the configuration.")

        url = _parse_redis_url(redis_target, db)
        return RedisConnectionInfo(
            # In redis-py 5.0.1+, we should migrate to `Redis.from_pool()` API
            client=Redis(
                connection_pool=ConnectionPool.from_url(
                    str(url),
                    **conn_pool_opts,
                    **conn_opts,
                ),
                **conn_opts,
                auto_close_connection_pool=True,
                ssl=redis_target.use_tls,
                ssl_cert_reqs=SSL_CERT_NONE if redis_target.tls_skip_verify else SSL_CERT_REQUIRED,
            ),
            sentinel=None,
            name=name,
            service_name=None,
            redis_helper_config=redis_helper_config,
        )


async def create_valkey_client(
    valkey_target: ValkeyTarget,
    *,
    name: str,
    db: int = 0,
    pubsub_channels: Optional[set[str]] = None,
) -> GlideClient:
    addresses: list[NodeAddress] = []
    if valkey_target.addr:
        host, port = addr_to_hostport_pair(valkey_target.addr)
        addresses.append(NodeAddress(host=str(host), port=int(port)))

    if sentinel_addresses := valkey_target.sentinel:
        for address in sentinel_addresses:
            host, port = addr_to_hostport_pair(address)
            addresses.append(NodeAddress(host=str(host), port=int(port)))

    credentials: Optional[ServerCredentials] = None
    if valkey_target.password:
        credentials = ServerCredentials(
            password=valkey_target.password,
        )
    pubsub_subscriptions: Optional[GlideClientConfiguration.PubSubSubscriptions] = None
    if pubsub_channels is not None:
        pubsub_subscriptions = GlideClientConfiguration.PubSubSubscriptions(
            channels_and_patterns={
                GlideClientConfiguration.PubSubChannelModes.Exact: pubsub_channels,
            },
            callback=None,
            context=None,
        )
    if not addresses:
        raise ValueError("At least one Redis address is required to create a GlideClient.")
    config = GlideClientConfiguration(
        addresses,
        use_tls=valkey_target.use_tls,
        advanced_config=AdvancedGlideClientConfiguration(
            tls_config=TlsAdvancedConfiguration(
                use_insecure_tls=valkey_target.tls_skip_verify,
            ),
        ),
        credentials=credentials,
        database_id=db,
        client_name=name,
        request_timeout=valkey_target.request_timeout or 1_000,  # default to 1 second
        pubsub_subscriptions=pubsub_subscriptions,
    )
    return await GlideClient.create(config)
