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

    async def test_ping_operation_client(self, monitoring_client: MonitoringValkeyClient) -> None:
        """Test that ping_operation_client() pings the operation client directly."""
        # Should succeed when operation client is healthy
        await monitoring_client.ping_operation_client()

        # Break operation client — ping_operation_client should fail
        await monitoring_client._operation_client.disconnect()
        with pytest.raises(Exception):
            await monitoring_client.ping_operation_client()

        # Monitor ping should still succeed
        await monitoring_client.ping()

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

    async def test_selective_reconnection_operation_only_when_monitor_healthy(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """When operation client is broken but monitor is healthy,
        only the operation client should be reconnected.

        This is the core BA-5577 scenario: the monitor loop detects the
        reconnect request from operation failure tracking, checks monitor
        health, and selectively reconnects only the operation client.
        """
        threshold = monitoring_client._operation_failure_threshold

        # 1. Verify both clients are initially healthy
        await monitoring_client.ping()
        async with monitoring_client.client() as conn:
            assert await conn.ping() == b"PONG"

        # 2. Break ONLY the operation client
        await monitoring_client._operation_client.disconnect()

        # 3. Verify monitor client is still healthy
        await monitoring_client._monitor_client.ping()

        # 4. Operation failures trigger reconnect event
        for i in range(threshold):
            with pytest.raises(_VALKEY_CONNECTION_ERRORS):
                async with monitoring_client.client() as conn:
                    await conn.ping()

        assert monitoring_client._operation_failure_count == 0
        assert monitoring_client._reconnect_event.is_set()

        # 5. Simulate monitor loop: since monitor is healthy, only operation reconnects
        monitoring_client._reconnect_event.clear()
        assert await monitoring_client._is_monitor_healthy()
        await monitoring_client._reconnect_operation_only()

        # 6. Operation client should be restored
        async with monitoring_client.client() as conn:
            assert await conn.ping() == b"PONG"

        # 7. Monitor client should remain healthy (was never disconnected)
        await monitoring_client._monitor_client.ping()

    async def test_full_reconnect_when_both_unhealthy(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """When both operation and monitor clients are broken,
        both should be reconnected via full _reconnect().
        """
        # 1. Break both clients
        await monitoring_client._operation_client.disconnect()
        await monitoring_client._monitor_client.disconnect()

        # 2. Monitor should be unhealthy
        assert not await monitoring_client._is_monitor_healthy()

        # 3. Full reconnect restores both
        await monitoring_client._reconnect()

        # 4. Both should be operational again
        await monitoring_client._monitor_client.ping()
        async with monitoring_client.client() as conn:
            assert await conn.ping() == b"PONG"

    async def test_monitor_loop_selective_reconnect_integration(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """Integration test: the monitor loop performs selective reconnection
        when operation failures reach the threshold while monitor stays healthy.
        """
        threshold = monitoring_client._operation_failure_threshold

        # 1. Break only the operation client
        await monitoring_client._operation_client.disconnect()

        # 2. Trigger operation failure threshold
        for i in range(threshold):
            with pytest.raises(_VALKEY_CONNECTION_ERRORS):
                async with monitoring_client.client() as conn:
                    await conn.ping()

        # 3. The reconnect event is set — let the running monitor loop handle it
        assert monitoring_client._reconnect_event.is_set()

        # 4. Wait for monitor loop to pick up the event and reconnect
        await asyncio.sleep(monitoring_client._monitor_interval + 1.0)

        # 5. Operation client should be restored by the monitor loop
        async with monitoring_client.client() as conn:
            assert await conn.ping() == b"PONG"

        # 6. Monitor client should still be healthy
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
