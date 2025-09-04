import asyncio
import functools
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Iterable, Optional, ParamSpec, Self, TypeVar, cast

import glide
from glide import (
    AdvancedGlideClientConfiguration,
    GlideClient,
    GlideClientConfiguration,
    Logger,
    LogLevel,
    NodeAddress,
    ServerCredentials,
    TlsAdvancedConfiguration,
)
from redis.asyncio.sentinel import Sentinel

from ai.backend.common.exception import BackendAIError, UnreachableError
from ai.backend.common.metrics.metric import (
    DomainType,
    LayerMetricObserver,
    LayerType,
)
from ai.backend.common.utils import addr_to_hostport_pair
from ai.backend.logging import BraceStyleAdapter

from ...types import ValkeyTarget

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


_DEFAULT_REQUEST_TIMEOUT = 1_000  # Default request timeout in milliseconds

Logger.init(LogLevel.OFF)  # Disable Glide logging by default


SSL_CERT_NONE = "none"
SSL_CERT_REQUIRED = "required"


@dataclass
class ValkeyStandaloneTarget:
    address: str
    password: Optional[str] = None
    request_timeout: Optional[int] = None
    use_tls: bool = False
    tls_skip_verify: bool = False

    @classmethod
    def from_valkey_target(cls, valkey_target: ValkeyTarget) -> Self:
        """
        Create a ValkeyConnectionConfig from a RedisTarget.
        """
        if not valkey_target.addr:
            raise ValueError("RedisTarget must have an address for standalone mode")
        return cls(
            address=valkey_target.addr,
            password=valkey_target.password,
            request_timeout=valkey_target.request_timeout,
            use_tls=valkey_target.use_tls,
            tls_skip_verify=valkey_target.tls_skip_verify,
        )


