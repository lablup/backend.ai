from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import cast

import pytest

from ai.backend.common.clients.valkey_client.client import (
    MonitoringValkeyClient,
    ValkeyStandaloneClient,
    ValkeyStandaloneTarget,
    create_valkey_client,
)
from ai.backend.common.defs import REDIS_STREAM_DB
from ai.backend.common.health_checker import ComponentId
from ai.backend.common.health_checker.checkers.valkey import ValkeyHealthChecker
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ValkeyTarget


class TestValkeyHealthChecker:
    """Test ValkeyHealthChecker with real Valkey/Redis containers."""

    @pytest.fixture
    async def valkey_client(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> AsyncGenerator[ValkeyStandaloneClient, None]:
        """Create a Valkey standalone client connected to the test container."""
        container_id, hostport_pair = redis_container

        target = ValkeyStandaloneTarget(address=hostport_pair.address)
        client = ValkeyStandaloneClient(
            target,
            db_id=0,
            human_readable_name="test-health-checker",
        )
        await client.connect()

        try:
            yield client
        finally:
            await client.disconnect()

    async def test_success(self, valkey_client: ValkeyStandaloneClient) -> None:
        """Test successful health check with real Valkey connection."""
        checker = ValkeyHealthChecker(
            clients={ComponentId("test"): valkey_client},
            timeout=5.0,
        )

        result = await checker.check_service()
        assert len(result.results) == 1
        status = result.results[list(result.results.keys())[0]]
        assert status.is_healthy
        assert status.error_message is None

    async def test_timeout_property(
        self,
        valkey_client: ValkeyStandaloneClient,
    ) -> None:
        """Test that timeout property returns the correct value."""
        timeout_value = 3.5
        checker = ValkeyHealthChecker(
            clients={ComponentId("test"): valkey_client},
            timeout=timeout_value,
        )

        assert checker.timeout == timeout_value

    async def test_connection_error(self) -> None:
        """Test health check failure with unreachable Valkey server."""
        # Create client pointing to non-existent server
        target = ValkeyStandaloneTarget(address="localhost:99999")
        client = ValkeyStandaloneClient(
            target,
            db_id=0,
            human_readable_name="test-fail",
        )

        try:
            # Connection will fail, but let's test the checker anyway
            await client.connect()
        except Exception:
            # Expected - connection should fail
            pass

        try:
            checker = ValkeyHealthChecker(
                clients={ComponentId("test"): client},
                timeout=1.0,
            )

            result = await checker.check_service()
            assert len(result.results) == 1
            status = result.results[list(result.results.keys())[0]]
            assert not status.is_healthy
            assert status.error_message is not None
        finally:
            await client.disconnect()

    async def test_multiple_checks(
        self,
        valkey_client: ValkeyStandaloneClient,
    ) -> None:
        """Test that multiple health checks work correctly."""
        checker = ValkeyHealthChecker(
            clients={ComponentId("test"): valkey_client},
            timeout=5.0,
        )

        # Multiple checks should all succeed
        result1 = await checker.check_service()
        assert result1.results[list(result1.results.keys())[0]].is_healthy

        result2 = await checker.check_service()
        assert result2.results[list(result2.results.keys())[0]].is_healthy

        result3 = await checker.check_service()
        assert result3.results[list(result3.results.keys())[0]].is_healthy


@pytest.mark.redis
class TestValkeyHealthCheckerSubComponents:
    """Test ValkeyHealthChecker sub-component reporting for MonitoringValkeyClient."""

    @pytest.fixture
    async def monitoring_client(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> AsyncGenerator[MonitoringValkeyClient, None]:
        hostport_pair: HostPortPairModel = redis_container[1]
        valkey_target = ValkeyTarget(addr=hostport_pair.address)
        client = cast(
            MonitoringValkeyClient,
            create_valkey_client(
                valkey_target,
                db_id=REDIS_STREAM_DB,
                human_readable_name="test.health-sub-component",
            ),
        )
        await client.connect()
        try:
            yield client
        finally:
            await client.disconnect()

    async def test_reports_sub_components_for_monitoring_client(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """MonitoringValkeyClient should report operation and monitor sub-components."""
        checker = ValkeyHealthChecker(
            clients={ComponentId("test"): monitoring_client},
            timeout=5.0,
        )

        result = await checker.check_service()
        status = result.results[ComponentId("test")]

        assert status.is_healthy
        assert status.sub_components is not None
        assert "operation" in status.sub_components
        assert "monitor" in status.sub_components
        assert status.sub_components["operation"].is_healthy
        assert status.sub_components["monitor"].is_healthy

    async def test_no_sub_components_for_basic_client(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> None:
        """ValkeyStandaloneClient should NOT report sub-components."""
        hostport_pair: HostPortPairModel = redis_container[1]
        target = ValkeyStandaloneTarget(address=hostport_pair.address)
        client = ValkeyStandaloneClient(target, db_id=0, human_readable_name="test-basic")
        await client.connect()
        try:
            checker = ValkeyHealthChecker(
                clients={ComponentId("test"): client},
                timeout=5.0,
            )

            result = await checker.check_service()
            status = result.results[ComponentId("test")]

            assert status.is_healthy
            assert status.sub_components is None
        finally:
            await client.disconnect()

    async def test_detects_operation_client_failure(
        self, monitoring_client: MonitoringValkeyClient
    ) -> None:
        """When operation client is broken, sub-components should reflect this."""
        # Break only the operation client
        await monitoring_client._operation_client.disconnect()

        checker = ValkeyHealthChecker(
            clients={ComponentId("test"): monitoring_client},
            timeout=5.0,
        )

        result = await checker.check_service()
        status = result.results[ComponentId("test")]

        # Overall should be unhealthy
        assert not status.is_healthy
        assert status.sub_components is not None
        # Monitor should still be healthy
        assert status.sub_components["monitor"].is_healthy
        # Operation should be unhealthy
        assert not status.sub_components["operation"].is_healthy
        assert status.sub_components["operation"].error_message is not None
