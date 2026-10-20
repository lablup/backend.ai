import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterable
from contextlib import AbstractAsyncContextManager, aclosing, asynccontextmanager
from dataclasses import dataclass
from typing import Final, Self, override

from aiotools import cancel_and_wait
from glide import (
    AdvancedGlideClientConfiguration,
    ClosingError,
    GlideClient,
    GlideClientConfiguration,
    Logger,
    LogLevel,
    NodeAddress,
    RequestError,
    ServerCredentials,
    TlsAdvancedConfiguration,
)
from glide import ConnectionError as GlideConnectionError
from glide import TimeoutError as GlideTimeoutError

from ai.backend.common.clients.valkey_client.sentinel_monitor.base import AbstractSentinelMonitor
from ai.backend.common.exception import (
    ClientNotConnectedError,
    ValkeyRoleMismatchError,
    ValkeySentinelMasterNotFound,
    ValkeySentinelMonitorNotFound,
)
from ai.backend.common.types import HostPortPair, ValkeyTarget
from ai.backend.common.utils import addr_to_hostport_pair
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))


_DEFAULT_REQUEST_TIMEOUT: Final[int] = 1_000  # Default request timeout in milliseconds
_MONITOR_REQUEST_TIMEOUT: Final[int] = 3_000  # Fixed timeout for monitor client in milliseconds
_DEFAULT_MONITOR_FAILURE_THRESHOLD: Final[int] = (
    3  # Number of consecutive monitor ping failures before reconnection
)
_DEFAULT_OPERATION_FAILURE_THRESHOLD: Final[int] = (
    10  # Number of consecutive operation failures before reconnection
)
_DEFAULT_MONITOR_INTERVAL: Final[float] = 10.0  # Interval between ping attempts in seconds

# Connection error types that indicate a broken Valkey connection
_VALKEY_CONNECTION_ERRORS: tuple[type[Exception], ...] = (
    ClosingError,
    ClientNotConnectedError,
    ConnectionError,
    OSError,
)
# Request errors after which the master is checked with the Sentinel monitor
_MASTER_CHECK_ERRORS: tuple[type[RequestError], ...] = (
    GlideTimeoutError,
    GlideConnectionError,
)

# Lower-cased marker of the error for a write sent to a node that is no longer the master
_READONLY_ERROR_MARKER: Final[str] = "readonly"

Logger.init(LogLevel.OFF)  # Disable Glide logging by default


@dataclass
class ValkeyStandaloneTarget:
    address: str
    password: str | None = None
    request_timeout: int | None = None
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
    password: str | None = None
    sentinel_password: str | None = None
    request_timeout: int | None = None
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
            sentinel_password=valkey_target.sentinel_password,
            request_timeout=valkey_target.request_timeout,
            use_tls=valkey_target.use_tls,
            tls_skip_verify=valkey_target.tls_skip_verify,
        )


class AbstractValkeyClient(ABC):
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
    def connected_address(self) -> HostPortPair | None:
        """The address of the node the client is connected to, or None when not connected."""
        raise NotImplementedError

    @abstractmethod
    async def check_health(self) -> None:
        """
        Verify that the underlying connection is alive and points to a usable node.

        Standalone clients fall back to PING. Sentinel clients additionally verify
        that the connected node is currently a master via the ROLE command, so a
        Sentinel failover that demotes the previously-connected master to a replica
        is detected on the next health check.

        Raises:
            ClientNotConnectedError: If the client is not connected.
            ValkeyRoleMismatchError: If the connected node is no longer a master
                (Sentinel mode only).
            Exception: If the underlying command fails (network error, timeout, ...).
        """
        raise NotImplementedError

    @abstractmethod
    def client(self) -> AbstractAsyncContextManager[GlideClient]:
        """
        Acquire the client for an operation.

        This context manager wraps client operations.
        MonitoringValkeyClient overrides this to add failure tracking and
        automatic reconnection when the failure threshold is exceeded.
        """
        raise NotImplementedError


