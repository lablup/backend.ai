import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Final, Iterable, Optional, Self

from aiotools import cancel_and_wait
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
from glide.exceptions import ClosingError
from redis.asyncio.sentinel import Sentinel

from ai.backend.common.exception import ClientNotConnectedError, ValkeySentinelMasterNotFound
from ai.backend.common.utils import addr_to_hostport_pair
from ai.backend.logging import BraceStyleAdapter

from ...types import ValkeyTarget

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


_DEFAULT_REQUEST_TIMEOUT: Final[int] = 1_000  # Default request timeout in milliseconds
_MONITOR_REQUEST_TIMEOUT: Final[int] = 3_000  # Fixed timeout for monitor client in milliseconds
_DEFAULT_CONSECUTIVE_FAILURE_THRESHOLD: Final[int] = (
    3  # Number of consecutive failures before reconnection
)
_DEFAULT_MONITOR_INTERVAL: Final[float] = 10.0  # Interval between ping attempts in seconds

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

    @abstractmethod
    async def ping(self) -> None:
        """
        Ping the server to check if the connection is alive.

        Raises:
            Exception: If the ping fails or connection is not available
        """
        pass

    @abstractmethod
    async def need_reconnect(self) -> bool:
        """
        Check if reconnection is needed.

        For Sentinel clients, this checks if the master address has changed.
        For standalone clients, this returns True only if the client is not connected.
        """
        raise NotImplementedError


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
            raise ClientNotConnectedError("ValkeyStandaloneClient is not connected")
        return self._valkey_client

    async def connect(self) -> None:
        if self._valkey_client is not None:
            return

        await self._create_valkey_client()

    async def disconnect(self) -> None:
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

        log.debug(
            "Created ValkeyClient for standalone at {}:{} for database {}",
            target_host,
            target_port,
            self._human_readable_name,
        )

    async def ping(self) -> None:
        """
        Ping the server to check if the connection is alive.

        Raises:
            ClientNotConnectedError: If the client is not connected
            Exception: If the ping fails
        """
        if self._valkey_client is None:
            raise ClientNotConnectedError("ValkeyStandaloneClient is not connected")
        await self._valkey_client.ping()

    async def need_reconnect(self) -> bool:
        return self._valkey_client is None


