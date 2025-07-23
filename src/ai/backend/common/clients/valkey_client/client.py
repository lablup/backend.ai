import asyncio
import functools
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Awaitable, Callable, Iterable, Optional, ParamSpec, Self, TypeVar, cast

import glide
from glide import (
    GlideClient,
    GlideClientConfiguration,
    Logger,
    LogLevel,
    NodeAddress,
    ServerCredentials,
)
from redis.asyncio.sentinel import Sentinel

from ai.backend.common.exception import BackendAIError, UnreachableError
from ai.backend.common.metrics.metric import (
    DomainType,
    LayerMetricObserver,
    LayerType,
)
from ai.backend.logging import BraceStyleAdapter

from ...types import HostPortPair, RedisTarget
from ...validators import DelimiterSeperatedList
from ...validators import HostPortPair as _HostPortPair

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


_DEFAULT_REQUEST_TIMEOUT = 1_000  # Default request timeout in milliseconds

Logger.init(LogLevel.OFF)  # Disable Glide logging by default


@dataclass
class ValkeyStandaloneTarget:
    address: HostPortPair
    password: Optional[str] = None
    request_timeout: Optional[int] = None

    @classmethod
    def from_redis_target(cls, redis_target: RedisTarget) -> Self:
        """
        Create a ValkeyConnectionConfig from a RedisTarget.
        """
        if not redis_target.addr:
            raise ValueError("RedisTarget must have an address for standalone mode")
        return cls(
            address=redis_target.addr,
            password=redis_target.password,
            request_timeout=1_000,  # Default request timeout
        )


def _sentinel_from_redis_target(
    redis_target: RedisTarget,
) -> Optional[Iterable[HostPortPair]]:
    if isinstance(redis_target.sentinel, str):
        return DelimiterSeperatedList(_HostPortPair).check_and_return(redis_target.sentinel)
    elif isinstance(redis_target.sentinel, list):
        return redis_target.sentinel
    return None


@dataclass
class ValkeySentinelTarget:
    sentinel_addresses: Iterable[HostPortPair]
    service_name: str
    password: Optional[str] = None
    request_timeout: Optional[int] = None

    @classmethod
    def from_redis_target(cls, redis_target: RedisTarget) -> Self:
        """
        Create a ValkeySentinelTarget from a RedisTarget.
        """
        if not redis_target.service_name:
            raise ValueError("RedisTarget must have service_name when using sentinel")
        # Convert sentinel addresses to list format
        sentinel_addresses = _sentinel_from_redis_target(redis_target)
        if not sentinel_addresses:
            raise ValueError("RedisTarget sentinel configuration is invalid or empty")

        return cls(
            sentinel_addresses=sentinel_addresses,
            service_name=redis_target.service_name,
            password=redis_target.password,
            request_timeout=1_000,  # Default request timeout
        )


class AbstractValkeyClient(ABC):
    @property
    @abstractmethod
    def client(self) -> GlideClient:
        pass

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass


class ValkeyStandaloneClient(AbstractValkeyClient):
    _target: ValkeyStandaloneTarget
    _valkey_client: Optional[GlideClient]
    _db_id: int
    _pubsub_channels: Optional[set[str]]
    _human_readable_name: str

    def __init__(
        self,
        target: ValkeyStandaloneTarget,
        db_id: int,
        human_readable_name: str,
        pubsub_channels: Optional[set[str]] = None,
    ) -> None:
        self._target = target
        self._valkey_client = None
        self._db_id = db_id
        self._human_readable_name = human_readable_name
        self._pubsub_channels = pubsub_channels

    @property
    def client(self) -> GlideClient:
        if self._valkey_client is None:
            raise RuntimeError("ValkeyStandaloneClient not connected. Call connect() first.")
        return self._valkey_client

    async def connect(self) -> None:
        if self._valkey_client is not None:
            return

        addresses = [
            NodeAddress(host=str(self._target.address.host), port=self._target.address.port)
        ]
        credentials = (
            ServerCredentials(password=self._target.password) if self._target.password else None
        )

        config = GlideClientConfiguration(
            addresses,
            credentials=credentials,
            database_id=self._db_id,
            request_timeout=self._target.request_timeout or 1_000,
            pubsub_subscriptions=GlideClientConfiguration.PubSubSubscriptions(
                channels_and_patterns={
                    GlideClientConfiguration.PubSubChannelModes.Exact: self._pubsub_channels,
                },
                callback=None,
                context=None,
            )
            if self._pubsub_channels
            else None,
        )

        glide_client = await GlideClient.create(config)
        self._valkey_client = glide_client

        log.info(
            "Created ValkeyClient for standalone at {}:{} for database {}",
            self._target.address.host,
            self._target.address.port,
            self._human_readable_name,
        )

    async def disconnect(self) -> None:
        if self._valkey_client:
            await self._valkey_client.close(err_message="ValkeyStandaloneClient is closed.")
            self._valkey_client = None