class ValkeyStandaloneClient(AbstractValkeyClient):
    _target: ValkeyStandaloneTarget
    _valkey_client: GlideClient | None
    _db_id: int
    _pubsub_channels: set[str] | None
    _human_readable_name: str

    def __init__(
        self,
        target: ValkeyStandaloneTarget,
        db_id: int,
        human_readable_name: str,
        pubsub_channels: set[str] | None = None,
    ) -> None:
        self._target = target
        self._valkey_client = None
        self._db_id = db_id
        self._human_readable_name = human_readable_name
        self._pubsub_channels = pubsub_channels

    @override
    async def connect(self) -> None:
        if self._valkey_client is not None:
            return

        await self._create_valkey_client()

    @override
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
            "valkey standalone client created",
            host=target_host,
            port=target_port,
            database_name=self._human_readable_name,
        )

    @override
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

    @override
    def connected_address(self) -> HostPortPair | None:
        if self._valkey_client is None:
            return None
        return HostPortPair(*addr_to_hostport_pair(self._target.address))

    @override
    async def check_health(self) -> None:
        """
        Verify that the standalone connection is alive by pinging the server.

        Raises:
            ClientNotConnectedError: If the client is not connected.
            Exception: If the ping fails.
        """
        if self._valkey_client is None:
            raise ClientNotConnectedError("ValkeyStandaloneClient is not connected")
        await self._valkey_client.ping()

    @asynccontextmanager
    @override
    async def client(self) -> AsyncIterator[GlideClient]:
        if self._valkey_client is None:
            raise ClientNotConnectedError("ValkeyStandaloneClient is not connected")
        yield self._valkey_client


class ValkeySentinelClient(AbstractValkeyClient):
    _target: ValkeySentinelTarget
    _db_id: int
    _human_readable_name: str
    _sentinel_monitor: AbstractSentinelMonitor
    _pubsub_channels: set[str] | None
    _valkey_client: GlideClient | None
    _master_address: HostPortPair | None

    def __init__(
        self,
        target: ValkeySentinelTarget,
        db_id: int,
        human_readable_name: str,
        sentinel_monitor: AbstractSentinelMonitor,
        pubsub_channels: set[str] | None = None,
    ) -> None:
        self._sentinel_monitor = sentinel_monitor
        self._db_id = db_id
        self._human_readable_name = human_readable_name
        self._target = target
        self._pubsub_channels = pubsub_channels
        self._valkey_client = None
        self._master_address = None

    @override
    async def connect(self) -> None:
        if self._valkey_client is not None:
            return

        await self._create_valkey_client()

    @override
    async def disconnect(self) -> None:
        if self._valkey_client:
            await self._valkey_client.close(err_message="ValkeySentinelClient is closed.")
            self._valkey_client = None
            self._master_address = None

    async def _create_valkey_client(self) -> None:
        master_address = await self._sentinel_monitor.get_master()
        addresses = [NodeAddress(host=str(master_address.host), port=master_address.port)]
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
        self._master_address = master_address

        log.info(
            "valkey master client created",
            host=str(master_address.host),
            port=master_address.port,
            database_name=self._human_readable_name,
        )

    @override
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

    @override
    def connected_address(self) -> HostPortPair | None:
        if self._valkey_client is None:
            return None
        return self._master_address

    @override
    async def check_health(self) -> None:
        """
        Verify that the connected node is still a master via the ROLE command.

        Running ROLE on the connected node (rather than asking Sentinel) detects
        the case where the previously-connected master has been demoted to a
        replica after a Sentinel failover, even before Sentinel's master view
        propagates. The command also doubles as a liveness check, so PING and
        master-change detection collapse into a single round-trip.

        Raises:
            ClientNotConnectedError: If the client is not connected.
            ValkeyRoleMismatchError: If the connected node is no longer a master.
            Exception: If the underlying ROLE command fails.
        """
        if self._valkey_client is None:
            raise ClientNotConnectedError("ValkeySentinelClient is not connected")
        result = await self._valkey_client.custom_command(["ROLE"])
        role = result[0] if result else None
        # ROLE responses come back as bytes from Glide; tolerate str for test/mocks.
        if role not in (b"master", "master"):
            raise ValkeyRoleMismatchError(
                f"Connected node role is {role!r}, expected 'master' "
                f"(service={self._target.service_name!r})"
            )

    @asynccontextmanager
    @override
    async def client(self) -> AsyncIterator[GlideClient]:
        if self._valkey_client is None:
            raise ClientNotConnectedError("ValkeySentinelClient is not connected")
        yield self._valkey_client