class ValkeySentinelClient(AbstractValkeyClient):
    _target: ValkeySentinelTarget
    _db_id: int
    _human_readable_name: str
    _sentinel: Sentinel
    _pubsub_channels: Optional[set[str]]
    _valkey_client: Optional[GlideClient]
    _master_address: Optional[tuple[str, int]]

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

    @property
    def client(self) -> GlideClient:
        if self._valkey_client is None:
            raise ClientNotConnectedError("ValkeySentinelClient is not connected")
        return self._valkey_client

    async def connect(self) -> None:
        if self._valkey_client is not None:
            return

        await self._create_valkey_client()

    async def disconnect(self) -> None:
        if self._valkey_client:
            await self._valkey_client.close(err_message="ValkeySentinelClient is closed.")
            self._valkey_client = None

    async def _create_valkey_client(self) -> None:
        master_address = await self._get_master_address()
        if master_address is None:
            raise ValkeySentinelMasterNotFound(
                f"Cannot find master for service '{self._target.service_name}'"
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

    async def ping(self) -> None:
        """
        Ping the current master to check if the connection is alive.

        Raises:
            ClientNotConnectedError: If the client is not connected
            Exception: If the ping fails
        """
        if self._valkey_client is None:
            raise ClientNotConnectedError("ValkeySentinelClient is not connected")
        await self._valkey_client.ping()

    async def need_reconnect(self) -> bool:
        """Check if reconnection is needed (client disconnected or master changed)."""
        if self._valkey_client is None:
            return True

        if self._master_address is None:
            return True

        current_master = await self._get_master_address()
        if current_master is None:
            return False

        return current_master != self._master_address


def _create_valkey_client_internal(
    valkey_target: ValkeyTarget,
    db_id: int,
    human_readable_name: str,
    pubsub_channels: Optional[set[str]] = None,
) -> AbstractValkeyClient:
    """
    Internal helper to create a basic Valkey client (Standalone or Sentinel).
    """
    if valkey_target.sentinel:
        sentinel_target = ValkeySentinelTarget.from_valkey_target(valkey_target)
        return ValkeySentinelClient(sentinel_target, db_id, human_readable_name, pubsub_channels)
    standalone_target = ValkeyStandaloneTarget.from_valkey_target(valkey_target)
    return ValkeyStandaloneClient(standalone_target, db_id, human_readable_name, pubsub_channels)


def create_valkey_client(
    valkey_target: ValkeyTarget,
    db_id: int,
    human_readable_name: str,
    pubsub_channels: Optional[set[str]] = None,
) -> AbstractValkeyClient:
    """
    Factory function to create a Valkey client based on the target type.

    Returns MonitoringValkeyClient that wraps separate work and monitor clients
    for improved reliability with long-running operations.
    """
    # Create operation client with user-specified timeout
    operation_client = _create_valkey_client_internal(
        valkey_target, db_id, human_readable_name, pubsub_channels
    )

    # Create monitor client with fixed 3-second timeout
    monitor_target = ValkeyTarget(
        addr=valkey_target.addr,
        sentinel=valkey_target.sentinel,
        service_name=valkey_target.service_name,
        password=valkey_target.password,
        request_timeout=_MONITOR_REQUEST_TIMEOUT,
        use_tls=valkey_target.use_tls,
        tls_skip_verify=valkey_target.tls_skip_verify,
    )
    monitor_client = _create_valkey_client_internal(
        monitor_target, db_id, f"{human_readable_name}-monitor", None
    )

    return MonitoringValkeyClient(operation_client, monitor_client)


class MonitoringValkeyClient(AbstractValkeyClient):
    """
    Valkey client wrapper with separated monitor client for health checks.

    This client wraps two separate Valkey clients:
    - operation_client: For actual operations (user-specified timeout)
    - monitor_client: For health checks only (fixed 3-second timeout)

    This separation prevents timeout issues when performing long-running operations
    like stream reads while maintaining connection health monitoring.
    """

    _operation_client: AbstractValkeyClient
    _monitor_client: AbstractValkeyClient
    _monitor_task: Optional[asyncio.Task[None]]
    _reconnectable_exceptions: tuple[type[Exception], ...]
    _consecutive_failure_threshold: int
    _consecutive_failure_count: int

    def __init__(
        self,
        operation_client: AbstractValkeyClient,
        monitor_client: AbstractValkeyClient,
        reconnectable_exceptions: tuple[type[Exception], ...] = (
            ClosingError,
            ClientNotConnectedError,
        ),
        consecutive_failure_threshold: int = _DEFAULT_CONSECUTIVE_FAILURE_THRESHOLD,
    ) -> None:
        self._operation_client = operation_client
        self._monitor_client = monitor_client
        self._monitor_task = None
        self._reconnectable_exceptions = reconnectable_exceptions
        self._consecutive_failure_threshold = consecutive_failure_threshold
        self._consecutive_failure_count = 0
        self._closed = False

    @property
    def client(self) -> GlideClient:
        return self._operation_client.client

    async def connect(self) -> None:
        await self._operation_client.connect()
        await self._monitor_client.connect()
        self._monitor_task = asyncio.create_task(self._monitor_connection())

    async def disconnect(self) -> None:
        self._closed = True
        if self._monitor_task:
            await cancel_and_wait(self._monitor_task)
            self._monitor_task = None

        await self._monitor_client.disconnect()
        await self._operation_client.disconnect()

    async def ping(self) -> None:
        """
        Ping the server to check if the connection is alive.
        Uses the monitor client to avoid interfering with operation tasks.

        Raises:
            ClientNotConnectedError: If the client is not connected
            Exception: If the ping fails
        """
        await self._monitor_client.ping()

    async def need_reconnect(self) -> bool:
        return await self._monitor_client.need_reconnect()

    async def _check_ping(self) -> bool:
        """
        Ping the monitor client and determine if reconnection is needed.

        Returns:
            True if reconnection is needed, False otherwise.
        """
        reconnectable_exceptions = self._reconnectable_exceptions
        try:
            await self._monitor_client.ping()
            self._consecutive_failure_count = 0
            return False
        except reconnectable_exceptions as e:
            log.warning("Connection error: {}, reconnecting immediately...", e)
            self._consecutive_failure_count = 0
            return True
        except Exception as e:
            self._consecutive_failure_count += 1
            log.warning(
                "Error in connection monitoring (consecutive failures: {}/{}): {}",
                self._consecutive_failure_count,
                self._consecutive_failure_threshold,
                e,
            )
            if self._consecutive_failure_count >= self._consecutive_failure_threshold:
                log.warning(
                    "Consecutive failure threshold reached ({}), reconnecting...",
                    self._consecutive_failure_threshold,
                )
                self._consecutive_failure_count = 0
                return True
            return False

    async def _check_connection(self) -> bool:
        """
        Check if reconnection is needed by ping and need_reconnect.

        Returns:
            True if reconnection is needed, False otherwise.
        """
        if await self._check_ping():
            return True

        if await self._monitor_client.need_reconnect():
            log.info("Reconnection needed (master changed), reconnecting...")
            return True

        return False

    async def _monitor_connection(self) -> None:
        log.info("Starting Valkey connection monitor task...")
        try:
            while True:
                try:
                    await asyncio.sleep(_DEFAULT_MONITOR_INTERVAL)
                    if await self._check_connection():
                        log.info("Reconnecting Valkey clients...")
                        await self._reconnect()
                except asyncio.CancelledError:
                    # Normal shutdown - don't log as error
                    raise
                except Exception as e:
                    if not self._closed:
                        log.exception("Error in Valkey connection monitor: {}", e)
                        continue
                    raise
        finally:
            log.info("Valkey connection monitor task stopped. Client closed: {}", self._closed)

    async def _reconnect(self) -> None:
        # Disconnect both clients
        try:
            await self._monitor_client.disconnect()
        except Exception as e:
            log.warning("Error disconnecting monitor client: {}", e)

        try:
            await self._operation_client.disconnect()
        except Exception as e:
            log.warning("Error disconnecting operation client: {}", e)

        # Reconnect both clients
        await self._operation_client.connect()
        await self._monitor_client.connect()