@dataclass
class ValkeySentinelTarget:
    sentinel_addresses: Iterable[str]
    service_name: str
    password: Optional[str] = None
    request_timeout: Optional[int] = None
    use_tls: bool = False
    tls_skip_verify: bool = False

    @classmethod
    def from_valkey_target(cls, valkey_target: ValkeyTarget) -> Self:
        """
        Create a ValkeySentinelTarget from a ValkeyTarget.
        """
        if not valkey_target.service_name:
            raise ValueError("RedisTarget must have service_name when using sentinel")

        if not valkey_target.sentinel:
            raise ValueError("RedisTarget sentinel configuration is invalid or empty")

        return cls(
            sentinel_addresses=valkey_target.sentinel,
            service_name=valkey_target.service_name,
            password=valkey_target.password,
            request_timeout=valkey_target.request_timeout,
            use_tls=valkey_target.use_tls,
            tls_skip_verify=valkey_target.tls_skip_verify,
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
    _monitor_task: Optional[asyncio.Task[None]]

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
        self._monitor_task = None

    @property
    def client(self) -> GlideClient:
        if self._valkey_client is None:
            raise RuntimeError("ValkeyStandaloneClient not connected. Call connect() first.")
        return self._valkey_client

    async def connect(self) -> None:
        if self._valkey_client is not None:
            return

        await self._create_valkey_client()
        self._monitor_task = asyncio.create_task(self._monitor_connection())

    async def disconnect(self) -> None:
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        if self._valkey_client:
            await self._valkey_client.close(err_message="ValkeyStandaloneClient is closed.")
            self._valkey_client = None

    async def _create_valkey_client(self) -> None:
        target_host, target_port = addr_to_hostport_pair(self._target.address)
        addresses = [NodeAddress(host=target_host, port=target_port)]

        credentials = (
            ServerCredentials(password=self._target.password) if self._target.password else None
        )

        config = GlideClientConfiguration(
            addresses,
            credentials=credentials,
            database_id=self._db_id,
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
            use_tls=self._target.use_tls,
            advanced_config=AdvancedGlideClientConfiguration(
                tls_config=TlsAdvancedConfiguration(
                    use_insecure_tls=self._target.tls_skip_verify,
                ),
            ),
        )

        glide_client = await GlideClient.create(config)
        self._valkey_client = glide_client

        log.info(
            "Created ValkeyClient for standalone at {}:{} for database {}",
            target_host,
            target_port,
            self._human_readable_name,
        )

    async def _ping(self) -> bool:
        """
        Ping the server to check if the connection is alive.
        """
        if self._valkey_client is None:
            return False
        try:
            await self._valkey_client.ping()
            return True
        except glide.ClosingError as e:
            target_host, target_port = addr_to_hostport_pair(self._target.address)
            log.warning(
                "Valkey client is closed for standalone at {}:{}, human readable name '{}': {}",
                target_host,
                target_port,
                self._human_readable_name,
                e,
            )
            return False
        except Exception as e:
            log.debug(
                "Failed to ping to service '{}', human readable name '{}', but cannot check if the connection is alive: {}",
                self._target.address,
                self._human_readable_name,
                e,
            )
            return True

    async def _check_connection(self) -> bool:
        """
        Check if the current connection is alive.
        If not, return False to trigger reconnection.
        """
        if not await self._ping():
            target_host, target_port = addr_to_hostport_pair(self._target.address)
            log.warning(
                "Connection to standalone server {}:{} is down, attempting to reconnect",
                target_host,
                target_port,
            )
            return False
        return True

    async def _monitor_connection(self) -> None:
        while True:
            try:
                await asyncio.sleep(10.0)
                if await self._check_connection():
                    continue
                target_host, target_port = addr_to_hostport_pair(self._target.address)
                log.info(
                    "Reconnecting to standalone server at {}:{}",
                    target_host,
                    target_port,
                )
                await self._reconnect()

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.exception("Error in connection monitoring: {}", e)

    async def _reconnect(self) -> None:
        if self._valkey_client:
            try:
                await self._valkey_client.close()
            except Exception as e:
                log.warning("Error closing old client: {}", e)
            self._valkey_client = None

        await self._create_valkey_client()


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
        sentinel_addrs = []
        for addr in target.sentinel_addresses:
            host, port = addr_to_hostport_pair(addr)
            sentinel_addrs.append((host, port))

        sentinel_kwargs: dict[str, Any] = {
            "password": target.password,
            "ssl": target.use_tls,
            "ssl_cert_reqs": SSL_CERT_NONE if target.tls_skip_verify else SSL_CERT_REQUIRED,
        }
        self._sentinel = Sentinel(
            sentinel_addrs,
            sentinel_kwargs=sentinel_kwargs,
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
        self._monitor_task = asyncio.create_task(self._monitor_connction())

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
            use_tls=self._target.use_tls,
            advanced_config=AdvancedGlideClientConfiguration(
                tls_config=TlsAdvancedConfiguration(
                    use_insecure_tls=self._target.tls_skip_verify,
                ),
            ),
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

    async def _ping(self) -> bool:
        """
        Ping the current master to check if the connection is alive.
        """
        if self._valkey_client is None:
            return False
        try:
            await self._valkey_client.ping()
            return True
        except glide.ClosingError as e:
            log.warning(
                "Valkey client is closed for service '{}', human readable name '{}': {}",
                self._target.service_name,
                self._human_readable_name,
                e,
            )
            return False
        except Exception as e:
            log.debug(
                "Failed to ping to service '{}', human readable name '{}', but cannot check if the connection is alive: {}",
                self._target.service_name,
                self._human_readable_name,
                e,
            )
            return True

    async def _check_connection(self) -> bool:
        """
        Check if the current master connection is alive.
        If not, attempt to reconnect.
        """
        if not await self._ping():
            log.warning(
                "Connection to master {}:{} is down, attempting to reconnect",
                self._master_address[0] if self._master_address else "unregistered",
                self._master_address[1] if self._master_address else "unregistered",
            )
            return False
        current_master = await self._get_master_address()
        if current_master is None or current_master == self._master_address:
            return True
        log.warning(
            "Master change detected for service '{}': {}:{} -> {}:{} in {}",
            self._target.service_name,
            self._master_address[0] if self._master_address else "unregistered",
            self._master_address[1] if self._master_address else "unregistered",
            current_master[0],
            current_master[1],
            self._human_readable_name,
        )
        return False

    async def _monitor_connction(self) -> None:
        while True:
            try:
                await asyncio.sleep(10.0)
                if await self._check_connection():
                    continue
                log.info("Reconnecting to new master for service '{}'", self._target.service_name)
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
    valkey_target: ValkeyTarget,
    db_id: int,
    human_readable_name: str,
    pubsub_channels: Optional[set[str]] = None,
) -> AbstractValkeyClient:
    """
    Factory function to create a Valkey client based on the target type.
    """
    if valkey_target.sentinel:
        sentinel_target = ValkeySentinelTarget.from_valkey_target(valkey_target)
        return ValkeySentinelClient(sentinel_target, db_id, human_readable_name, pubsub_channels)
    standalone_target = ValkeyStandaloneTarget.from_valkey_target(valkey_target)
    return ValkeyStandaloneClient(standalone_target, db_id, human_readable_name, pubsub_channels)


P = ParamSpec("P")
R = TypeVar("R")


def create_layer_aware_valkey_decorator(
    layer: LayerType,
    default_retry_count: int = 3,
    default_retry_delay: float = 0.1,
):
    """
    Factory function to create layer-aware valkey decorators.

    Args:
        layer: The layer type for metric observation
        default_retry_count: Default number of retries for valkey operations
        default_retry_delay: Default delay between retries in seconds

    Returns:
        A valkey_decorator function configured for the specified layer
    """

    def valkey_decorator(
        *,
        retry_count: int = default_retry_count,
        retry_delay: float = default_retry_delay,
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
            operation = func.__name__

            async def wrapper(*args, **kwargs) -> R:
                log.trace("Calling {}", operation)
                start = time.perf_counter()
                for attempt in range(retry_count):
                    try:
                        observer.observe_layer_operation_triggered(
                            domain=DomainType.VALKEY,
                            layer=layer,
                            operation=operation,
                        )
                        res = await func(*args, **kwargs)
                        observer.observe_layer_operation(
                            domain=DomainType.VALKEY,
                            layer=layer,
                            operation=operation,
                            success=True,
                            duration=time.perf_counter() - start,
                        )
                        return res
                    except BackendAIError as e:
                        log.exception(
                            "Error in valkey request method {}, args: {}, kwargs: {}, retry_count: {}, error: {}",
                            operation,
                            args,
                            kwargs,
                            retry_count,
                            e,
                        )
                        observer.observe_layer_operation(
                            domain=DomainType.VALKEY,
                            layer=layer,
                            operation=operation,
                            success=False,
                            duration=time.perf_counter() - start,
                        )
                        # If it's a BackendAIError, this error is intended to be handled by the caller.
                        raise e
                    except glide.TimeoutError as e:
                        if attempt < retry_count - 1:
                            observer.observe_layer_retry(
                                domain=DomainType.VALKEY,
                                layer=layer,
                                operation=operation,
                            )
                            await asyncio.sleep(retry_delay)
                            continue
                        log.warning(
                            "Timeout in {}, args: {}, kwargs: {}, retry_count: {}, error: {}",
                            operation,
                            args,
                            kwargs,
                            retry_count,
                            e,
                        )
                        observer.observe_layer_operation(
                            domain=DomainType.VALKEY,
                            layer=layer,
                            operation=operation,
                            success=False,
                            duration=time.perf_counter() - start,
                        )
                        raise e
                    except Exception as e:
                        if attempt < retry_count - 1:
                            log.debug(
                                "Retrying {} due to error: {} (attempt {}/{})",
                                operation,
                                e,
                                attempt + 1,
                                retry_count,
                            )
                            observer.observe_layer_retry(
                                domain=DomainType.VALKEY,
                                layer=layer,
                                operation=operation,
                            )
                            await asyncio.sleep(retry_delay)
                            continue
                        log.exception(
                            "Error in {}, args: {}, kwargs: {}, retry_count: {}, error: {}",
                            operation,
                            args,
                            kwargs,
                            retry_count,
                            e,
                        )
                        observer.observe_layer_operation(
                            domain=DomainType.VALKEY,
                            layer=layer,
                            operation=operation,
                            success=False,
                            duration=time.perf_counter() - start,
                        )
                        raise e
                raise UnreachableError(
                    f"Reached unreachable code in {operation} after {retry_count} attempts"
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
    ) -> Callable[
        [Callable[P, Awaitable[R]]],
        Callable[P, Awaitable[R]],
    ]:
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