def _create_valkey_client_internal(
    valkey_target: ValkeyTarget,
    db_id: int,
    human_readable_name: str,
    pubsub_channels: set[str] | None = None,
    sentinel_monitor: AbstractSentinelMonitor | None = None,
) -> AbstractValkeyClient:
    """
    Internal helper to create a basic Valkey client (Standalone or Sentinel).
    """
    if valkey_target.sentinel:
        if sentinel_monitor is None:
            raise ValkeySentinelMonitorNotFound(
                f"A Sentinel monitor is required for service '{valkey_target.service_name}'"
            )
        sentinel_target = ValkeySentinelTarget.from_valkey_target(valkey_target)
        return ValkeySentinelClient(
            sentinel_target, db_id, human_readable_name, sentinel_monitor, pubsub_channels
        )
    standalone_target = ValkeyStandaloneTarget.from_valkey_target(valkey_target)
    return ValkeyStandaloneClient(standalone_target, db_id, human_readable_name, pubsub_channels)


def create_valkey_client(
    valkey_target: ValkeyTarget,
    db_id: int,
    human_readable_name: str,
    pubsub_channels: set[str] | None = None,
    sentinel_monitor: AbstractSentinelMonitor | None = None,
) -> AbstractValkeyClient:
    """
    Factory function to create a Valkey client based on the target type.

    Returns MonitoringValkeyClient that wraps separate work and monitor clients
    for improved reliability with long-running operations.
    A Sentinel target requires `sentinel_monitor`.
    """
    # Create operation client with user-specified timeout
    operation_client = _create_valkey_client_internal(
        valkey_target, db_id, human_readable_name, pubsub_channels, sentinel_monitor
    )

    # Create monitor client with fixed 3-second timeout
    monitor_target = ValkeyTarget(
        addr=valkey_target.addr,
        sentinel=valkey_target.sentinel,
        service_name=valkey_target.service_name,
        password=valkey_target.password,
        sentinel_password=valkey_target.sentinel_password,
        request_timeout=_MONITOR_REQUEST_TIMEOUT,
        use_tls=valkey_target.use_tls,
        tls_skip_verify=valkey_target.tls_skip_verify,
    )
    monitor_client = _create_valkey_client_internal(
        monitor_target, db_id, f"{human_readable_name}-monitor", None, sentinel_monitor
    )

    return MonitoringValkeyClient(
        operation_client,
        monitor_client,
        sentinel_monitor=sentinel_monitor if valkey_target.sentinel else None,
    )


@dataclass(frozen=True)
class MonitoringValkeyClientSpec:
    """Configuration for MonitoringValkeyClient."""

    reconnectable_exceptions: tuple[type[Exception], ...] = (
        ClosingError,
        ClientNotConnectedError,
        ValkeyRoleMismatchError,
    )
    """Exception types that indicate a broken connection requiring immediate reconnection."""

    monitor_failure_threshold: int = _DEFAULT_MONITOR_FAILURE_THRESHOLD
    """Number of consecutive monitor health-check failures before triggering reconnection."""

    operation_failure_threshold: int = _DEFAULT_OPERATION_FAILURE_THRESHOLD
    """Number of consecutive operation failures before triggering reconnection."""

    monitor_interval: float = _DEFAULT_MONITOR_INTERVAL
    """Interval in seconds between health check pings."""


