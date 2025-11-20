"""
Tests for ValkeyScheduleClient health status timestamp tracking.
Tests the client with real Redis operations for route health monitoring.
"""

from __future__ import annotations

import asyncio
from time import time
from typing import AsyncGenerator

import pytest

from ai.backend.common.clients.valkey_client.valkey_schedule.client import (
    MAX_HEALTH_STALENESS_SEC,
    HealthCheckStatus,
    ValkeyScheduleClient,
)
from ai.backend.common.defs import REDIS_LIVE_DB
from ai.backend.common.typed_validators import HostPortPair as HostPortPairModel
from ai.backend.common.types import ValkeyTarget


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
    async def test_validate_health_status_with_valid_timestamp(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test validation with healthy status and fresh timestamp"""
        fresh_timestamp = str(int(time()))
        result = await valkey_schedule_client._validate_health_status("1", fresh_timestamp)
        assert result == HealthCheckStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_validate_health_status_with_stale_timestamp(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test validation with healthy status but stale timestamp"""
        stale_timestamp = str(int(time()) - MAX_HEALTH_STALENESS_SEC - 10)
        result = await valkey_schedule_client._validate_health_status("1", stale_timestamp)
        assert result == HealthCheckStatus.STALE

    @pytest.mark.asyncio
    async def test_validate_health_status_with_unhealthy_status(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test validation with unhealthy status regardless of timestamp"""
        fresh_timestamp = str(int(time()))
        result = await valkey_schedule_client._validate_health_status("0", fresh_timestamp)
        assert result == HealthCheckStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_validate_health_status_with_invalid_timestamp(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test validation with invalid timestamp formats"""
        result1 = await valkey_schedule_client._validate_health_status("1", "invalid")
        assert result1 == HealthCheckStatus.STALE
        result2 = await valkey_schedule_client._validate_health_status("1", "")
        assert result2 == HealthCheckStatus.STALE

    @pytest.mark.asyncio
    async def test_initialize_routes_health_status_batch(
        self, valkey_schedule_client: ValkeyScheduleClient
    ) -> None:
        """Test that initialized routes are unhealthy until first health check"""
        route_ids = ["route-1", "route-2", "route-3"]

        await valkey_schedule_client.initialize_routes_health_status_batch(route_ids)

        # Verify all initialized routes are considered stale (no timestamp data)
        for route_id in route_ids:
            status = await valkey_schedule_client.get_route_health_status(route_id)
            assert status is not None
            assert status.readiness == HealthCheckStatus.STALE, "Initialized route should be stale"
            assert status.liveness == HealthCheckStatus.STALE, "Initialized route should be stale"

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
        # Should be stale without timestamp fields
        assert status.readiness == HealthCheckStatus.STALE
        assert status.liveness == HealthCheckStatus.STALE

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

        # Verify results with proper type narrowing
        assert len(statuses) == 3

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

        # Initialize route
        await valkey_schedule_client.initialize_routes_health_status_batch([route_id])
        initial_status = await valkey_schedule_client.get_route_health_status(route_id)
        assert initial_status is not None
        initial_last_check = initial_status.last_check

        # Wait to ensure timestamp difference
        await asyncio.sleep(1.1)

        # Check health status should update last_check
        await valkey_schedule_client.check_route_health_status([route_id])

        # Verify last_check was updated
        updated_status = await valkey_schedule_client.get_route_health_status(route_id)
        assert updated_status is not None
        assert updated_status.last_check > initial_last_check, (
            "last_check should be updated after check"
        )
