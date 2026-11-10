from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import override
from unittest.mock import AsyncMock, MagicMock

import pytest
from glide import ClosingError, GlideClient, RequestError
from glide import ConnectionError as GlideConnectionError
from glide import TimeoutError as GlideTimeoutError

from ai.backend.common.clients.valkey_client.client import (
    MonitoringValkeyClient,
    MonitoringValkeyClientSpec,
    ValkeySentinelClient,
    ValkeySentinelTarget,
    ValkeyStandaloneClient,
    ValkeyStandaloneTarget,
    create_valkey_client,
)
from ai.backend.common.clients.valkey_client.sentinel_monitor.base import AbstractSentinelMonitor
from ai.backend.common.exception import (
    ClientNotConnectedError,
    ValkeyRoleMismatchError,
    ValkeySentinelMasterNotFound,
    ValkeySentinelMonitorNotFound,
)
from ai.backend.common.types import HostPortPair, ValkeyTarget

INITIAL_MASTER = HostPortPair("127.0.0.1", 6379)
NEW_MASTER = HostPortPair("10.0.0.2", 6379)


class _FakeSentinelMonitor(AbstractSentinelMonitor):
    """Reports `master` and lets a test switch it."""

    master: HostPortPair
    check_master_calls: list[HostPortPair]
    _changed: asyncio.Event
    _closed: bool

    def __init__(self, master: HostPortPair) -> None:
        self.master = master
        self.check_master_calls = []
        self._changed = asyncio.Event()
        self._closed = False

    @override
    async def start(self) -> None:
        pass

    @override
    async def close(self) -> None:
        self._closed = True
        self._changed.set()

    @override
    async def get_master(self) -> HostPortPair:
        return self.master

    @override
    async def watch_master(self) -> AsyncGenerator[HostPortPair]:
        last: HostPortPair | None = None
        while not self._closed:
            changed = self._changed
            if self.master != last:
                last = self.master
                yield last
            await changed.wait()

    @override
    async def check_master(self, address: HostPortPair) -> HostPortPair:
        self.check_master_calls.append(address)
        return self.master

    def switch(self, master: HostPortPair) -> None:
        self.master = master
        changed = self._changed
        self._changed = asyncio.Event()
        changed.set()


async def _wait_until(condition: Callable[[], bool], timeout: float = 1.0) -> None:
    async with asyncio.timeout(timeout):
        while not condition():
            await asyncio.sleep(0.01)


# ---- shared fixtures ----


@pytest.fixture
def sentinel_target() -> ValkeySentinelTarget:
    return ValkeySentinelTarget(
        sentinel_addresses=["127.0.0.1:26379"],
        service_name="mymaster",
        password=None,
        request_timeout=1000,
        use_tls=False,
        tls_skip_verify=False,
    )


@pytest.fixture
def mock_glide_client() -> AsyncMock:
    client = AsyncMock()
    client.ping = AsyncMock(return_value=b"PONG")
    client.close = AsyncMock()
    # ROLE response on a master node: [role, replication_offset, [replicas]]
    client.custom_command = AsyncMock(return_value=[b"master", 0, []])
    return client


@pytest.fixture
def sentinel_monitor() -> _FakeSentinelMonitor:
    return _FakeSentinelMonitor(INITIAL_MASTER)


@pytest.fixture
def sentinel_client(
    sentinel_target: ValkeySentinelTarget,
    sentinel_monitor: _FakeSentinelMonitor,
) -> ValkeySentinelClient:
    return ValkeySentinelClient(
        target=sentinel_target,
        db_id=0,
        human_readable_name="test.sentinel",
        sentinel_monitor=sentinel_monitor,
    )


@pytest.fixture
def connected_sentinel_client(
    sentinel_client: ValkeySentinelClient,
    mock_glide_client: AsyncMock,
) -> ValkeySentinelClient:
    sentinel_client._valkey_client = mock_glide_client
    sentinel_client._master_address = INITIAL_MASTER
    return sentinel_client