class ValkeySentinelClient(AbstractValkeyClient):
    _target: ValkeySentinelTarget
    _db_id: int
    _human_readable_name: str
    _sentinel: Sentinel
    _pubsub_channels: Optional[set[str]]
    _valkey_client: Optional[GlideClient]
    _master_address: Optional[tuple[str, int]]
    _monitor_task: Optional[asyncio.Task[None]]

    def __init__(
        self,
        target: ValkeySentinelTarget,
        db_id: int,
        human_readable_name: str,
        pubsub_channels: Optional[set[str]] = None,
    ) -> None:
        self._sentinel = Sentinel(
            [(str(host), port) for host, port in target.sentinel_addresses],
            sentinel_kwargs={
                "password": target.password,
            },
        )
        self._db_id = db_id
        self._human_readable_name = human_readable_name
        self._target = target
        self._pubsub_channels = pubsub_channels
        self._valkey_client = None
        self._master_address = None
        self._monitor_task = None

    @property
    def client(self) -> GlideClient:
        if self._valkey_client is None:
            raise RuntimeError("ValkeySentinelClient not connected. Call connect() first.")
        return self._valkey_client

    async def connect(self) -> None:
        if self._valkey_client is not None:
            return

        await self._create_valkey_client()
        self._monitor_task = asyncio.create_task(self._monitor_master())

    async def disconnect(self) -> None:
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        if self._valkey_client:
            await self._valkey_client.close(err_message="ValkeySentinelClient is closed.")
            self._valkey_client = None

    async def _create_valkey_client(self) -> None:
        master_address = await self._get_master_address()
        if master_address is None:
            raise RuntimeError(
                f"Cannot find master for service '{self._target.service_name}' in {self._human_readable_name}"
            )

        self._master_address = master_address

        addresses = [NodeAddress(host=master_address[0], port=master_address[1])]
        credentials = (
            ServerCredentials(password=self._target.password) if self._target.password else None
        )

        config = GlideClientConfiguration(
            addresses,
            credentials=credentials,
            database_id=self._db_id,
            client_name=self._target.service_name,
            request_timeout=self._target.request_timeout or _DEFAULT_REQUEST_TIMEOUT,
            pubsub_subscriptions=GlideClientConfiguration.PubSubSubscriptions(
                channels_and_patterns={
                    GlideClientConfiguration.PubSubChannelModes.Exact: self._pubsub_channels,
                },
                callback=None,
                context=None,
            )
            if self._pubsub_channels
            else None,
        )

        glide_client = await GlideClient.create(config)
        self._valkey_client = glide_client

        log.info(
            "Created ValkeyClient for master at {}:{} for database {}",
            master_address[0],
            master_address[1],
            self._human_readable_name,
        )

    async def _get_master_address(self) -> Optional[tuple[str, int]]:
        try:
            return await self._sentinel.discover_master(self._target.service_name)
        except Exception as e:
            log.error(
                "Failed to discover master for service '{}': {}", self._target.service_name, e
            )
            return None

    async def _monitor_master(self) -> None:
        while True:
            try:
                await asyncio.sleep(5.0)
                current_master = await self._get_master_address()
                if current_master is None or current_master == self._master_address:
                    continue

                log.info(
                    "Master change detected for service '{}': {}:{} -> {}:{} in {}",
                    self._target.service_name,
                    self._master_address[0] if self._master_address else "unregistered",
                    self._master_address[1] if self._master_address else "unregistered",
                    current_master[0],
                    current_master[1],
                    self._human_readable_name,
                )
                await self._reconnect_to_new_master()

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.exception("Error in master monitoring: {}", e)

    async def _reconnect_to_new_master(self) -> None:
        if self._valkey_client:
            try:
                await self._valkey_client.close()
            except Exception as e:
                log.warning("Error closing old client: {}", e)
            self._valkey_client = None

        await self._create_valkey_client()


def create_valkey_client(
    target: RedisTarget,
    db_id: int,
    human_readable_name: str,
    pubsub_channels: Optional[set[str]] = None,
) -> AbstractValkeyClient:
    """
    Factory function to create a Valkey client based on the target type.
    """
    if target.sentinel:
        sentinel_target = ValkeySentinelTarget.from_redis_target(target)
        return ValkeySentinelClient(sentinel_target, db_id, human_readable_name, pubsub_channels)
    standalone_target = ValkeyStandaloneTarget.from_redis_target(target)
    return ValkeyStandaloneClient(standalone_target, db_id, human_readable_name, pubsub_channels)


P = ParamSpec("P")
R = TypeVar("R")


