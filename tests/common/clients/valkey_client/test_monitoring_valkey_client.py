from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import cast

import pytest

from ai.backend.common.clients.valkey_client.client import (
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

        # Operation client should be accessible
        operation_glide = monitoring_client.client
        result = await operation_glide.ping()
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

    async def test_client_not_connected_error(
        self, redis_container: tuple[str, HostPortPairModel]
    ) -> None:
        """Test that ClientNotConnectedError is raised when accessing disconnected client"""
        hostport_pair: HostPortPairModel = redis_container[1]
        valkey_target = ValkeyTarget(addr=hostport_pair.address)
        client = create_valkey_client(
            valkey_target,
            db_id=REDIS_STREAM_DB,
            human_readable_name="test.not_connected",
        )

        # Should raise error when not connected
        with pytest.raises(ClientNotConnectedError):
            _ = client.client

        # Connect and verify it works
        await client.connect()
        try:
            await client.ping()
        finally:
            await client.disconnect()

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