def _create_mock_sentinel_client(sentinel_monitor: _FakeSentinelMonitor) -> AsyncMock:
    """A Sentinel client connecting to the master `sentinel_monitor` reports."""
    mock_glide = AsyncMock()
    mock_glide.ping = AsyncMock(return_value=b"PONG")
    mock_glide.custom_command = AsyncMock(return_value=[b"master", 0, []])

    client = AsyncMock(spec=ValkeySentinelClient)
    address: list[HostPortPair | None] = [sentinel_monitor.master]

    async def connect() -> None:
        address[0] = sentinel_monitor.master

    async def disconnect() -> None:
        address[0] = None

    client.ping = AsyncMock()
    client.check_health = AsyncMock()
    client.connect = AsyncMock(side_effect=connect)
    client.disconnect = AsyncMock(side_effect=disconnect)
    client.connected_address = MagicMock(side_effect=lambda: address[0])

    @asynccontextmanager
    async def mock_client_cm() -> AsyncIterator[AsyncMock]:
        yield mock_glide

    client.client = mock_client_cm
    client._mock_glide = mock_glide
    return client


# ---- ValkeySentinelClient.connect() / disconnect() ----


class TestValkeySentinelClientConnect:
    """Tests for ValkeySentinelClient.connect() lifecycle."""

    async def test_connects_to_master_from_sentinel_monitor(
        self,
        sentinel_client: ValkeySentinelClient,
        mock_glide_client: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_create = AsyncMock(return_value=mock_glide_client)
        monkeypatch.setattr(GlideClient, "create", mock_create)
        await sentinel_client.connect()

        assert sentinel_client._valkey_client is mock_glide_client
        assert sentinel_client.connected_address() == INITIAL_MASTER
        address = mock_create.call_args.args[0].addresses[0]
        assert (address.host, address.port) == (str(INITIAL_MASTER.host), INITIAL_MASTER.port)

    async def test_raises_master_not_found_from_sentinel_monitor(
        self,
        sentinel_client: ValkeySentinelClient,
        sentinel_monitor: _FakeSentinelMonitor,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(
            sentinel_monitor,
            "get_master",
            AsyncMock(side_effect=ValkeySentinelMasterNotFound("no master")),
        )
        with pytest.raises(ValkeySentinelMasterNotFound):
            await sentinel_client.connect()
        assert sentinel_client.connected_address() is None

    async def test_skips_if_already_connected(
        self,
        connected_sentinel_client: ValkeySentinelClient,
        sentinel_monitor: _FakeSentinelMonitor,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        get_master = AsyncMock(return_value=NEW_MASTER)
        monkeypatch.setattr(sentinel_monitor, "get_master", get_master)
        await connected_sentinel_client.connect()
        get_master.assert_not_called()

    async def test_disconnect_closes_client(
        self,
        connected_sentinel_client: ValkeySentinelClient,
        mock_glide_client: AsyncMock,
    ) -> None:
        await connected_sentinel_client.disconnect()

        mock_glide_client.close.assert_called_once()
        assert connected_sentinel_client._valkey_client is None
        assert connected_sentinel_client.connected_address() is None


# ---- ValkeySentinelClient.ping() ----


class TestValkeySentinelClientPing:
    """Tests for ValkeySentinelClient.ping()."""

    async def test_raises_when_not_connected(self, sentinel_client: ValkeySentinelClient) -> None:
        with pytest.raises(ClientNotConnectedError):
            await sentinel_client.ping()

    async def test_pings_successfully_when_connected(
        self,
        connected_sentinel_client: ValkeySentinelClient,
        mock_glide_client: AsyncMock,
    ) -> None:
        await connected_sentinel_client.ping()
        mock_glide_client.ping.assert_called_once()


# ---- MonitoringValkeyClient with Sentinel ----


class TestMonitoringValkeyClientWithSentinel:
    """Tests for MonitoringValkeyClient wrapping ValkeySentinelClient (mock-based)."""

    @pytest.fixture
    def mock_sentinel_operation_client(self, sentinel_monitor: _FakeSentinelMonitor) -> AsyncMock:
        return _create_mock_sentinel_client(sentinel_monitor)

    @pytest.fixture
    def mock_sentinel_monitor_client(self, sentinel_monitor: _FakeSentinelMonitor) -> AsyncMock:
        return _create_mock_sentinel_client(sentinel_monitor)

    @pytest.fixture
    def monitoring_client(
        self,
        mock_sentinel_operation_client: AsyncMock,
        mock_sentinel_monitor_client: AsyncMock,
        sentinel_monitor: _FakeSentinelMonitor,
    ) -> MonitoringValkeyClient:
        spec = MonitoringValkeyClientSpec(monitor_interval=0.01)
        return MonitoringValkeyClient(
            operation_client=mock_sentinel_operation_client,
            monitor_client=mock_sentinel_monitor_client,
            spec=spec,
            sentinel_monitor=sentinel_monitor,
        )

    # -- _check_connection --

    async def test_check_connection_no_reconnect_when_healthy(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        assert await monitoring_client._check_connection() is False

    async def test_check_connection_triggers_reconnect_on_role_mismatch(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        """Role mismatch (failover demoted the connected master) triggers immediate reconnect."""
        mock_sentinel_monitor_client.check_health.side_effect = ValkeyRoleMismatchError(
            "Connected node role is 'slave', expected 'master'"
        )
        assert await monitoring_client._check_connection() is True
        assert monitoring_client._monitor_consecutive_failure_count == 0

    @pytest.mark.parametrize(
        "exception",
        [
            ClosingError("Connection closed"),
            ClientNotConnectedError("Not connected"),
            ValkeyRoleMismatchError("Connected node role is 'slave', expected 'master'"),
        ],
        ids=["ClosingError", "ClientNotConnectedError", "ValkeyRoleMismatchError"],
    )
    async def test_check_connection_returns_true_on_reconnectable_exception(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
        exception: Exception,
    ) -> None:
        """Reconnectable exceptions trigger immediate reconnection."""
        mock_sentinel_monitor_client.check_health.side_effect = exception

        assert await monitoring_client._check_connection() is True
        assert monitoring_client._monitor_consecutive_failure_count == 0

    async def test_check_connection_accumulates_failures_until_threshold(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        """General exceptions accumulate; reconnect triggers at threshold (3)."""
        mock_sentinel_monitor_client.check_health.side_effect = TimeoutError("Timed out")

        assert await monitoring_client._check_connection() is False
        assert monitoring_client._monitor_consecutive_failure_count == 1

        assert await monitoring_client._check_connection() is False
        assert monitoring_client._monitor_consecutive_failure_count == 2

        # Third failure: threshold reached → reconnect
        assert await monitoring_client._check_connection() is True
        assert monitoring_client._monitor_consecutive_failure_count == 0

    async def test_check_connection_resets_failure_count_on_success(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        """Successful health check resets the consecutive failure counter."""
        mock_sentinel_monitor_client.check_health.side_effect = TimeoutError("Timed out")

        await monitoring_client._check_connection()
        await monitoring_client._check_connection()
        assert monitoring_client._monitor_consecutive_failure_count == 2

        # Recovery: health check succeeds
        mock_sentinel_monitor_client.check_health.side_effect = None
        mock_sentinel_monitor_client.check_health.return_value = None

        assert await monitoring_client._check_connection() is False
        assert monitoring_client._monitor_consecutive_failure_count == 0

    # -- _reconnect --

    async def test_reconnect_disconnects_and_reconnects_both_clients(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_operation_client: AsyncMock,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        await monitoring_client._reconnect()

        mock_sentinel_monitor_client.disconnect.assert_called_once()
        mock_sentinel_operation_client.disconnect.assert_called_once()
        mock_sentinel_operation_client.connect.assert_called_once()
        mock_sentinel_monitor_client.connect.assert_called_once()

    async def test_reconnect_continues_even_if_disconnect_fails(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_operation_client: AsyncMock,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        mock_sentinel_monitor_client.disconnect.side_effect = ConnectionError("Already closed")
        mock_sentinel_operation_client.disconnect.side_effect = ConnectionError("Already closed")

        await monitoring_client._reconnect()

        mock_sentinel_operation_client.connect.assert_called_once()
        mock_sentinel_monitor_client.connect.assert_called_once()

    # -- monitor loop --

    async def test_monitor_loop_calls_reconnect_on_role_mismatch(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Failover demotion (ROLE != master) on the monitor client triggers _reconnect."""
        call_count = 0

        async def fake_check_health() -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValkeyRoleMismatchError("Connected node role is 'slave', expected 'master'")
            raise asyncio.CancelledError

        mock_sentinel_monitor_client.check_health = fake_check_health

        mock_reconnect = AsyncMock()
        monkeypatch.setattr(monitoring_client, "_reconnect", mock_reconnect)

        task = asyncio.create_task(monitoring_client._monitor_connection())
        await asyncio.sleep(0.1)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        mock_reconnect.assert_called()

    async def test_monitor_loop_survives_reconnect_failure(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Monitor loop must not die when _reconnect() raises; it should log and retry."""
        check_count = 0

        async def fake_check_health() -> None:
            nonlocal check_count
            check_count += 1
            if check_count <= 2:
                raise ValkeyRoleMismatchError("Connected node role is 'slave', expected 'master'")
            raise asyncio.CancelledError

        mock_sentinel_monitor_client.check_health = fake_check_health

        reconnect_call_count = 0

        async def failing_then_succeeding_reconnect() -> None:
            nonlocal reconnect_call_count
            reconnect_call_count += 1
            if reconnect_call_count == 1:
                raise ConnectionError("Sentinel temporarily unavailable")

        monkeypatch.setattr(monitoring_client, "_reconnect", failing_then_succeeding_reconnect)

        task = asyncio.create_task(monitoring_client._monitor_connection())
        await asyncio.sleep(0.2)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert reconnect_call_count == 2


# ---- MonitoringValkeyClient following master changes ----


class TestMonitoringValkeyClientMasterChange:
    """Reconnection to the master the Sentinel monitor reports."""

    @pytest.fixture
    def mock_sentinel_operation_client(self, sentinel_monitor: _FakeSentinelMonitor) -> AsyncMock:
        return _create_mock_sentinel_client(sentinel_monitor)

    @pytest.fixture
    def mock_sentinel_monitor_client(self, sentinel_monitor: _FakeSentinelMonitor) -> AsyncMock:
        return _create_mock_sentinel_client(sentinel_monitor)

    @pytest.fixture
    async def monitoring_client(
        self,
        mock_sentinel_operation_client: AsyncMock,
        mock_sentinel_monitor_client: AsyncMock,
        sentinel_monitor: _FakeSentinelMonitor,
    ) -> AsyncIterator[MonitoringValkeyClient]:
        # A long interval keeps the periodic health check out of the way.
        spec = MonitoringValkeyClientSpec(monitor_interval=60.0)
        client = MonitoringValkeyClient(
            operation_client=mock_sentinel_operation_client,
            monitor_client=mock_sentinel_monitor_client,
            spec=spec,
            sentinel_monitor=sentinel_monitor,
        )
        yield client
        await client.disconnect()

    async def test_reconnects_when_watched_master_changes(
        self,
        monitoring_client: MonitoringValkeyClient,
        sentinel_monitor: _FakeSentinelMonitor,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        await monitoring_client.connect()
        sentinel_monitor.switch(NEW_MASTER)

        await _wait_until(lambda: monitoring_client.connected_address() == NEW_MASTER)
        assert mock_sentinel_monitor_client.connected_address() == NEW_MASTER

    async def test_does_not_reconnect_when_watched_master_is_connected(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_operation_client: AsyncMock,
    ) -> None:
        await monitoring_client.connect()
        await asyncio.sleep(0.1)

        mock_sentinel_operation_client.connect.assert_called_once()
        mock_sentinel_operation_client.disconnect.assert_not_called()

    @pytest.mark.parametrize(
        "error",
        [
            ConnectionError("connection refused"),
            GlideConnectionError("connection lost"),
            GlideTimeoutError("timed out"),
            RequestError("READONLY You can't write against a read only replica."),
        ],
        ids=["ConnectionError", "GlideConnectionError", "GlideTimeoutError", "READONLY"],
    )
    async def test_request_error_reconnects_when_master_moved(
        self,
        monitoring_client: MonitoringValkeyClient,
        sentinel_monitor: _FakeSentinelMonitor,
        error: Exception,
    ) -> None:
        """A switch whose notification never arrived is caught by the first failed request."""
        await monitoring_client.connect()
        assert monitoring_client._watch_task is not None
        monitoring_client._watch_task.cancel()
        sentinel_monitor.master = NEW_MASTER

        with pytest.raises(type(error)):
            async with monitoring_client.client() as _conn:
                raise error

        await _wait_until(lambda: monitoring_client.connected_address() == NEW_MASTER)
        assert sentinel_monitor.check_master_calls == [INITIAL_MASTER]

    async def test_request_error_keeps_connection_when_master_unchanged(
        self,
        monitoring_client: MonitoringValkeyClient,
        sentinel_monitor: _FakeSentinelMonitor,
        mock_sentinel_operation_client: AsyncMock,
    ) -> None:
        await monitoring_client.connect()

        with pytest.raises(GlideTimeoutError):
            async with monitoring_client.client() as _conn:
                raise GlideTimeoutError("timed out")

        await _wait_until(lambda: sentinel_monitor.check_master_calls == [INITIAL_MASTER])
        mock_sentinel_operation_client.disconnect.assert_not_called()

    async def test_unrelated_request_error_does_not_check_master(
        self,
        monitoring_client: MonitoringValkeyClient,
    ) -> None:
        with pytest.raises(RequestError):
            async with monitoring_client.client() as _conn:
                raise RequestError("WRONGTYPE Operation against a key holding the wrong kind")

        assert not monitoring_client._master_check_requested
        assert not monitoring_client._wake_event.is_set()

    async def test_request_errors_coalesce_into_one_master_check(
        self,
        monitoring_client: MonitoringValkeyClient,
        sentinel_monitor: _FakeSentinelMonitor,
    ) -> None:
        for _ in range(5):
            with pytest.raises(GlideTimeoutError):
                async with monitoring_client.client() as _conn:
                    raise GlideTimeoutError("timed out")

        assert await monitoring_client._needs_reconnect(woken=True) is False
        assert sentinel_monitor.check_master_calls == [INITIAL_MASTER]

    async def test_request_wakeup_skips_health_check(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        """A slow health check on an unreachable master must not delay the next master check."""
        with pytest.raises(GlideTimeoutError):
            async with monitoring_client.client() as _conn:
                raise GlideTimeoutError("timed out")

        assert await monitoring_client._needs_reconnect(woken=True) is False
        mock_sentinel_monitor_client.check_health.assert_not_called()

    async def test_health_check_failure_reconnects_at_once_when_master_moved(
        self,
        monitoring_client: MonitoringValkeyClient,
        sentinel_monitor: _FakeSentinelMonitor,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        """A timeout on the old master does not wait for the failure threshold."""
        mock_sentinel_monitor_client.check_health.side_effect = TimeoutError("ROLE timed out")
        sentinel_monitor.master = NEW_MASTER

        assert await monitoring_client._check_connection() is True
        assert monitoring_client._monitor_consecutive_failure_count == 0

    async def test_health_check_failure_counts_when_master_check_fails(
        self,
        monitoring_client: MonitoringValkeyClient,
        sentinel_monitor: _FakeSentinelMonitor,
        mock_sentinel_monitor_client: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_sentinel_monitor_client.check_health.side_effect = TimeoutError("ROLE timed out")
        monkeypatch.setattr(
            sentinel_monitor,
            "check_master",
            AsyncMock(side_effect=ValkeySentinelMasterNotFound("no Sentinel answered")),
        )

        assert await monitoring_client._check_connection() is False
        assert monitoring_client._monitor_consecutive_failure_count == 1

    async def test_watch_task_ends_when_sentinel_monitor_closes(
        self,
        monitoring_client: MonitoringValkeyClient,
        sentinel_monitor: _FakeSentinelMonitor,
    ) -> None:
        await monitoring_client.connect()
        await sentinel_monitor.close()

        watch_task = monitoring_client._watch_task
        assert watch_task is not None
        await asyncio.wait_for(watch_task, timeout=1.0)


# ---- MonitoringValkeyClient.client() context manager with Sentinel ----


class TestMonitoringValkeyClientContextManagerWithSentinel:
    """Tests for the client() context manager with Sentinel-backed operation client."""

    @pytest.fixture
    def mock_sentinel_operation_client(self, sentinel_monitor: _FakeSentinelMonitor) -> AsyncMock:
        return _create_mock_sentinel_client(sentinel_monitor)

    @pytest.fixture
    def mock_sentinel_monitor_client(self, sentinel_monitor: _FakeSentinelMonitor) -> AsyncMock:
        return _create_mock_sentinel_client(sentinel_monitor)

    @pytest.fixture
    def monitoring_client(
        self,
        mock_sentinel_operation_client: AsyncMock,
        mock_sentinel_monitor_client: AsyncMock,
        sentinel_monitor: _FakeSentinelMonitor,
    ) -> MonitoringValkeyClient:
        spec = MonitoringValkeyClientSpec(
            operation_failure_threshold=3,
            monitor_interval=0.01,
        )
        return MonitoringValkeyClient(
            operation_client=mock_sentinel_operation_client,
            monitor_client=mock_sentinel_monitor_client,
            spec=spec,
            sentinel_monitor=sentinel_monitor,
        )

    async def test_client_yields_glide_client(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """client() yields the operation GlideClient from sentinel client."""
        async with monitoring_client.client() as conn:
            result = await conn.ping()
            assert result == b"PONG"

    async def test_client_resets_failure_count_on_success(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        monitoring_client._operation_failure_count = 2
        async with monitoring_client.client() as conn:
            await conn.ping()
        assert monitoring_client._operation_failure_count == 0

    async def test_client_increments_failure_count_on_connection_error(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        with pytest.raises(ConnectionError):
            async with monitoring_client.client() as _conn:
                raise ConnectionError("simulated sentinel connection failure")
        assert monitoring_client._operation_failure_count == 1

    async def test_client_does_not_increment_on_non_connection_error(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        with pytest.raises(ValueError):
            async with monitoring_client.client() as _conn:
                raise ValueError("business logic error")
        assert monitoring_client._operation_failure_count == 0

    async def test_client_requests_reconnect_at_threshold(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """When operation failure threshold is reached, a reconnect is requested."""
        threshold = monitoring_client._operation_failure_threshold

        for _ in range(threshold):
            with pytest.raises(ConnectionError):
                async with monitoring_client.client() as _conn:
                    raise ConnectionError("failure")

        assert monitoring_client._operation_failure_count == 0
        assert monitoring_client._reconnect_requested

    async def test_client_does_not_request_reconnect_below_threshold(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        threshold = monitoring_client._operation_failure_threshold

        for _ in range(threshold - 1):
            with pytest.raises(ConnectionError):
                async with monitoring_client.client() as _conn:
                    raise ConnectionError("failure")

        assert monitoring_client._operation_failure_count == threshold - 1
        assert not monitoring_client._reconnect_requested

    async def test_reconnect_request_wakes_monitor_loop(
        self,
        monitoring_client: MonitoringValkeyClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When client() requests a reconnect, the monitor loop wakes up and reconnects."""
        reconnect_called = asyncio.Event()
        original_reconnect = monitoring_client._reconnect

        async def tracking_reconnect() -> None:
            await original_reconnect()
            reconnect_called.set()

        monkeypatch.setattr(monitoring_client, "_reconnect", tracking_reconnect)

        task = asyncio.create_task(monitoring_client._monitor_connection())
        try:
            # Trigger operation failures to reach threshold
            threshold = monitoring_client._operation_failure_threshold
            for _ in range(threshold):
                with pytest.raises(ConnectionError):
                    async with monitoring_client.client() as _conn:
                        raise ConnectionError("failure")

            # Wait for monitor loop to pick up the reconnect request
            await asyncio.wait_for(reconnect_called.wait(), timeout=1.0)
            assert reconnect_called.is_set()
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def test_client_tracks_not_connected_error_from_sentinel(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """ClientNotConnectedError from sentinel operation client is tracked as connection error."""
        with pytest.raises(ClientNotConnectedError):
            async with monitoring_client.client() as _conn:
                raise ClientNotConnectedError("ValkeySentinelClient is not connected")
        assert monitoring_client._operation_failure_count == 1


# ---- create_valkey_client() factory ----


class TestCreateValkeyClientFactory:
    """Tests for create_valkey_client() factory function producing correct client types."""

    @pytest.fixture
    def sentinel_valkey_target(self) -> ValkeyTarget:
        return ValkeyTarget(
            sentinel=["127.0.0.1:26379", "127.0.0.1:26380"],
            service_name="mymaster",
            password="secret",
            request_timeout=2000,
        )

    @pytest.fixture
    def standalone_valkey_target(self) -> ValkeyTarget:
        return ValkeyTarget(addr="127.0.0.1:6379")

    @pytest.fixture
    def sentinel_valkey_target_with_custom_timeout(self) -> ValkeyTarget:
        return ValkeyTarget(
            sentinel=["127.0.0.1:26379"],
            service_name="mymaster",
            request_timeout=30000,
        )

    def test_creates_sentinel_clients_when_sentinel_config_provided(
        self, sentinel_valkey_target: ValkeyTarget, sentinel_monitor: _FakeSentinelMonitor
    ) -> None:
        client = create_valkey_client(
            sentinel_valkey_target,
            db_id=0,
            human_readable_name="test",
            sentinel_monitor=sentinel_monitor,
        )

        assert isinstance(client, MonitoringValkeyClient)
        assert isinstance(client._operation_client, ValkeySentinelClient)
        assert isinstance(client._monitor_client, ValkeySentinelClient)
        assert client._sentinel_monitor is sentinel_monitor

    def test_raises_when_sentinel_monitor_is_missing(
        self, sentinel_valkey_target: ValkeyTarget
    ) -> None:
        with pytest.raises(ValkeySentinelMonitorNotFound):
            create_valkey_client(sentinel_valkey_target, db_id=0, human_readable_name="test")

    def test_creates_standalone_clients_when_no_sentinel_config(
        self, standalone_valkey_target: ValkeyTarget
    ) -> None:
        client = create_valkey_client(standalone_valkey_target, db_id=0, human_readable_name="test")

        assert isinstance(client, MonitoringValkeyClient)
        assert isinstance(client._operation_client, ValkeyStandaloneClient)
        assert isinstance(client._monitor_client, ValkeyStandaloneClient)
        assert client._sentinel_monitor is None

    def test_monitor_client_uses_fixed_timeout(
        self,
        sentinel_valkey_target_with_custom_timeout: ValkeyTarget,
        sentinel_monitor: _FakeSentinelMonitor,
    ) -> None:
        client = create_valkey_client(
            sentinel_valkey_target_with_custom_timeout,
            db_id=0,
            human_readable_name="test",
            sentinel_monitor=sentinel_monitor,
        )

        assert isinstance(client, MonitoringValkeyClient)
        operation_client = client._operation_client
        monitor_client = client._monitor_client
        assert isinstance(operation_client, ValkeySentinelClient)
        assert isinstance(monitor_client, ValkeySentinelClient)

        assert operation_client._target.request_timeout == 30000
        assert monitor_client._target.request_timeout == 3000


# ---- ValkeySentinelClient.check_health() ----


class TestValkeySentinelClientCheckHealth:
    """Tests for ValkeySentinelClient.check_health() using ROLE."""

    async def test_raises_when_not_connected(self, sentinel_client: ValkeySentinelClient) -> None:
        with pytest.raises(ClientNotConnectedError):
            await sentinel_client.check_health()

    async def test_passes_when_role_is_master(
        self,
        connected_sentinel_client: ValkeySentinelClient,
        mock_glide_client: AsyncMock,
    ) -> None:
        mock_glide_client.custom_command.return_value = [b"master", 0, []]
        await connected_sentinel_client.check_health()
        mock_glide_client.custom_command.assert_called_once_with(["ROLE"])

    async def test_passes_when_role_is_master_as_str(
        self,
        connected_sentinel_client: ValkeySentinelClient,
        mock_glide_client: AsyncMock,
    ) -> None:
        """Tolerate str role in case the Glide decoder returns text."""
        mock_glide_client.custom_command.return_value = ["master", 0, []]
        await connected_sentinel_client.check_health()

    async def test_raises_when_role_is_slave(
        self,
        connected_sentinel_client: ValkeySentinelClient,
        mock_glide_client: AsyncMock,
    ) -> None:
        """Failover demoted the connected node — check_health must raise."""
        mock_glide_client.custom_command.return_value = [
            b"slave",
            b"10.0.0.1",
            6379,
            b"connected",
            0,
        ]
        with pytest.raises(ValkeyRoleMismatchError):
            await connected_sentinel_client.check_health()

    async def test_raises_on_empty_role_response(
        self,
        connected_sentinel_client: ValkeySentinelClient,
        mock_glide_client: AsyncMock,
    ) -> None:
        mock_glide_client.custom_command.return_value = []
        with pytest.raises(ValkeyRoleMismatchError):
            await connected_sentinel_client.check_health()

    async def test_propagates_underlying_command_failure(
        self,
        connected_sentinel_client: ValkeySentinelClient,
        mock_glide_client: AsyncMock,
    ) -> None:
        mock_glide_client.custom_command.side_effect = TimeoutError("ROLE timed out")
        with pytest.raises(TimeoutError):
            await connected_sentinel_client.check_health()


# ---- ValkeyStandaloneClient.check_health() ----


class TestValkeyStandaloneClientCheckHealth:
    """Tests for ValkeyStandaloneClient.check_health()."""

    @pytest.fixture
    def standalone_client(self) -> ValkeyStandaloneClient:
        target = ValkeyStandaloneTarget(address="127.0.0.1:6379")
        return ValkeyStandaloneClient(target=target, db_id=0, human_readable_name="test.standalone")

    async def test_raises_when_not_connected(
        self, standalone_client: ValkeyStandaloneClient
    ) -> None:
        with pytest.raises(ClientNotConnectedError):
            await standalone_client.check_health()

    async def test_passes_when_ping_succeeds(
        self,
        standalone_client: ValkeyStandaloneClient,
        mock_glide_client: AsyncMock,
    ) -> None:
        standalone_client._valkey_client = mock_glide_client
        await standalone_client.check_health()
        mock_glide_client.ping.assert_called_once()

    async def test_propagates_ping_failure(
        self,
        standalone_client: ValkeyStandaloneClient,
        mock_glide_client: AsyncMock,
    ) -> None:
        mock_glide_client.ping.side_effect = TimeoutError("PING timed out")
        standalone_client._valkey_client = mock_glide_client
        with pytest.raises(TimeoutError):
            await standalone_client.check_health()
