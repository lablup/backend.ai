from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from glide.exceptions import ClosingError  # type: ignore[import-not-found]

from ai.backend.common.clients.valkey_client.client import (
    MonitoringValkeyClient,
    ValkeySentinelClient,
    ValkeySentinelTarget,
)
from ai.backend.common.exception import ClientNotConnectedError, ValkeySentinelMasterNotFound


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


class TestValkeySentinelClientNeedReconnect:
    """Tests for ValkeySentinelClient.need_reconnect() detecting master address changes."""

    async def test_returns_true_when_client_is_none(
        self, sentinel_target: ValkeySentinelTarget
    ) -> None:
        sentinel_client = ValkeySentinelClient(
            target=sentinel_target,
            db_id=0,
            human_readable_name="test.sentinel",
        )
        # _valkey_client is None by default (not connected)
        assert await sentinel_client.need_reconnect() is True

    async def test_returns_true_when_master_address_is_none(
        self,
        sentinel_target: ValkeySentinelTarget,
        mock_glide_client: AsyncMock,
    ) -> None:
        sentinel_client = ValkeySentinelClient(
            target=sentinel_target,
            db_id=0,
            human_readable_name="test.sentinel",
        )
        # Simulate a state where client exists but master_address was never set
        sentinel_client._valkey_client = mock_glide_client
        sentinel_client._master_address = None

        assert await sentinel_client.need_reconnect() is True

    async def test_returns_true_when_master_address_changed(
        self,
        sentinel_target: ValkeySentinelTarget,
        mock_glide_client: AsyncMock,
    ) -> None:
        sentinel_client = ValkeySentinelClient(
            target=sentinel_target,
            db_id=0,
            human_readable_name="test.sentinel",
        )
        sentinel_client._valkey_client = mock_glide_client
        sentinel_client._master_address = ("old-host", 6379)

        # Sentinel now reports a different master (failover happened)
        sentinel_client._sentinel = MagicMock()
        sentinel_client._sentinel.discover_master = AsyncMock(
            return_value=("new-host", 6379),
        )

        assert await sentinel_client.need_reconnect() is True

    async def test_returns_false_when_master_address_unchanged(
        self,
        sentinel_target: ValkeySentinelTarget,
        mock_glide_client: AsyncMock,
    ) -> None:
        sentinel_client = ValkeySentinelClient(
            target=sentinel_target,
            db_id=0,
            human_readable_name="test.sentinel",
        )
        sentinel_client._valkey_client = mock_glide_client
        sentinel_client._master_address = ("same-host", 6379)

        sentinel_client._sentinel = MagicMock()
        sentinel_client._sentinel.discover_master = AsyncMock(
            return_value=("same-host", 6379),
        )

        assert await sentinel_client.need_reconnect() is False

    async def test_returns_false_when_discovery_fails(
        self,
        sentinel_target: ValkeySentinelTarget,
        mock_glide_client: AsyncMock,
    ) -> None:
        """When Sentinel discovery fails, keep the current connection (conservative strategy)."""
        sentinel_client = ValkeySentinelClient(
            target=sentinel_target,
            db_id=0,
            human_readable_name="test.sentinel",
        )
        sentinel_client._valkey_client = mock_glide_client
        sentinel_client._master_address = ("current-host", 6379)

        sentinel_client._sentinel = MagicMock()
        sentinel_client._sentinel.discover_master = AsyncMock(
            side_effect=ConnectionError("Sentinel unreachable"),
        )

        # _get_master_address returns None on failure → need_reconnect returns False
        assert await sentinel_client.need_reconnect() is False


class TestValkeySentinelClientGetMasterAddress:
    """Tests for ValkeySentinelClient._get_master_address() Sentinel discovery."""

    async def test_returns_address_on_success(self, sentinel_target: ValkeySentinelTarget) -> None:
        sentinel_client = ValkeySentinelClient(
            target=sentinel_target,
            db_id=0,
            human_readable_name="test.sentinel",
        )
        sentinel_client._sentinel = MagicMock()
        sentinel_client._sentinel.discover_master = AsyncMock(
            return_value=("10.0.0.1", 6379),
        )

        result = await sentinel_client._get_master_address()
        assert result == ("10.0.0.1", 6379)

    async def test_returns_none_on_discovery_failure(
        self, sentinel_target: ValkeySentinelTarget
    ) -> None:
        sentinel_client = ValkeySentinelClient(
            target=sentinel_target,
            db_id=0,
            human_readable_name="test.sentinel",
        )
        sentinel_client._sentinel = MagicMock()
        sentinel_client._sentinel.discover_master = AsyncMock(
            side_effect=ConnectionError("All sentinels down"),
        )

        result = await sentinel_client._get_master_address()
        assert result is None