class MonitoringValkeyClient(AbstractValkeyClient):
    """
    Valkey client wrapper with separated monitor client for health checks.

    This client wraps two separate Valkey clients:
    - operation_client: For actual operations (user-specified timeout)
    - monitor_client: For health checks only (fixed 3-second timeout)

    This separation prevents timeout issues when performing long-running operations
    like stream reads while maintaining connection health monitoring.

    With a Sentinel monitor, the clients reconnect when the master they are connected to
    is no longer the master: on a master change the monitor reports, and when a request
    or a health check fails and the monitor answers with another master.
    """

    _operation_client: AbstractValkeyClient
    _monitor_client: AbstractValkeyClient
    _sentinel_monitor: AbstractSentinelMonitor | None
    _reconnectable_exceptions: tuple[type[Exception], ...]
    _monitor_failure_threshold: int
    _operation_failure_threshold: int
    _monitor_interval: float
    _monitor_task: asyncio.Task[None] | None
    _watch_task: asyncio.Task[None] | None
    # Wakes the monitor loop before the interval ends; the two flags below say why.
    _wake_event: asyncio.Event
    _reconnect_requested: bool
    _master_check_requested: bool
    _monitor_consecutive_failure_count: int
    _operation_failure_count: int
    _closed: bool

    def __init__(
        self,
        operation_client: AbstractValkeyClient,
        monitor_client: AbstractValkeyClient,
        spec: MonitoringValkeyClientSpec | None = None,
        sentinel_monitor: AbstractSentinelMonitor | None = None,
    ) -> None:
        resolved_spec = spec or MonitoringValkeyClientSpec()
        self._operation_client = operation_client
        self._monitor_client = monitor_client
        self._sentinel_monitor = sentinel_monitor
        self._reconnectable_exceptions = resolved_spec.reconnectable_exceptions
        self._monitor_failure_threshold = resolved_spec.monitor_failure_threshold
        self._operation_failure_threshold = resolved_spec.operation_failure_threshold
        self._monitor_interval = resolved_spec.monitor_interval
        self._monitor_task = None
        self._watch_task = None
        self._wake_event = asyncio.Event()
        self._reconnect_requested = False
        self._master_check_requested = False
        self._monitor_consecutive_failure_count = 0
        self._operation_failure_count = 0
        self._closed = False

    @override
    async def connect(self) -> None:
        await self._operation_client.connect()
        await self._monitor_client.connect()
        self._closed = False
        self._monitor_task = asyncio.create_task(self._monitor_connection())
        if self._sentinel_monitor is not None:
            self._watch_task = asyncio.create_task(self._watch_master(self._sentinel_monitor))

    @override
    async def disconnect(self) -> None:
        self._closed = True
        if self._watch_task:
            await cancel_and_wait(self._watch_task)
            self._watch_task = None
        if self._monitor_task:
            await cancel_and_wait(self._monitor_task)
            self._monitor_task = None

        await self._monitor_client.disconnect()
        await self._operation_client.disconnect()

    @override
    async def ping(self) -> None:
        """
        Ping the server to check if the connection is alive.
        Uses the monitor client to avoid interfering with operation tasks.

        Raises:
            ClientNotConnectedError: If the client is not connected
            Exception: If the ping fails
        """
        await self._monitor_client.ping()

    @override
    def connected_address(self) -> HostPortPair | None:
        return self._operation_client.connected_address()

    @override
    async def check_health(self) -> None:
        """
        Run the unified health check via the monitor client.

        Raises:
            ClientNotConnectedError: If the monitor client is not connected.
            ValkeyRoleMismatchError: If the connected node is no longer a master (Sentinel).
            Exception: If the underlying health check command fails.
        """
        await self._monitor_client.check_health()

    @asynccontextmanager
    @override
    async def client(self) -> AsyncIterator[GlideClient]:
        """
        Acquire the operation client for use, tracking consecutive failures.

        On connection errors, increments the failure counter. When the
        consecutive failure threshold is exceeded, marks the client for
        reconnection by the monitor loop rather than reconnecting directly.
        Connection errors, timeouts and writes refused by a replica also ask
        the monitor loop to check the master with the Sentinel monitor.

        On successful operations, resets the failure counter.
        """
        try:
            async with self._operation_client.client() as conn:
                yield conn
        except _VALKEY_CONNECTION_ERRORS:
            self._request_master_check()
            self._operation_failure_count += 1
            log.warning(
                "valkey operation connection failed",
                failure_count=self._operation_failure_count,
                failure_threshold=self._operation_failure_threshold,
            )
            if self._operation_failure_count >= self._operation_failure_threshold:
                log.warning(
                    "valkey operation failure threshold reached, requesting reconnect",
                    failure_threshold=self._operation_failure_threshold,
                )
                self._operation_failure_count = 0
                self._request_reconnect()
            raise
        except RequestError as e:
            if isinstance(e, _MASTER_CHECK_ERRORS) or _READONLY_ERROR_MARKER in str(e).lower():
                self._request_master_check()
            raise
        else:
            self._operation_failure_count = 0

    def _request_reconnect(self) -> None:
        self._reconnect_requested = True
        self._wake_event.set()

    def _request_master_check(self) -> None:
        if self._sentinel_monitor is None:
            return
        self._master_check_requested = True
        self._wake_event.set()

    def _is_connected_to(self, address: HostPortPair) -> bool:
        return (
            self._operation_client.connected_address() == address
            and self._monitor_client.connected_address() == address
        )

    async def _master_changed(self) -> bool:
        """Whether the Sentinel monitor answers with a master the clients are not connected to."""
        if self._sentinel_monitor is None:
            return False
        connected = self._operation_client.connected_address()
        if connected is None:
            return True
        try:
            master = await self._sentinel_monitor.check_master(connected)
        except ValkeySentinelMasterNotFound as e:
            log.warning("valkey master check failed", exc_info=e)
            return False
        return not self._is_connected_to(master)

    async def _watch_master(self, sentinel_monitor: AbstractSentinelMonitor) -> None:
        while not self._closed:
            try:
                async with aclosing(sentinel_monitor.watch_master()) as masters:
                    async for master in masters:
                        if not self._is_connected_to(master):
                            self._request_master_check()
                # The Sentinel monitor is closed.
                return
            except ValkeySentinelMasterNotFound as e:
                log.warning("valkey master watch failed", exc_info=e)
                await asyncio.sleep(self._monitor_interval)

    async def _needs_reconnect(self, woken: bool) -> bool:
        """The health check runs only when the interval ends, so a request does not wait on it."""
        reconnect_requested = self._reconnect_requested
        master_check_requested = self._master_check_requested
        self._reconnect_requested = False
        self._master_check_requested = False
        if reconnect_requested:
            return True
        if master_check_requested and await self._master_changed():
            return True
        if woken:
            return False
        return await self._check_connection()

    async def _check_connection(self) -> bool:
        """
        Run a unified health check on the monitor client and decide if reconnection
        is needed.

        A failure on a master the Sentinel monitor no longer reports triggers immediate
        reconnection, as do reconnectable exceptions (including role mismatch after a
        Sentinel failover). Other transient errors accumulate against the monitor
        failure threshold before triggering reconnection.

        Returns:
            True if reconnection is needed, False otherwise.
        """
        try:
            await self._monitor_client.check_health()
        except Exception as e:
            if await self._master_changed():
                log.warning("valkey health check failed on a replaced master", exc_info=e)
                self._monitor_consecutive_failure_count = 0
                return True
            return self._count_health_check_failure(e)
        self._monitor_consecutive_failure_count = 0
        return False

    def _count_health_check_failure(self, e: Exception) -> bool:
        if isinstance(e, self._reconnectable_exceptions):
            log.warning("valkey health check requested reconnect", exc_info=e)
            self._monitor_consecutive_failure_count = 0
            return True
        self._monitor_consecutive_failure_count += 1
        log.warning(
            "valkey connection monitoring failed",
            exc_info=e,
            failure_count=self._monitor_consecutive_failure_count,
            failure_threshold=self._monitor_failure_threshold,
        )
        if self._monitor_consecutive_failure_count >= self._monitor_failure_threshold:
            log.warning(
                "valkey monitor failure threshold reached, reconnecting",
                failure_threshold=self._monitor_failure_threshold,
            )
            self._monitor_consecutive_failure_count = 0
            return True
        return False

    async def _monitor_connection(self) -> None:
        log.debug("valkey connection monitor started")
        try:
            while True:
                try:
                    # Wait for either the monitor interval or an explicit request
                    woken = True
                    try:
                        await asyncio.wait_for(
                            self._wake_event.wait(),
                            timeout=self._monitor_interval,
                        )
                    except TimeoutError:
                        woken = False
                    self._wake_event.clear()
                    if await self._needs_reconnect(woken):
                        log.info("valkey clients reconnecting")
                        await self._reconnect()
                except asyncio.CancelledError:
                    # Normal shutdown - don't log as error
                    raise
                except Exception:
                    if not self._closed:
                        log.exception("valkey connection monitor failed")
                        continue
                    raise
        finally:
            log.debug("valkey connection monitor stopped", closed=self._closed)

    async def _reconnect(self) -> None:
        # Disconnect both clients
        try:
            await self._monitor_client.disconnect()
        except Exception as e:
            log.warning("valkey monitor client disconnect failed", exc_info=e)

        try:
            await self._operation_client.disconnect()
        except Exception as e:
            log.warning("valkey operation client disconnect failed", exc_info=e)

        # Reconnect both clients
        await self._operation_client.connect()
        await self._monitor_client.connect()
