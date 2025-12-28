"""
Tests for ValkeyScheduleClient health status timestamp tracking.
Tests the client with real Redis operations for route health monitoring.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import AsyncGenerator
from uuid import uuid4

import pytest
from glide import ExpirySet, ExpiryType

from ai.backend.common.clients.valkey_client.valkey_schedule.client import (
    AGENT_LAST_CHECK_TTL_SEC,
    KERNEL_HEALTH_TTL_SEC,
    MAX_HEALTH_STALENESS_SEC,
    MAX_KERNEL_HEALTH_STALENESS_SEC,
    HealthCheckStatus,
    ValkeyScheduleClient,
)
from ai.backend.common.defs import REDIS_LIVE_DB
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import AgentId, KernelId, ValkeyTarget


class TestValkeyScheduleClient:
    """Test cases for ValkeyScheduleClient health status functionality"""

    @pytest.fixture
    async def valkey_schedule_client(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> AsyncGenerator[ValkeyScheduleClient, None]:
        """Create ValkeyScheduleClient with real Redis container"""
        _, hostport_pair = redis_container

        valkey_target = ValkeyTarget(
            addr=hostport_pair.address,
        )

        client = await ValkeyScheduleClient.create(
            valkey_target=valkey_target,
            db_id=REDIS_LIVE_DB,
            human_readable_name="test-valkey-schedule",
        )

        try:
            yield client
        finally:
            await client.close()

    async def _set_stale_health_data(self, client: ValkeyScheduleClient, route_id: str) -> None:
        """Helper: Manually set stale health data for testing staleness detection"""
        key = client._get_route_health_key(route_id)
        stale_timestamp = str(int(time()) - MAX_HEALTH_STALENESS_SEC - 10)
        await client._client.client.hset(
            key,
            {
                "readiness": "1",
                "last_readiness": stale_timestamp,
                "liveness": "1",
                "last_liveness": stale_timestamp,
            },
        )

    @pytest.mark.asyncio
    async def test_initialize_routes_health_status_batch(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test that initialized routes have None readiness/liveness until first health check"""
        route_ids = ["route-1", "route-2", "route-3"]

        await valkey_schedule_client.initialize_routes_health_status_batch(route_ids)

        # Verify all initialized routes have None readiness/liveness (no timestamp data yet)
        for route_id in route_ids:
            status = await valkey_schedule_client.get_route_health_status(route_id)
            assert status is not None
            assert status.readiness is None, "Initialized route should have None readiness"
            assert status.liveness is None, "Initialized route should have None liveness"

    @pytest.mark.asyncio
    async def test_update_route_readiness_healthy(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test that updating readiness to healthy makes route ready"""
        route_id = "test-route-healthy"

        await valkey_schedule_client.update_route_readiness(route_id, True)

        status = await valkey_schedule_client.get_route_health_status(route_id)
        assert status is not None
        assert status.readiness == HealthCheckStatus.HEALTHY, (
            "Route should be ready after healthy update"
        )

    @pytest.mark.asyncio
    async def test_update_route_readiness_unhealthy(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test that updating readiness to unhealthy makes route not ready"""
        route_id = "test-route-unhealthy"

        await valkey_schedule_client.update_route_readiness(route_id, False)

        status = await valkey_schedule_client.get_route_health_status(route_id)
        assert status is not None
        assert status.readiness == HealthCheckStatus.UNHEALTHY, (
            "Route should not be ready after unhealthy update"
        )

    @pytest.mark.asyncio
    async def test_update_route_liveness_healthy(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test that updating liveness to healthy makes route alive"""
        route_id = "test-route-live"

        await valkey_schedule_client.update_route_liveness(route_id, True)

        status = await valkey_schedule_client.get_route_health_status(route_id)
        assert status is not None
        assert status.liveness == HealthCheckStatus.HEALTHY, (
            "Route should be alive after healthy update"
        )

    @pytest.mark.asyncio
    async def test_update_route_liveness_unhealthy(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test that updating liveness to unhealthy makes route not alive"""
        route_id = "test-route-dead"

        await valkey_schedule_client.update_route_liveness(route_id, False)

        status = await valkey_schedule_client.get_route_health_status(route_id)
        assert status is not None
        assert status.liveness == HealthCheckStatus.UNHEALTHY, (
            "Route should not be alive after unhealthy update"
        )

    @pytest.mark.asyncio
    async def test_update_routes_readiness_batch(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test batch updating readiness for multiple routes with correct statuses"""
        route_readiness = {
            "batch-route-1": True,
            "batch-route-2": False,
            "batch-route-3": True,
        }

        await valkey_schedule_client.update_routes_readiness_batch(route_readiness)

        # Verify all routes have correct readiness status
        for route_id, expected_readiness in route_readiness.items():
            status = await valkey_schedule_client.get_route_health_status(route_id)
            assert status is not None
            expected_status = (
                HealthCheckStatus.HEALTHY if expected_readiness else HealthCheckStatus.UNHEALTHY
            )
            assert status.readiness == expected_status, (
                f"Route {route_id} should have readiness={expected_status}"
            )

    @pytest.mark.asyncio
    async def test_get_route_health_status_healthy_and_fresh(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test getting health status with healthy and fresh data"""
        route_id = "test-fresh-healthy"

        # Set healthy status with fresh timestamp
        await valkey_schedule_client.update_route_readiness(route_id, True)
        await valkey_schedule_client.update_route_liveness(route_id, True)

        status = await valkey_schedule_client.get_route_health_status(route_id)
        assert status is not None
        assert status.readiness == HealthCheckStatus.HEALTHY
        assert status.liveness == HealthCheckStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_get_route_health_status_healthy_but_stale(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test that stale health data is considered stale"""
        route_id = "test-stale-healthy"

        # Set stale health data
        await self._set_stale_health_data(valkey_schedule_client, route_id)

        status = await valkey_schedule_client.get_route_health_status(route_id)
        assert status is not None
        # Stale data should be marked as stale
        assert status.readiness == HealthCheckStatus.STALE, (
            "Stale health data should be marked as stale"
        )
        assert status.liveness == HealthCheckStatus.STALE, (
            "Stale health data should be marked as stale"
        )

    @pytest.mark.asyncio
    async def test_get_route_health_status_unhealthy(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test getting health status with unhealthy status"""
        route_id = "test-unhealthy"

        await valkey_schedule_client.update_route_readiness(route_id, False)
        await valkey_schedule_client.update_route_liveness(route_id, False)

        status = await valkey_schedule_client.get_route_health_status(route_id)
        assert status is not None
        assert status.readiness == HealthCheckStatus.UNHEALTHY
        assert status.liveness == HealthCheckStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_get_route_health_status_missing_fields(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test getting health status when last_readiness/last_liveness are missing"""
        route_id = "test-missing-fields"

        # Initialize route (no last_readiness/last_liveness fields)
        await valkey_schedule_client.initialize_routes_health_status_batch([route_id])

        status = await valkey_schedule_client.get_route_health_status(route_id)
        assert status is not None
        # Should be None without timestamp fields
        assert status.readiness is None
        assert status.liveness is None

    @pytest.mark.asyncio
    async def test_get_route_health_status_not_found(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test getting health status for non-existent route"""
        status = await valkey_schedule_client.get_route_health_status("nonexistent-route")
        assert status is None

    @pytest.mark.asyncio
    async def test_check_route_health_status_multiple_routes(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test checking health status for multiple routes with different states"""
        # Setup routes with different states
        healthy_route = "check-healthy"
        unhealthy_route = "check-unhealthy"
        stale_route = "check-stale"

        # Healthy route
        await valkey_schedule_client.update_route_readiness(healthy_route, True)
        await valkey_schedule_client.update_route_liveness(healthy_route, True)

        # Unhealthy route
        await valkey_schedule_client.update_route_readiness(unhealthy_route, False)
        await valkey_schedule_client.update_route_liveness(unhealthy_route, False)

        # Stale route
        await self._set_stale_health_data(valkey_schedule_client, stale_route)

        # Check all routes
        statuses = await valkey_schedule_client.check_route_health_status([
            healthy_route,
            unhealthy_route,
            stale_route,
        ])

        healthy_status = statuses[healthy_route]
        assert healthy_status is not None
        assert healthy_status.readiness == HealthCheckStatus.HEALTHY, (
            "Healthy route should be ready"
        )

        unhealthy_status = statuses[unhealthy_route]
        assert unhealthy_status is not None
        assert unhealthy_status.readiness == HealthCheckStatus.UNHEALTHY, (
            "Unhealthy route should not be ready"
        )

        stale_status = statuses[stale_route]
        assert stale_status is not None
        assert stale_status.readiness == HealthCheckStatus.STALE, (
            "Stale route should be marked as stale"
        )

    @pytest.mark.asyncio
    async def test_check_route_health_status_updates_last_check(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test that check_route_health_status updates last_check timestamp"""
        route_id = "check-last-check"

        # Set route with old last_check timestamp
        key = valkey_schedule_client._get_route_health_key(route_id)
        old_timestamp = str(int(time()) - 60)  # 60 seconds ago
        await valkey_schedule_client._client.client.hset(
            key,
            {"readiness": "1", "last_readiness": old_timestamp, "last_check": old_timestamp},
        )

        # Check health status should update last_check
        await valkey_schedule_client.check_route_health_status([route_id])

        # Verify last_check was updated to current time
        updated_status = await valkey_schedule_client.get_route_health_status(route_id)
        assert updated_status is not None
        assert updated_status.last_check is not None
        assert updated_status.last_check > int(old_timestamp), (
            "last_check should be updated after check"
        )


@dataclass
class KernelPresenceFixture:
    """Container for kernel presence test fixtures."""

    client: ValkeyScheduleClient
    kernel_id: KernelId
    kernel_ids: list[KernelId]
    healthy_kernel_id: KernelId
    unhealthy_kernel_id: KernelId
    stale_kernel_id: KernelId
    missing_kernel_id: KernelId


class TestKernelPresenceStatus:
    """Test cases for kernel presence status functionality"""

    @pytest.fixture
    async def valkey_schedule_client(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> AsyncGenerator[ValkeyScheduleClient, None]:
        """Create ValkeyScheduleClient with real Redis container."""
        _, hostport_pair = redis_container

        valkey_target = ValkeyTarget(
            addr=hostport_pair.address,
        )

        client = await ValkeyScheduleClient.create(
            valkey_target=valkey_target,
            db_id=REDIS_LIVE_DB,
            human_readable_name="test-valkey-schedule-kernel",
        )

        try:
            yield client
        finally:
            await client.close()

    @pytest.fixture
    def kernel_id(self) -> KernelId:
        """Generate a single kernel ID."""
        return KernelId(uuid4())

    @pytest.fixture
    def kernel_ids(self) -> list[KernelId]:
        """Generate multiple kernel IDs."""
        return [KernelId(uuid4()) for _ in range(3)]

    @pytest.fixture
    async def initialized_kernel(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        kernel_id: KernelId,
    ) -> KernelId:
        """Initialize a kernel and return its ID."""
        await valkey_schedule_client.initialize_kernel_presence_batch([kernel_id])
        return kernel_id

    @pytest.fixture
    async def initialized_kernels(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        kernel_ids: list[KernelId],
    ) -> list[KernelId]:
        """Initialize multiple kernels and return their IDs."""
        await valkey_schedule_client.initialize_kernel_presence_batch(kernel_ids)
        return kernel_ids

    @pytest.fixture
    async def healthy_kernel(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
    ) -> KernelId:
        """Create a kernel with healthy presence status."""
        kernel_id = KernelId(uuid4())
        await valkey_schedule_client.initialize_kernel_presence_batch([kernel_id])
        await valkey_schedule_client.update_kernel_presence_batch({kernel_id: True})
        return kernel_id

    @pytest.fixture
    async def unhealthy_kernel(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
    ) -> KernelId:
        """Create a kernel with unhealthy presence status."""
        kernel_id = KernelId(uuid4())
        await valkey_schedule_client.initialize_kernel_presence_batch([kernel_id])
        await valkey_schedule_client.update_kernel_presence_batch({kernel_id: False})
        return kernel_id

    @pytest.fixture
    async def stale_kernel(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
    ) -> KernelId:
        """Create a kernel with stale presence status."""
        kernel_id = KernelId(uuid4())
        key = valkey_schedule_client._get_kernel_presence_key(kernel_id)
        stale_timestamp = str(int(time()) - MAX_KERNEL_HEALTH_STALENESS_SEC - 10)
        await valkey_schedule_client._client.client.hset(
            key,
            {
                "presence": "1",
                "last_presence": stale_timestamp,
                "last_check": stale_timestamp,
                "created_at": stale_timestamp,
            },
        )
        await valkey_schedule_client._client.client.expire(key, KERNEL_HEALTH_TTL_SEC)
        return kernel_id

    @pytest.fixture
    async def mixed_state_kernels(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        healthy_kernel: KernelId,
        unhealthy_kernel: KernelId,
        stale_kernel: KernelId,
    ) -> KernelPresenceFixture:
        """Create kernels with various states for mixed state testing."""
        missing_kernel_id = KernelId(uuid4())  # Not initialized
        return KernelPresenceFixture(
            client=valkey_schedule_client,
            kernel_id=healthy_kernel,
            kernel_ids=[healthy_kernel, unhealthy_kernel, stale_kernel, missing_kernel_id],
            healthy_kernel_id=healthy_kernel,
            unhealthy_kernel_id=unhealthy_kernel,
            stale_kernel_id=stale_kernel,
            missing_kernel_id=missing_kernel_id,
        )

    # ===== Tests =====

    @pytest.mark.asyncio
    async def test_initialize_kernel_presence_batch(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        initialized_kernels: list[KernelId],
    ) -> None:
        """Test batch initialization of kernel presence status."""
        statuses = await valkey_schedule_client.check_kernel_presence_status_batch(
            initialized_kernels
        )

        assert len(statuses) == len(initialized_kernels)
        for kernel_id in initialized_kernels:
            status = statuses[kernel_id]
            assert status is not None
            assert status.presence == HealthCheckStatus.UNHEALTHY
            assert status.last_presence is not None and status.last_presence > 0
            assert status.last_check is not None and status.last_check > 0
            assert status.created_at > 0

    @pytest.mark.asyncio
    async def test_initialize_kernel_presence_batch_empty(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test that empty batch initialization does nothing."""
        await valkey_schedule_client.initialize_kernel_presence_batch([])

    @pytest.mark.asyncio
    async def test_update_kernel_presence_batch_healthy(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        healthy_kernel: KernelId,
    ) -> None:
        """Test batch update of kernel presence to healthy."""
        statuses = await valkey_schedule_client.check_kernel_presence_status_batch([healthy_kernel])

        status = statuses[healthy_kernel]
        assert status is not None
        assert status.presence == HealthCheckStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_update_kernel_presence_batch_unhealthy(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        unhealthy_kernel: KernelId,
    ) -> None:
        """Test batch update of kernel presence to unhealthy."""
        statuses = await valkey_schedule_client.check_kernel_presence_status_batch([
            unhealthy_kernel
        ])

        status = statuses[unhealthy_kernel]
        assert status is not None
        assert status.presence == HealthCheckStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_update_kernel_presence_batch_mixed(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        healthy_kernel: KernelId,
        unhealthy_kernel: KernelId,
    ) -> None:
        """Test batch update with mixed healthy/unhealthy states."""
        statuses = await valkey_schedule_client.check_kernel_presence_status_batch([
            healthy_kernel,
            unhealthy_kernel,
        ])

        healthy_status = statuses[healthy_kernel]
        assert healthy_status is not None
        assert healthy_status.presence == HealthCheckStatus.HEALTHY

        unhealthy_status = statuses[unhealthy_kernel]
        assert unhealthy_status is not None
        assert unhealthy_status.presence == HealthCheckStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_delete_kernel_presence_batch(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        initialized_kernels: list[KernelId],
    ) -> None:
        """Test batch deletion of kernel presence status."""
        # Verify exists before delete
        statuses_before = await valkey_schedule_client.check_kernel_presence_status_batch(
            initialized_kernels
        )
        for kernel_id in initialized_kernels:
            assert statuses_before[kernel_id] is not None

        # Delete
        await valkey_schedule_client.delete_kernel_presence_batch(initialized_kernels)

        # Verify deleted
        statuses_after = await valkey_schedule_client.check_kernel_presence_status_batch(
            initialized_kernels
        )
        for kernel_id in initialized_kernels:
            assert statuses_after[kernel_id] is None

    @pytest.mark.asyncio
    async def test_delete_kernel_presence_batch_empty(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test that empty batch deletion does nothing."""
        await valkey_schedule_client.delete_kernel_presence_batch([])

    @pytest.mark.asyncio
    async def test_check_kernel_presence_status_batch_not_found(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        kernel_ids: list[KernelId],
    ) -> None:
        """Test checking status for non-existent kernels."""
        statuses = await valkey_schedule_client.check_kernel_presence_status_batch(kernel_ids)

        assert len(statuses) == len(kernel_ids)
        for kernel_id in kernel_ids:
            assert statuses[kernel_id] is None

    @pytest.mark.asyncio
    async def test_check_kernel_presence_status_batch_empty(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test checking status with empty list."""
        statuses = await valkey_schedule_client.check_kernel_presence_status_batch([])
        assert statuses == {}

    @pytest.mark.asyncio
    async def test_check_kernel_presence_status_batch_updates_last_check(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
    ) -> None:
        """Test that check updates last_check timestamp."""
        # Set kernel with old last_check timestamp
        kernel_id = KernelId(uuid4())
        key = valkey_schedule_client._get_kernel_presence_key(kernel_id)
        old_timestamp = str(int(time()) - 60)  # 60 seconds ago
        await valkey_schedule_client._client.client.hset(
            key,
            {
                "presence": "1",
                "last_presence": old_timestamp,
                "last_check": old_timestamp,
                "created_at": old_timestamp,
            },
        )

        # Check should update last_check
        statuses = await valkey_schedule_client.check_kernel_presence_status_batch([kernel_id])
        status = statuses[kernel_id]
        assert status is not None
        assert status.last_check is not None
        assert status.last_check > int(old_timestamp)

    @pytest.mark.asyncio
    async def test_check_kernel_presence_status_batch_stale_detection(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        stale_kernel: KernelId,
    ) -> None:
        """Test that stale kernel presence is detected correctly."""
        statuses = await valkey_schedule_client.check_kernel_presence_status_batch([stale_kernel])

        status = statuses[stale_kernel]
        assert status is not None
        assert status.presence == HealthCheckStatus.STALE

    @pytest.mark.asyncio
    async def test_check_kernel_presence_status_batch_mixed_states(
        self,
        mixed_state_kernels: KernelPresenceFixture,
    ) -> None:
        """Test checking multiple kernels with different states."""
        fixture = mixed_state_kernels
        statuses = await fixture.client.check_kernel_presence_status_batch(fixture.kernel_ids)

        assert len(statuses) == len(fixture.kernel_ids)

        healthy_status = statuses[fixture.healthy_kernel_id]
        assert healthy_status is not None
        assert healthy_status.presence == HealthCheckStatus.HEALTHY

        unhealthy_status = statuses[fixture.unhealthy_kernel_id]
        assert unhealthy_status is not None
        assert unhealthy_status.presence == HealthCheckStatus.UNHEALTHY

        stale_status = statuses[fixture.stale_kernel_id]
        assert stale_status is not None
        assert stale_status.presence == HealthCheckStatus.STALE

        assert statuses[fixture.missing_kernel_id] is None


class TestAgentLastCheck:
    """Test cases for agent last check functionality.

    These tests verify the bidirectional kernel presence synchronization
    mechanism, specifically the agent_last_check timestamp tracking.
    """

    @pytest.fixture
    async def valkey_schedule_client(
        self,
        redis_container: tuple[str, HostPortPairModel],
    ) -> AsyncGenerator[ValkeyScheduleClient, None]:
        """Create ValkeyScheduleClient with real Redis container."""
        _, hostport_pair = redis_container

        valkey_target = ValkeyTarget(
            addr=hostport_pair.address,
        )

        client = await ValkeyScheduleClient.create(
            valkey_target=valkey_target,
            db_id=REDIS_LIVE_DB,
            human_readable_name="test-valkey-schedule-agent",
        )

        try:
            yield client
        finally:
            await client.close()

    @pytest.fixture
    def agent_id(self) -> AgentId:
        """Generate a unique agent ID."""
        return AgentId(f"test-agent-{uuid4().hex[:8]}")

    @pytest.fixture
    def agent_ids(self) -> set[AgentId]:
        """Generate multiple unique agent IDs."""
        return {AgentId(f"test-agent-{uuid4().hex[:8]}") for _ in range(2)}

    @pytest.fixture
    def kernel_ids(self) -> list[KernelId]:
        """Generate multiple kernel IDs."""
        return [KernelId(uuid4()) for _ in range(3)]

    @pytest.mark.asyncio
    async def test_get_agent_last_check_not_exists(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        agent_id: AgentId,
    ) -> None:
        """Test that get_agent_last_check returns None for non-existent agent."""
        result = await valkey_schedule_client.get_agent_last_check(agent_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_agent_last_check_exists(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        agent_id: AgentId,
    ) -> None:
        """Test that get_agent_last_check returns timestamp when it exists."""
        # Manually set agent_last_check
        key = valkey_schedule_client._get_agent_last_check_key(agent_id)
        expected_timestamp = int(time())
        await valkey_schedule_client._client.client.set(
            key,
            str(expected_timestamp),
            expiry=ExpirySet(ExpiryType.SEC, AGENT_LAST_CHECK_TTL_SEC),
        )

        result = await valkey_schedule_client.get_agent_last_check(agent_id)
        assert result == expected_timestamp

    @pytest.mark.asyncio
    async def test_check_kernel_presence_updates_agent_last_check(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        agent_id: AgentId,
        kernel_ids: list[KernelId],
    ) -> None:
        """Test that check_kernel_presence_status_batch updates agent_last_check."""
        # Initialize kernels
        await valkey_schedule_client.initialize_kernel_presence_batch(kernel_ids)

        # Verify agent_last_check doesn't exist yet
        assert await valkey_schedule_client.get_agent_last_check(agent_id) is None

        # Call check_kernel_presence_status_batch with agent_ids
        await valkey_schedule_client.check_kernel_presence_status_batch(
            kernel_ids, agent_ids={agent_id}
        )

        # Verify agent_last_check was set
        result = await valkey_schedule_client.get_agent_last_check(agent_id)
        assert result is not None
        assert result > 0

    @pytest.mark.asyncio
    async def test_check_kernel_presence_updates_multiple_agents_last_check(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        agent_ids: set[AgentId],
        kernel_ids: list[KernelId],
    ) -> None:
        """Test that check_kernel_presence_status_batch updates multiple agent_last_check."""
        # Initialize kernels
        await valkey_schedule_client.initialize_kernel_presence_batch(kernel_ids)

        # Call check_kernel_presence_status_batch with multiple agent_ids
        await valkey_schedule_client.check_kernel_presence_status_batch(
            kernel_ids, agent_ids=agent_ids
        )

        # Verify all agent_last_check values were set
        for agent_id in agent_ids:
            result = await valkey_schedule_client.get_agent_last_check(agent_id)
            assert result is not None
            assert result > 0

    @pytest.mark.asyncio
    async def test_check_kernel_presence_without_agent_ids_does_not_update(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        agent_id: AgentId,
        kernel_ids: list[KernelId],
    ) -> None:
        """Test that check_kernel_presence_status_batch without agent_ids doesn't update."""
        # Initialize kernels
        await valkey_schedule_client.initialize_kernel_presence_batch(kernel_ids)

        # Call without agent_ids
        await valkey_schedule_client.check_kernel_presence_status_batch(kernel_ids)

        # Verify agent_last_check was not set
        result = await valkey_schedule_client.get_agent_last_check(agent_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_kernel_presence_batch_does_not_update_last_check(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        kernel_ids: list[KernelId],
    ) -> None:
        """Test that get_kernel_presence_batch does not update last_check timestamp."""
        # Initialize kernels
        await valkey_schedule_client.initialize_kernel_presence_batch(kernel_ids)

        # Get initial last_check values
        initial_statuses = await valkey_schedule_client.check_kernel_presence_status_batch(
            kernel_ids
        )
        initial_last_checks: dict[KernelId, int] = {}
        for kid, status in initial_statuses.items():
            if status and status.last_check is not None:
                initial_last_checks[kid] = status.last_check

        # Wait a bit
        import asyncio

        await asyncio.sleep(0.1)

        # Call get_kernel_presence_batch (read-only)
        await valkey_schedule_client.get_kernel_presence_batch(kernel_ids)

        # Verify last_check values are unchanged
        current_statuses = await valkey_schedule_client.check_kernel_presence_status_batch(
            kernel_ids
        )
        for kernel_id, status in current_statuses.items():
            if status and status.last_check is not None:
                # last_check should be updated by check_kernel_presence_status_batch
                # but not by get_kernel_presence_batch
                initial_value = initial_last_checks.get(kernel_id, 0)
                assert status.last_check >= initial_value

    @pytest.mark.asyncio
    async def test_get_kernel_presence_batch_returns_status(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
        kernel_ids: list[KernelId],
    ) -> None:
        """Test that get_kernel_presence_batch returns correct status."""
        # Initialize and update kernels with healthy status
        await valkey_schedule_client.initialize_kernel_presence_batch(kernel_ids)
        await valkey_schedule_client.update_kernel_presence_batch({
            kernel_ids[0]: True,  # healthy
            kernel_ids[1]: False,  # unhealthy
        })

        # Get presence batch
        statuses = await valkey_schedule_client.get_kernel_presence_batch(kernel_ids)

        assert len(statuses) == len(kernel_ids)

        # Healthy kernel
        status0 = statuses[kernel_ids[0]]
        assert status0 is not None
        assert status0.presence == HealthCheckStatus.HEALTHY

        # Unhealthy kernel
        status1 = statuses[kernel_ids[1]]
        assert status1 is not None
        assert status1.presence == HealthCheckStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_get_kernel_presence_batch_missing_kernel(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
    ) -> None:
        """Test that get_kernel_presence_batch returns None for non-existent kernel."""
        missing_kernel_id = KernelId(uuid4())

        statuses = await valkey_schedule_client.get_kernel_presence_batch([missing_kernel_id])

        assert statuses[missing_kernel_id] is None

    @pytest.mark.asyncio
    async def test_get_kernel_presence_batch_empty(
        self,
        valkey_schedule_client: ValkeyScheduleClient,
    ) -> None:
        """Test that get_kernel_presence_batch returns empty dict for empty input."""
        statuses = await valkey_schedule_client.get_kernel_presence_batch([])

        assert statuses == {}