def create_layer_aware_valkey_decorator(
    layer: LayerType,
):
    """
    Factory function to create layer-aware valkey decorators.

    Args:
        layer: The layer type for metric observation

    Returns:
        A valkey_decorator function configured for the specified layer
    """

    def valkey_decorator(
        *,
        retry_count: int = 3,
        retry_delay: float = 0.1,
    ) -> Callable[
        [Callable[P, Awaitable[R]]],
        Callable[P, Awaitable[R]],
    ]:
        """
        Decorator for Valkey client operations that adds retry logic and metrics.

        Note: This decorator should only be applied to public methods that are exposed
        to external users. Internal/private methods should not use this decorator.
        """

        def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
            observer = LayerMetricObserver.instance()

            async def wrapper(*args, **kwargs) -> R:
                log.trace("Calling {}", func.__name__)
                start = time.perf_counter()
                for attempt in range(retry_count):
                    try:
                        observer.observe_layer_operation_triggered(
                            domain=DomainType.VALKEY,
                            layer=layer,
                            operation=func.__name__,
                        )
                        res = await func(*args, **kwargs)
                        observer.observe_layer_operation(
                            domain=DomainType.VALKEY,
                            layer=layer,
                            operation=func.__name__,
                            success=True,
                            duration=time.perf_counter() - start,
                        )
                        return res
                    except BackendAIError as e:
                        log.exception(
                            "Error in valkey request method {}, args: {}, kwargs: {}, retry_count: {}, error: {}",
                            func.__name__,
                            args,
                            kwargs,
                            retry_count,
                            e,
                        )
                        observer.observe_layer_operation(
                            domain=DomainType.VALKEY,
                            layer=layer,
                            operation=func.__name__,
                            success=False,
                            duration=time.perf_counter() - start,
                        )
                        # If it's a BackendAIError, this error is intended to be handled by the caller.
                        raise e
                    except glide.TimeoutError as e:
                        if attempt < retry_count - 1:
                            await asyncio.sleep(retry_delay)
                            continue
                        log.warning(
                            "Timeout in {}, args: {}, kwargs: {}, retry_count: {}, error: {}",
                            func.__name__,
                            args,
                            kwargs,
                            retry_count,
                            e,
                        )
                        observer.observe_layer_operation(
                            domain=DomainType.VALKEY,
                            layer=layer,
                            operation=func.__name__,
                            success=False,
                            duration=time.perf_counter() - start,
                        )
                    except Exception as e:
                        if attempt < retry_count - 1:
                            await asyncio.sleep(retry_delay)
                            continue
                        log.exception(
                            "Error in {}, args: {}, kwargs: {}, retry_count: {}, error: {}",
                            func.__name__,
                            args,
                            kwargs,
                            retry_count,
                            e,
                        )
                        observer.observe_layer_operation(
                            domain=DomainType.VALKEY,
                            layer=layer,
                            operation=func.__name__,
                            success=False,
                            duration=time.perf_counter() - start,
                        )
                        raise e
                raise UnreachableError(
                    f"Reached unreachable code in {func.__name__} after {retry_count} attempts"
                )

            return wrapper

        return decorator

    return valkey_decorator


def create_layer_aware_valkey_decorator_with_default(
    layer: LayerType,
):
    """
    Factory function to create layer-aware valkey decorators.

    Args:
        layer: The layer type for metric observation

    Returns:
        A valkey_decorator function configured for the specified layer
    """

    def valkey_decorator(
        *,
        retry_count: int = 1,
        retry_delay: float = 0.1,
        default_return: R,
    ):
        #    ) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
        """
        Decorator for Valkey client operations that adds retry logic and metrics.
        If `default_return` is set (even to None), it will be returned on final failure.
        """

        def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
            observer = LayerMetricObserver.instance()

            @functools.wraps(func)
            async def wrapper(*args, **kwargs) -> R:
                log.trace("Calling {}", func.__name__)
                start = time.perf_counter()

                for attempt in range(retry_count):
                    try:
                        observer.observe_layer_operation_triggered(
                            domain=DomainType.VALKEY,
                            layer=layer,
                            operation=func.__name__,
                        )
                        res = await func(*args, **kwargs)
                        observer.observe_layer_operation(
                            domain=DomainType.VALKEY,
                            layer=layer,
                            operation=func.__name__,
                            success=True,
                            duration=time.perf_counter() - start,
                        )
                        return res
                    except BackendAIError as e:
                        log.exception(
                            "Handled BackendAIError in {}, args: {}, kwargs: {}, retry: {}, error: {}",
                            func.__name__,
                            args,
                            kwargs,
                            retry_count,
                            e,
                        )
                        observer.observe_layer_operation(
                            domain=DomainType.VALKEY,
                            layer=layer,
                            operation=func.__name__,
                            success=False,
                            duration=time.perf_counter() - start,
                        )
                        break
                    except Exception as e:
                        if attempt < retry_count - 1:
                            await asyncio.sleep(retry_delay)
                            continue
                        log.exception(
                            "Unhandled error in {}, args: {}, kwargs: {}, retry: {}, error: {}",
                            func.__name__,
                            args,
                            kwargs,
                            retry_count,
                            e,
                        )
                        observer.observe_layer_operation(
                            domain=DomainType.VALKEY,
                            layer=layer,
                            operation=func.__name__,
                            success=False,
                            duration=time.perf_counter() - start,
                        )
                        break

                log.warning("Returning default value from {} after failure", func.__name__)
                return cast(R, default_return)

            return wrapper

        return decorator

    return valkey_decorator
