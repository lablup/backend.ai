from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from glide.exceptions import ClosingError  # type: ignore[import-not-found]

from ai.backend.common.clients.valkey_client.client import (
    MonitoringValkeyClient,
    ValkeySentinelClient,
    ValkeySentinelTarget,
    ValkeyStandaloneClient,
    create_valkey_client,
)
from ai.backend.common.exception import ClientNotConnectedError, ValkeySentinelMasterNotFound
from ai.backend.common.types import ValkeyTarget


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
    sentinel.discover_master = AsyncMock(return_value=("127.0.0.1", 6379))
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
    sentinel_client._master_address = ("127.0.0.1", 6379)
    return sentinel_client


class TestValkeySentinelClientNeedReconnect:
    """Tests for ValkeySentinelClient.need_reconnect() detecting master address changes."""

    async def test_returns_true_when_client_is_none(
        self, sentinel_client: ValkeySentinelClient
    ) -> None:
        # _valkey_client is None by default (not connected)
        assert await sentinel_client.need_reconnect() is True

    async def test_returns_true_when_master_address_is_none(
        self,
        sentinel_client: ValkeySentinelClient,
        mock_glide_client: AsyncMock,
    ) -> None:
        # Simulate a state where client exists but master_address was never set
        sentinel_client._valkey_client = mock_glide_client
        sentinel_client._master_address = None

        assert await sentinel_client.need_reconnect() is True

    async def test_returns_true_when_master_address_changed(
        self,
        connected_sentinel_client: ValkeySentinelClient,
        mock_sentinel: MagicMock,
    ) -> None:
        # Sentinel now reports a different master (failover happened)
        mock_sentinel.discover_master.return_value = ("new-host", 6379)

        assert await connected_sentinel_client.need_reconnect() is True

    async def test_returns_false_when_master_address_unchanged(
        self, connected_sentinel_client: ValkeySentinelClient
    ) -> None:
        # mock_sentinel already returns ("127.0.0.1", 6379) which matches _master_address
        assert await connected_sentinel_client.need_reconnect() is False

    async def test_returns_false_when_discovery_fails(
        self,
        connected_sentinel_client: ValkeySentinelClient,
        mock_sentinel: MagicMock,
    ) -> None:
        """When Sentinel discovery fails, keep the current connection (conservative strategy)."""
        mock_sentinel.discover_master.side_effect = ConnectionError("Sentinel unreachable")

        # _get_master_address returns None on failure → need_reconnect returns False
        assert await connected_sentinel_client.need_reconnect() is False


class TestValkeySentinelClientGetMasterAddress:
    """Tests for ValkeySentinelClient._get_master_address() Sentinel discovery."""

    async def test_returns_address_on_success(
        self,
        sentinel_client: ValkeySentinelClient,
        mock_sentinel: MagicMock,
    ) -> None:
        mock_sentinel.discover_master.return_value = ("10.0.0.1", 6379)

        result = await sentinel_client._get_master_address()
        assert result == ("10.0.0.1", 6379)

    async def test_returns_none_on_discovery_failure(
        self,
        sentinel_client: ValkeySentinelClient,
        mock_sentinel: MagicMock,
    ) -> None:
        mock_sentinel.discover_master.side_effect = ConnectionError("All sentinels down")

        result = await sentinel_client._get_master_address()
        assert result is None


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
    ) -> None:
        with patch(
            "ai.backend.common.clients.valkey_client.client.GlideClient.create",
            new_callable=AsyncMock,
            return_value=mock_glide_client,
        ):
            await sentinel_client.connect()

        assert sentinel_client._valkey_client is mock_glide_client
        assert sentinel_client._master_address == ("127.0.0.1", 6379)

    async def test_skips_if_already_connected(
        self,
        connected_sentinel_client: ValkeySentinelClient,
        mock_sentinel: MagicMock,
    ) -> None:
        # connect() should return early without calling discover_master
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


