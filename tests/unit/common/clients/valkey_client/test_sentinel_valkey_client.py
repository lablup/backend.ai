from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from glide import GlideClient
from glide.exceptions import ClosingError  # type: ignore[import-not-found]

import ai.backend.common.clients.valkey_client.client as client_module
from ai.backend.common.clients.valkey_client.client import (
    MonitoringValkeyClient,
    ValkeySentinelClient,
    ValkeySentinelTarget,
    ValkeyStandaloneClient,
    create_valkey_client,
)
from ai.backend.common.exception import ClientNotConnectedError, ValkeySentinelMasterNotFound
from ai.backend.common.types import ValkeyTarget

INITIAL_MASTER = ("127.0.0.1", 6379)
NEW_MASTER = ("10.0.0.2", 6379)


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
    return client


@pytest.fixture
def mock_sentinel() -> MagicMock:
    sentinel = MagicMock()
    sentinel.discover_master = AsyncMock(return_value=INITIAL_MASTER)
    return sentinel


@pytest.fixture
def sentinel_client(
    sentinel_target: ValkeySentinelTarget,
    mock_sentinel: MagicMock,
) -> ValkeySentinelClient:
    client = ValkeySentinelClient(
        target=sentinel_target,
        db_id=0,
        human_readable_name="test.sentinel",
    )
    client._sentinel = mock_sentinel
    return client


@pytest.fixture
def connected_sentinel_client(
    sentinel_client: ValkeySentinelClient,
    mock_glide_client: AsyncMock,
) -> ValkeySentinelClient:
    sentinel_client._valkey_client = mock_glide_client
    sentinel_client._master_address = INITIAL_MASTER
    return sentinel_client


def _create_mock_sentinel_client() -> AsyncMock:
    client = AsyncMock(spec=ValkeySentinelClient)
    client.need_reconnect = AsyncMock(return_value=False)
    client.ping = AsyncMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.client = MagicMock()
    return client


# ---- ValkeySentinelClient.need_reconnect() ----


class TestValkeySentinelClientNeedReconnect:
    """Tests for ValkeySentinelClient.need_reconnect() detecting master address changes."""

    async def test_returns_true_when_client_is_none(
        self, sentinel_client: ValkeySentinelClient
    ) -> None:
        assert await sentinel_client.need_reconnect() is True

    async def test_returns_true_when_master_address_is_none(
        self,
        sentinel_client: ValkeySentinelClient,
        mock_glide_client: AsyncMock,
    ) -> None:
        sentinel_client._valkey_client = mock_glide_client
        sentinel_client._master_address = None
        assert await sentinel_client.need_reconnect() is True

    async def test_returns_true_when_master_address_changed(
        self,
        connected_sentinel_client: ValkeySentinelClient,
        mock_sentinel: MagicMock,
    ) -> None:
        mock_sentinel.discover_master.return_value = NEW_MASTER
        assert await connected_sentinel_client.need_reconnect() is True

    async def test_returns_false_when_master_address_unchanged(
        self, connected_sentinel_client: ValkeySentinelClient
    ) -> None:
        assert await connected_sentinel_client.need_reconnect() is False

    async def test_returns_false_when_discovery_fails(
        self,
        connected_sentinel_client: ValkeySentinelClient,
        mock_sentinel: MagicMock,
    ) -> None:
        """When Sentinel discovery fails, keep the current connection (conservative strategy)."""
        mock_sentinel.discover_master.side_effect = ConnectionError("Sentinel unreachable")
        assert await connected_sentinel_client.need_reconnect() is False


# ---- ValkeySentinelClient._get_master_address() ----