class TestValkeySentinelClientConnect:
    """Tests for ValkeySentinelClient.connect() lifecycle."""

    async def test_raises_master_not_found_when_discovery_fails(
        self, sentinel_target: ValkeySentinelTarget
    ) -> None:
        sentinel_client = ValkeySentinelClient(
            target=sentinel_target,
            db_id=0,
            human_readable_name="test.sentinel",
        )
        sentinel_client._sentinel = MagicMock()
        sentinel_client._sentinel.discover_master = AsyncMock(
            side_effect=ConnectionError("Sentinel unreachable"),
        )

        with pytest.raises(ValkeySentinelMasterNotFound):
            await sentinel_client.connect()

    async def test_creates_client_on_successful_discovery(
        self,
        sentinel_target: ValkeySentinelTarget,
        mock_glide_client: AsyncMock,
    ) -> None:
        sentinel_client = ValkeySentinelClient(
            target=sentinel_target,
            db_id=0,
            human_readable_name="test.sentinel",
        )
        sentinel_client._sentinel = MagicMock()
        sentinel_client._sentinel.discover_master = AsyncMock(
            return_value=("10.0.0.1", 6379),
        )

        with patch(
            "ai.backend.common.clients.valkey_client.client.GlideClient.create",
            new_callable=AsyncMock,
            return_value=mock_glide_client,
        ):
            await sentinel_client.connect()

        assert sentinel_client._valkey_client is mock_glide_client
        assert sentinel_client._master_address == ("10.0.0.1", 6379)

    async def test_skips_if_already_connected(
        self,
        sentinel_target: ValkeySentinelTarget,
        mock_glide_client: AsyncMock,
    ) -> None:
        sentinel_client = ValkeySentinelClient(
            target=sentinel_target,
            db_id=0,
            human_readable_name="test.sentinel",
        )
        sentinel_client._valkey_client = mock_glide_client

        sentinel_client._sentinel = MagicMock()
        sentinel_client._sentinel.discover_master = AsyncMock()

        # connect() should return early without calling discover_master
        await sentinel_client.connect()
        sentinel_client._sentinel.discover_master.assert_not_called()

    async def test_disconnect_closes_client(
        self,
        sentinel_target: ValkeySentinelTarget,
        mock_glide_client: AsyncMock,
    ) -> None:
        sentinel_client = ValkeySentinelClient(
            target=sentinel_target,
            db_id=0,
            human_readable_name="test.sentinel",
        )
        sentinel_client._valkey_client = mock_glide_client

        await sentinel_client.disconnect()

        mock_glide_client.close.assert_called_once()
        assert sentinel_client._valkey_client is None


class TestValkeySentinelClientPing:
    """Tests for ValkeySentinelClient.ping()."""

    async def test_raises_when_not_connected(self, sentinel_target: ValkeySentinelTarget) -> None:
        sentinel_client = ValkeySentinelClient(
            target=sentinel_target,
            db_id=0,
            human_readable_name="test.sentinel",
        )

        with pytest.raises(ClientNotConnectedError):
            await sentinel_client.ping()

    async def test_pings_successfully_when_connected(
        self,
        sentinel_target: ValkeySentinelTarget,
        mock_glide_client: AsyncMock,
    ) -> None:
        sentinel_client = ValkeySentinelClient(
            target=sentinel_target,
            db_id=0,
            human_readable_name="test.sentinel",
        )
        sentinel_client._valkey_client = mock_glide_client

        await sentinel_client.ping()
        mock_glide_client.ping.assert_called_once()


class TestMonitoringValkeyClientWithSentinel:
    """Tests for MonitoringValkeyClient wrapping ValkeySentinelClient (mock-based)."""

    @pytest.fixture
    def mock_sentinel_operation_client(self) -> AsyncMock:
        client = AsyncMock(spec=ValkeySentinelClient)
        client.need_reconnect = AsyncMock(return_value=False)
        client.ping = AsyncMock()
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.client = MagicMock()
        return client

    @pytest.fixture
    def mock_sentinel_monitor_client(self) -> AsyncMock:
        client = AsyncMock(spec=ValkeySentinelClient)
        client.need_reconnect = AsyncMock(return_value=False)
        client.ping = AsyncMock()
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.client = MagicMock()
        return client

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

    async def test_check_ping_returns_true_on_closing_error(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        """ClosingError triggers immediate reconnection."""
        mock_sentinel_monitor_client.ping.side_effect = ClosingError("Connection closed")

        result = await monitoring_client._check_ping()
        assert result is True
        assert monitoring_client._consecutive_failure_count == 0

    async def test_check_ping_returns_true_on_client_not_connected_error(
        self,
        monitoring_client: MonitoringValkeyClient,
        mock_sentinel_monitor_client: AsyncMock,
    ) -> None:
        """ClientNotConnectedError triggers immediate reconnection."""
        mock_sentinel_monitor_client.ping.side_effect = ClientNotConnectedError(
            "Not connected",
        )

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
