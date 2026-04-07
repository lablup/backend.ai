from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import cast

import pytest

from ai.backend.common.clients.valkey_client.client import (
    _VALKEY_CONNECTION_ERRORS,
    MonitoringValkeyClient,
    create_valkey_client,
)
from ai.backend.common.defs import REDIS_STREAM_DB
from ai.backend.common.exception import ClientNotConnectedError
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ValkeyTarget


@pytest.mark.redis
class TestMonitoringValkeyClient:
    @pytest.fixture
    async def monitoring_client(
        self, redis_container: tuple[str, HostPortPairModel]
    ) -> AsyncIterator[MonitoringValkeyClient]:
        hostport_pair: HostPortPairModel = redis_container[1]
        valkey_target = ValkeyTarget(addr=hostport_pair.address)
        client = cast(
            MonitoringValkeyClient,
            create_valkey_client(
                valkey_target,
                db_id=REDIS_STREAM_DB,
                human_readable_name="test.monitoring",
            ),
        )
        await client.connect()
        try:
            yield client
        finally:
            await client.disconnect()

    async def test_connect_disconnect_reconnect(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """Test basic connect/disconnect/reconnect lifecycle"""
        # Client should be connected
        await monitoring_client.ping()

        # Disconnect
        await monitoring_client.disconnect()

        # Reconnect
        await monitoring_client.connect()

        # Should work after reconnection
        await monitoring_client.ping()

    async def test_operation_client_independence(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """Test that operation client and monitor client work independently"""
        # Both clients should be operational after connect
        await monitoring_client.ping()

        # Operation client should be accessible via context manager
        async with monitoring_client.client() as conn:
            result = await conn.ping()
            assert result == b"PONG"

    async def test_reconnect_on_connection_error(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """Test reconnection logic when connection errors occur"""
        # Force disconnect both clients to simulate connection loss
        await monitoring_client._operation_client.disconnect()
        await monitoring_client._monitor_client.disconnect()

        # Trigger reconnect
        await monitoring_client._reconnect()

        # Should be operational after reconnect
        await monitoring_client.ping()

    async def test_monitor_client_separation(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """Test that monitor client is separate from operation client"""
        # Verify both clients exist
        assert monitoring_client._operation_client is not None
        assert monitoring_client._monitor_client is not None

        # Verify they are different instances
        assert monitoring_client._operation_client is not monitoring_client._monitor_client

        # Verify ping uses monitor client
        await monitoring_client.ping()

    async def test_monitor_task_lifecycle(self, monitoring_client: MonitoringValkeyClient) -> None:
        """Test that monitor task is created and cancelled properly"""
        # Monitor task should be running after connect
        assert monitoring_client._monitor_task is not None
        assert not monitoring_client._monitor_task.done()

        # Allow monitor to run at least once
        await asyncio.sleep(0.1)

        # Disconnect should cancel monitor task
        await monitoring_client.disconnect()
        assert monitoring_client._monitor_task is None

    async def test_monitor_task_cancellation_no_error_log(
        self,
        redis_container: tuple[str, HostPortPairModel],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that CancelledError during shutdown does not produce error logs (BA-3593)"""
        hostport_pair: HostPortPairModel = redis_container[1]
        valkey_target = ValkeyTarget(addr=hostport_pair.address)
        client = cast(
            MonitoringValkeyClient,
            create_valkey_client(
                valkey_target,
                db_id=REDIS_STREAM_DB,
                human_readable_name="test.cancellation",
            ),
        )

        await client.connect()

        # Ensure monitor task is running
        assert client._monitor_task is not None
        assert not client._monitor_task.done()

        # Allow monitor to start its sleep cycle
        await asyncio.sleep(0.1)

        # Clear any previous logs
        caplog.clear()

        # Disconnect - this should cancel the monitor task without error logs
        with caplog.at_level(logging.ERROR):
            await client.disconnect()

        # Verify no error logs about CancelledError
        error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
        cancelled_error_logs = [
            record
            for record in error_logs
            if "CancelledError" in str(record.message)
            or "Error in Valkey connection monitor" in str(record.message)
        ]
        assert len(cancelled_error_logs) == 0, (
            f"Unexpected error logs during cancellation: {[r.message for r in cancelled_error_logs]}"
        )

    async def test_monitor_task_external_cancellation_no_error_log(
        self,
        redis_container: tuple[str, HostPortPairModel],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that external task cancellation (simulating shutdown) does not produce error logs (BA-3593)"""
        hostport_pair: HostPortPairModel = redis_container[1]
        valkey_target = ValkeyTarget(addr=hostport_pair.address)
        client = cast(
            MonitoringValkeyClient,
            create_valkey_client(
                valkey_target,
                db_id=REDIS_STREAM_DB,
                human_readable_name="test.external_cancellation",
            ),
        )

        await client.connect()

        # Ensure monitor task is running
        monitor_task = client._monitor_task
        assert monitor_task is not None
        assert not monitor_task.done()

        # Allow monitor to start its sleep cycle
        await asyncio.sleep(0.1)

        # Clear any previous logs
        caplog.clear()

        # Simulate external cancellation (like aiotools server shutdown)
        # This is the scenario where cancellation happens BEFORE disconnect() is called
        with caplog.at_level(logging.ERROR):
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass  # Expected

        # Verify no error logs about CancelledError
        error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
        cancelled_error_logs = [
            record
            for record in error_logs
            if "CancelledError" in str(record.message)
            or "Error in Valkey connection monitor" in str(record.message)
        ]
        assert len(cancelled_error_logs) == 0, (
            f"Unexpected error logs during external cancellation: {[r.message for r in cancelled_error_logs]}"
        )

        # Cleanup - manually close the clients since we bypassed disconnect()
        client._monitor_task = None
        await client._monitor_client.disconnect()
        await client._operation_client.disconnect()


@pytest.mark.redis
class TestMonitoringValkeyClientContextManager:
    """Tests for the client() context manager and retry-based disconnection logic."""

    @pytest.fixture
    async def monitoring_client(
        self, redis_container: tuple[str, HostPortPairModel]
    ) -> AsyncIterator[MonitoringValkeyClient]:
        hostport_pair: HostPortPairModel = redis_container[1]
        valkey_target = ValkeyTarget(addr=hostport_pair.address)
        client = cast(
            MonitoringValkeyClient,
            create_valkey_client(
                valkey_target,
                db_id=REDIS_STREAM_DB,
                human_readable_name="test.client",
            ),
        )
        await client.connect()
        try:
            yield client
        finally:
            await client.disconnect()

    async def test_client_yields_glide_client(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """Test that client() yields the operation GlideClient."""
        async with monitoring_client.client() as conn:
            result = await conn.ping()
            assert result == b"PONG"

    async def test_client_resets_failure_count_on_success(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """Test that successful operations reset the failure counter."""
        # Manually set a non-zero failure count
        monitoring_client._operation_failure_count = 2

        async with monitoring_client.client() as conn:
            await conn.ping()

        # Success should reset the counter
        assert monitoring_client._operation_failure_count == 0

    async def test_client_increments_failure_count_on_connection_error(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """Test that connection errors increment the failure counter."""
        assert monitoring_client._operation_failure_count == 0

        with pytest.raises(ConnectionError):
            async with monitoring_client.client() as _conn:
                raise ConnectionError("simulated connection failure")

        assert monitoring_client._operation_failure_count == 1

    async def test_client_does_not_increment_on_non_connection_error(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """Test that non-connection errors do NOT increment the failure counter."""
        assert monitoring_client._operation_failure_count == 0

        with pytest.raises(ValueError):
            async with monitoring_client.client() as _conn:
                raise ValueError("business logic error")

        # Non-connection errors should not affect the counter
        assert monitoring_client._operation_failure_count == 0

    async def test_client_does_not_reconnect_below_threshold(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """Test that failures below threshold do NOT trigger reconnection."""
        threshold = monitoring_client._operation_failure_threshold

        # Simulate failures up to threshold - 1
        for i in range(threshold - 1):
            with pytest.raises(ConnectionError):
                async with monitoring_client.client() as _conn:
                    raise ConnectionError(f"failure {i + 1}")

        assert monitoring_client._operation_failure_count == threshold - 1
        # Client should still be operational (no reconnect triggered)
        async with monitoring_client.client() as conn:
            result = await conn.ping()
            assert result == b"PONG"

    async def test_operation_client_recovery_while_monitor_healthy(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """Test that operation client recovers via client() even when monitor client is healthy.

        This is the core scenario where the monitor loop alone cannot detect the problem:
        the monitor client pings successfully, but the operation client is broken.
        The client() failure tracking sets _reconnect_event, and the monitor loop
        performs the actual reconnection.
        """
        threshold = monitoring_client._operation_failure_threshold

        # 1. Verify both clients are initially healthy
        await monitoring_client.ping()  # monitor client ping
        async with monitoring_client.client() as conn:
            assert await conn.ping() == b"PONG"  # operation client works

        # 2. Break ONLY the operation client — monitor client stays healthy
        await monitoring_client._operation_client.disconnect()

        # 3. Verify monitor client is still healthy (this is the key distinction)
        await monitoring_client._monitor_client.ping()

        # 4. Operation requests fail, client() tracks failures
        for i in range(threshold):
            with pytest.raises(_VALKEY_CONNECTION_ERRORS):
                async with monitoring_client.client() as conn:
                    await conn.ping()

        # 5. Counter should be reset and reconnect event should be set
        assert monitoring_client._operation_failure_count == 0
        assert monitoring_client._reconnect_event.is_set()

        # 6. Simulate monitor loop picking up the reconnect request
        monitoring_client._reconnect_event.clear()
        await monitoring_client._reconnect()

        # 7. Operation client should be restored
        async with monitoring_client.client() as conn:
            result = await conn.ping()
            assert result == b"PONG"

        # 8. Monitor client should also still be healthy after reconnect
        await monitoring_client._monitor_client.ping()

    async def test_client_tracks_each_connection_error_type(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """Test that all defined connection error types are tracked."""
        test_errors: list[type[Exception]] = [
            ConnectionError,
            OSError,
            ClientNotConnectedError,
        ]

        for error_type in test_errors:
            monitoring_client._operation_failure_count = 0

            with pytest.raises(error_type):
                async with monitoring_client.client() as _conn:
                    raise error_type(f"test {error_type.__name__}")

            assert monitoring_client._operation_failure_count == 1

    async def test_client_mixed_success_and_failure(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """Test that a successful operation between failures resets the counter."""
        # First failure
        with pytest.raises(ConnectionError):
            async with monitoring_client.client() as _conn:
                raise ConnectionError("failure 1")
        assert monitoring_client._operation_failure_count == 1

        # Second failure
        with pytest.raises(ConnectionError):
            async with monitoring_client.client() as _conn:
                raise ConnectionError("failure 2")
        assert monitoring_client._operation_failure_count == 2

        # Success resets
        async with monitoring_client.client() as conn:
            await conn.ping()
        assert monitoring_client._operation_failure_count == 0

        # Failure again starts from 1
        with pytest.raises(ConnectionError):
            async with monitoring_client.client() as _conn:
                raise ConnectionError("failure 3")
        assert monitoring_client._operation_failure_count == 1