class TestValkeySentinelClientGetMasterAddress:
    """Tests for ValkeySentinelClient._get_master_address() Sentinel discovery."""

    async def test_returns_address_on_success(self, sentinel_client: ValkeySentinelClient) -> None:
        result = await sentinel_client._get_master_address()
        assert result == INITIAL_MASTER

    async def test_returns_none_on_discovery_failure(
        self,
        sentinel_client: ValkeySentinelClient,
        mock_sentinel: MagicMock,
    ) -> None:
        mock_sentinel.discover_master.side_effect = ConnectionError("All sentinels down")
        result = await sentinel_client._get_master_address()
        assert result is None


# ---- ValkeySentinelClient.connect() / disconnect() ----


class TestValkeySentinelClientConnect:
    """Tests for ValkeySentinelClient.connect() lifecycle."""

    async def test_raises_master_not_found_when_discovery_fails(
        self,
        sentinel_client: ValkeySentinelClient,
        mock_sentinel: MagicMock,
    ) -> None:
        mock_sentinel.discover_master.side_effect = ConnectionError("Sentinel unreachable")
        with pytest.raises(ValkeySentinelMasterNotFound):
            await sentinel_client.connect()

    async def test_creates_client_on_successful_discovery(
        self,
        sentinel_client: ValkeySentinelClient,
        mock_glide_client: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(GlideClient, "create", AsyncMock(return_value=mock_glide_client))
        await sentinel_client.connect()

        assert sentinel_client._valkey_client is mock_glide_client
        assert sentinel_client._master_address == INITIAL_MASTER

    async def test_skips_if_already_connected(
        self,
        connected_sentinel_client: ValkeySentinelClient,
        mock_sentinel: MagicMock,
    ) -> None:
        mock_sentinel.discover_master.reset_mock()
        await connected_sentinel_client.connect()
        mock_sentinel.discover_master.assert_not_called()

    async def test_disconnect_closes_client(
        self,
        connected_sentinel_client: ValkeySentinelClient,
        mock_glide_client: AsyncMock,
    ) -> None:
        await connected_sentinel_client.disconnect()

        mock_glide_client.close.assert_called_once()
        assert connected_sentinel_client._valkey_client is None


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
    def mock_sentinel_operation_client(self) -> AsyncMock:
        return _create_mock_sentinel_client()

    @pytest.fixture
    def mock_sentinel_monitor_client(self) -> AsyncMock:
        return _create_mock_sentinel_client()

    @pytest.fixture
    def monitoring_client(
        self,
        mock_sentinel_operation_client: AsyncMock,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> MonitoringValkeyClient:
        return MonitoringValkeyClient(
            operation_client=mock_sentinel_operation_client,
            monitor_client=mock_sentinel_monitor_client,
        )

    # -- _check_connection --

    async def test_check_connection_triggers_reconnect_on_master_change(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        mock_sentinel_monitor_client.need_reconnect.return_value = True
        assert await monitoring_client._check_connection() is True

    async def test_check_connection_no_reconnect_when_stable(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        assert await monitoring_client._check_connection() is False

    # -- _check_ping --

    @pytest.mark.parametrize(
        "exception",
        [
            ClosingError("Connection closed"),
            ClientNotConnectedError("Not connected"),
        ],
        ids=["ClosingError", "ClientNotConnectedError"],
    )
    async def test_check_ping_returns_true_on_reconnectable_exception(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
        exception: Exception,
    ) -> None:
        """Reconnectable exceptions trigger immediate reconnection."""
        mock_sentinel_monitor_client.ping.side_effect = exception

        assert await monitoring_client._check_ping() is True
        assert monitoring_client._consecutive_failure_count == 0

    async def test_check_ping_accumulates_failures_until_threshold(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        """General exceptions accumulate; reconnect triggers at threshold (3)."""
        mock_sentinel_monitor_client.ping.side_effect = TimeoutError("Timed out")

        assert await monitoring_client._check_ping() is False
        assert monitoring_client._consecutive_failure_count == 1

        assert await monitoring_client._check_ping() is False
        assert monitoring_client._consecutive_failure_count == 2

        # Third failure: threshold reached → reconnect
        assert await monitoring_client._check_ping() is True
        assert monitoring_client._consecutive_failure_count == 0

    async def test_check_ping_resets_failure_count_on_success(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        """Successful ping resets the consecutive failure counter."""
        mock_sentinel_monitor_client.ping.side_effect = TimeoutError("Timed out")

        await monitoring_client._check_ping()
        await monitoring_client._check_ping()
        assert monitoring_client._consecutive_failure_count == 2

        # Recovery: ping succeeds
        mock_sentinel_monitor_client.ping.side_effect = None
        mock_sentinel_monitor_client.ping.return_value = None

        assert await monitoring_client._check_ping() is False
        assert monitoring_client._consecutive_failure_count == 0

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

    # -- need_reconnect delegation --

    async def test_need_reconnect_delegates_to_monitor_client(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        mock_sentinel_monitor_client.need_reconnect.return_value = True
        assert await monitoring_client.need_reconnect() is True

        mock_sentinel_monitor_client.need_reconnect.return_value = False
        assert await monitoring_client.need_reconnect() is False

    # -- monitor loop --

    async def test_monitor_loop_calls_reconnect_when_check_connection_returns_true(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The monitor loop triggers _reconnect when _check_connection returns True."""
        call_count = 0

        async def fake_need_reconnect() -> bool:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return True
            raise asyncio.CancelledError

        mock_sentinel_monitor_client.need_reconnect = fake_need_reconnect

        mock_reconnect = AsyncMock()
        monkeypatch.setattr(monitoring_client, "_reconnect", mock_reconnect)
        monkeypatch.setattr(client_module, "_DEFAULT_MONITOR_INTERVAL", 0.01)

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

        async def fake_need_reconnect() -> bool:
            nonlocal check_count
            check_count += 1
            if check_count <= 2:
                return True
            raise asyncio.CancelledError

        mock_sentinel_monitor_client.need_reconnect = fake_need_reconnect

        reconnect_call_count = 0

        async def failing_then_succeeding_reconnect() -> None:
            nonlocal reconnect_call_count
            reconnect_call_count += 1
            if reconnect_call_count == 1:
                raise ConnectionError("Sentinel temporarily unavailable")

        monkeypatch.setattr(monitoring_client, "_reconnect", failing_then_succeeding_reconnect)
        monkeypatch.setattr(client_module, "_DEFAULT_MONITOR_INTERVAL", 0.01)

        task = asyncio.create_task(monitoring_client._monitor_connection())
        await asyncio.sleep(0.2)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert reconnect_call_count == 2


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
        self, sentinel_valkey_target: ValkeyTarget
    ) -> None:
        client = create_valkey_client(sentinel_valkey_target, db_id=0, human_readable_name="test")

        assert isinstance(client, MonitoringValkeyClient)
        assert isinstance(client._operation_client, ValkeySentinelClient)
        assert isinstance(client._monitor_client, ValkeySentinelClient)

    def test_creates_standalone_clients_when_no_sentinel_config(
        self, standalone_valkey_target: ValkeyTarget
    ) -> None:
        client = create_valkey_client(standalone_valkey_target, db_id=0, human_readable_name="test")

        assert isinstance(client, MonitoringValkeyClient)
        assert isinstance(client._operation_client, ValkeyStandaloneClient)
        assert isinstance(client._monitor_client, ValkeyStandaloneClient)

    def test_monitor_client_uses_fixed_timeout(
        self, sentinel_valkey_target_with_custom_timeout: ValkeyTarget
    ) -> None:
        client = create_valkey_client(
            sentinel_valkey_target_with_custom_timeout, db_id=0, human_readable_name="test"
        )

        assert isinstance(client, MonitoringValkeyClient)
        operation_client = client._operation_client
        monitor_client = client._monitor_client
        assert isinstance(operation_client, ValkeySentinelClient)
        assert isinstance(monitor_client, ValkeySentinelClient)

        assert operation_client._target.request_timeout == 30000
        assert monitor_client._target.request_timeout == 3000