def _create_mock_sentinel_client() -> AsyncMock:
    client = AsyncMock(spec=ValkeySentinelClient)
    client.need_reconnect = AsyncMock(return_value=False)
    client.ping = AsyncMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.client = MagicMock()
    return client


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

    async def test_check_connection_triggers_reconnect_on_master_change(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        """When Sentinel reports master address change, _check_connection returns True."""
        mock_sentinel_monitor_client.need_reconnect.return_value = True

        result = await monitoring_client._check_connection()
        assert result is True

    async def test_check_connection_no_reconnect_when_stable(
        self,
        monitoring_client: MonitoringValkeyClient,
    ) -> None:
        """When ping succeeds and master is unchanged, no reconnect needed."""
        result = await monitoring_client._check_connection()
        assert result is False

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

        result = await monitoring_client._check_ping()
        assert result is True
        assert monitoring_client._consecutive_failure_count == 0

    async def test_check_ping_accumulates_failures_until_threshold(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        """General exceptions accumulate; reconnect triggers at threshold (3)."""
        mock_sentinel_monitor_client.ping.side_effect = TimeoutError("Timed out")

        # First two failures: no reconnect yet
        assert await monitoring_client._check_ping() is False
        assert monitoring_client._consecutive_failure_count == 1

        assert await monitoring_client._check_ping() is False
        assert monitoring_client._consecutive_failure_count == 2

        # Third failure: threshold reached → reconnect
        assert await monitoring_client._check_ping() is True
        assert monitoring_client._consecutive_failure_count == 0  # reset after threshold

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

        # Now ping succeeds
        mock_sentinel_monitor_client.ping.side_effect = None
        mock_sentinel_monitor_client.ping.return_value = None

        result = await monitoring_client._check_ping()
        assert result is False
        assert monitoring_client._consecutive_failure_count == 0

    async def test_reconnect_disconnects_and_reconnects_both_clients(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_operation_client: AsyncMock,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        """_reconnect() disconnects both clients then reconnects them."""
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
        """_reconnect() continues reconnection even if disconnect raises."""
        mock_sentinel_monitor_client.disconnect.side_effect = ConnectionError("Already closed")
        mock_sentinel_operation_client.disconnect.side_effect = ConnectionError("Already closed")

        await monitoring_client._reconnect()

        # Both connect calls should still happen despite disconnect errors
        mock_sentinel_operation_client.connect.assert_called_once()
        mock_sentinel_monitor_client.connect.assert_called_once()

    async def test_need_reconnect_delegates_to_monitor_client(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        """MonitoringValkeyClient.need_reconnect() delegates to the monitor client."""
        mock_sentinel_monitor_client.need_reconnect.return_value = True
        assert await monitoring_client.need_reconnect() is True

        mock_sentinel_monitor_client.need_reconnect.return_value = False
        assert await monitoring_client.need_reconnect() is False

    async def test_monitor_loop_calls_reconnect_when_check_connection_returns_true(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        """The monitor loop triggers _reconnect when _check_connection returns True."""
        call_count = 0

        # Make master change detected on first check, then stop via CancelledError
        async def fake_need_reconnect() -> bool:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return True
            raise asyncio.CancelledError

        mock_sentinel_monitor_client.need_reconnect = fake_need_reconnect

        with (
            patch.object(
                monitoring_client,
                "_reconnect",
                new_callable=AsyncMock,
            ) as mock_reconnect,
            patch(
                "ai.backend.common.clients.valkey_client.client._DEFAULT_MONITOR_INTERVAL",
                0.01,
            ),
        ):
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
    ) -> None:
        """Monitor loop must not die when _reconnect() raises; it should log and retry."""
        check_count = 0

        async def fake_need_reconnect() -> bool:
            nonlocal check_count
            check_count += 1
            if check_count <= 2:
                # First two cycles: master changed → trigger reconnect
                return True
            # Third cycle: cancel to end test
            raise asyncio.CancelledError

        mock_sentinel_monitor_client.need_reconnect = fake_need_reconnect

        reconnect_call_count = 0

        async def failing_then_succeeding_reconnect() -> None:
            nonlocal reconnect_call_count
            reconnect_call_count += 1
            if reconnect_call_count == 1:
                raise ConnectionError("Sentinel temporarily unavailable")
            # Second call succeeds

        with (
            patch.object(
                monitoring_client,
                "_reconnect",
                side_effect=failing_then_succeeding_reconnect,
            ),
            patch(
                "ai.backend.common.clients.valkey_client.client._DEFAULT_MONITOR_INTERVAL",
                0.01,
            ),
        ):
            task = asyncio.create_task(monitoring_client._monitor_connection())
            await asyncio.sleep(0.2)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # The loop survived the first reconnect failure and retried successfully
        assert reconnect_call_count == 2

    async def test_failover_reconnects_to_new_master(
        self,
        sentinel_target: ValkeySentinelTarget,
        mock_sentinel: MagicMock,
    ) -> None:
        """Full failover flow: connected to master A → detect change → reconnect → master B."""
        old_master_client = AsyncMock()
        old_master_client.ping = AsyncMock(return_value=b"PONG")
        old_master_client.close = AsyncMock()

        new_master_client = AsyncMock()
        new_master_client.ping = AsyncMock(return_value=b"PONG")
        new_master_client.close = AsyncMock()

        # Phase 1: initial connect to master A
        mock_sentinel.discover_master.return_value = ("master-a", 6379)

        operation_client = ValkeySentinelClient(
            target=sentinel_target,
            db_id=0,
            human_readable_name="test.op",
        )
        operation_client._sentinel = mock_sentinel

        with patch(
            "ai.backend.common.clients.valkey_client.client.GlideClient.create",
            new_callable=AsyncMock,
            return_value=old_master_client,
        ):
            await operation_client.connect()

        assert operation_client._master_address == ("master-a", 6379)
        assert operation_client._valkey_client is old_master_client

        # Phase 2: failover happens — sentinel now reports master B
        mock_sentinel.discover_master.return_value = ("master-b", 6379)
        assert await operation_client.need_reconnect() is True

        # Phase 3: reconnect — disconnect old, connect to new master
        await operation_client.disconnect()
        old_master_client.close.assert_called_once()

        with patch(
            "ai.backend.common.clients.valkey_client.client.GlideClient.create",
            new_callable=AsyncMock,
            return_value=new_master_client,
        ):
            await operation_client.connect()

        assert operation_client._master_address == ("master-b", 6379)
        assert operation_client._valkey_client is new_master_client


class TestCreateValkeyClientFactory:
    """Tests for create_valkey_client() factory function producing correct client types."""

    def test_creates_sentinel_clients_when_sentinel_config_provided(self) -> None:
        target = ValkeyTarget(
            sentinel=["127.0.0.1:26379", "127.0.0.1:26380"],
            service_name="mymaster",
            password="secret",
            request_timeout=2000,
        )

        client = create_valkey_client(target, db_id=0, human_readable_name="test")

        assert isinstance(client, MonitoringValkeyClient)
        assert isinstance(client._operation_client, ValkeySentinelClient)
        assert isinstance(client._monitor_client, ValkeySentinelClient)

    def test_creates_standalone_clients_when_no_sentinel_config(self) -> None:
        target = ValkeyTarget(addr="127.0.0.1:6379")

        client = create_valkey_client(target, db_id=0, human_readable_name="test")

        assert isinstance(client, MonitoringValkeyClient)
        assert isinstance(client._operation_client, ValkeyStandaloneClient)
        assert isinstance(client._monitor_client, ValkeyStandaloneClient)

    def test_monitor_client_uses_fixed_timeout(self) -> None:
        target = ValkeyTarget(
            sentinel=["127.0.0.1:26379"],
            service_name="mymaster",
            request_timeout=30000,
        )

        client = create_valkey_client(target, db_id=0, human_readable_name="test")

        assert isinstance(client, MonitoringValkeyClient)
        operation_client = client._operation_client
        monitor_client = client._monitor_client
        assert isinstance(operation_client, ValkeySentinelClient)
        assert isinstance(monitor_client, ValkeySentinelClient)

        # Operation client keeps user-specified timeout
        assert operation_client._target.request_timeout == 30000

        # Monitor client uses fixed 3-second timeout regardless of user config
        assert monitor_client._target.request_timeout == 3000
