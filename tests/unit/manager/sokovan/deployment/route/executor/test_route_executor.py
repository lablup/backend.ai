"""Unit tests for Sokovan RouteExecutor.

Based on BEP-1033 test scenarios for route executor testing.

Test Scenarios:
- RP-001 ~ RP-003: Route Provisioning
- RH-001 ~ RH-004: Route Health Check
- RR-001 ~ RR-004: Running Route Check
- RE-001 ~ RE-003: Route Eviction
- RT-001 ~ RT-003: Route Termination
- SD-001 ~ SD-004: Service Discovery Sync
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from ai.backend.common.types import SessionId
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor
from ai.backend.manager.sokovan.deployment.route.recorder.context import RouteRecorderContext

# =============================================================================
# TestProvisionRoutes (RP-001 ~ RP-003)
# =============================================================================


class TestProvisionRoutes:
    """Tests for provision_routes functionality.

    Verifies the executor correctly creates sessions for routes.
    """

    async def test_successful_provisioning(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_scheduling_controller: AsyncMock,
        provisioning_route: RouteData,
    ) -> None:
        """RP-001: Successful route provisioning.

        Given: PROVISIONING route without session
        When: Provision routes
        Then: Session created and linked to route
        """
        # Arrange
        deployment = MagicMock()
        deployment.id = provisioning_route.endpoint_id
        mock_deployment_repo.get_endpoints_by_ids.return_value = [deployment]

        expected_session_id = SessionId(uuid4())
        mock_scheduling_controller.enqueue_session.return_value = expected_session_id

        entity_ids = [provisioning_route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.provision_routes([provisioning_route])

        # Assert
        assert len(result.successes) == 1
        assert len(result.errors) == 0
        mock_scheduling_controller.enqueue_session.assert_awaited_once()
        mock_deployment_repo.update_route_sessions.assert_awaited_once()

        # Verify route_id -> session_id mapping in update call
        call_args = mock_deployment_repo.update_route_sessions.call_args
        route_session_ids = call_args[0][0]
        assert provisioning_route.route_id in route_session_ids
        assert route_session_ids[provisioning_route.route_id] == expected_session_id

    async def test_route_with_existing_session_skipped(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_scheduling_controller: AsyncMock,
        provisioning_route_with_session: RouteData,
    ) -> None:
        """RP-002: Route with existing session is skipped.

        Given: PROVISIONING route that already has session
        When: Provision routes
        Then: Session creation skipped
        """
        # Arrange
        deployment = MagicMock()
        deployment.id = provisioning_route_with_session.endpoint_id
        mock_deployment_repo.get_endpoints_by_ids.return_value = [deployment]

        entity_ids = [provisioning_route_with_session.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.provision_routes([provisioning_route_with_session])

        # Assert
        assert len(result.successes) == 1
        mock_scheduling_controller.enqueue_session.assert_not_awaited()

    async def test_provisioning_failure_captured(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_scheduling_controller: AsyncMock,
        provisioning_route: RouteData,
    ) -> None:
        """RP-003: Provisioning failure is captured.

        Given: Route with provisioning error
        When: Provision routes
        Then: Error captured in result
        """
        # Arrange
        mock_deployment_repo.get_endpoints_by_ids.return_value = []  # No deployment found

        entity_ids = [provisioning_route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.provision_routes([provisioning_route])

        # Assert
        assert len(result.successes) == 0
        assert len(result.errors) == 1


# =============================================================================
# TestCheckRouteHealth (RH-001 ~ RH-004)
# =============================================================================


class TestCheckRouteHealth:
    """Tests for check_route_health functionality.

    Verifies the executor correctly checks route health via Valkey.
    """

    async def test_healthy_route_in_successes(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
        healthy_route: RouteData,
        health_status_healthy: MagicMock,
    ) -> None:
        """RH-001: Healthy route is in successes.

        Given: Route with HEALTHY status in Valkey
        When: Check route health
        Then: Route in successes list
        """
        # Arrange
        route_id_str = str(healthy_route.route_id)
        mock_valkey_schedule.check_route_health_status.return_value = {
            route_id_str: health_status_healthy
        }

        entity_ids = [healthy_route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.check_route_health([healthy_route])

        # Assert
        assert len(result.successes) == 1
        assert len(result.errors) == 0
        assert len(result.stale) == 0

    async def test_unhealthy_route_in_errors(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
        healthy_route: RouteData,
        health_status_unhealthy: MagicMock,
    ) -> None:
        """RH-002: Unhealthy route is in errors.

        Given: Route with UNHEALTHY status in Valkey
        When: Check route health
        Then: Route in errors list
        """
        # Arrange
        route_id_str = str(healthy_route.route_id)
        mock_valkey_schedule.check_route_health_status.return_value = {
            route_id_str: health_status_unhealthy
        }

        entity_ids = [healthy_route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.check_route_health([healthy_route])

        # Assert
        assert len(result.successes) == 0
        assert len(result.errors) == 1
        assert len(result.stale) == 0

    async def test_stale_route_in_stale_list(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
        healthy_route: RouteData,
        health_status_stale: MagicMock,
    ) -> None:
        """RH-003: Stale route is in stale list.

        Given: Route with STALE status in Valkey
        When: Check route health
        Then: Route in stale list
        """
        # Arrange
        route_id_str = str(healthy_route.route_id)
        mock_valkey_schedule.check_route_health_status.return_value = {
            route_id_str: health_status_stale
        }

        entity_ids = [healthy_route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.check_route_health([healthy_route])

        # Assert
        assert len(result.successes) == 0
        assert len(result.errors) == 0
        assert len(result.stale) == 1

    async def test_missing_health_data_treated_as_stale(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
        healthy_route: RouteData,
    ) -> None:
        """RH-004: Missing health data is treated as stale.

        Given: Route with no health data in Valkey
        When: Check route health
        Then: Route in stale list
        """
        # Arrange - Empty health status response
        mock_valkey_schedule.check_route_health_status.return_value = {}

        entity_ids = [healthy_route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.check_route_health([healthy_route])

        # Assert
        assert len(result.successes) == 0
        assert len(result.errors) == 0
        assert len(result.stale) == 1


# =============================================================================
# TestCheckRunningRoutes (RR-001 ~ RR-004)
# =============================================================================


class TestCheckRunningRoutes:
    """Tests for check_running_routes functionality.

    Verifies the executor correctly checks session status for running routes.
    """

    async def test_active_session_route_in_successes(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        running_route: RouteData,
        session_status_running: MagicMock,
    ) -> None:
        """RR-001: Route with active session is in successes.

        Given: Running route with active session
        When: Check running routes
        Then: Route in successes list
        """
        # Arrange
        mock_deployment_repo.fetch_session_statuses_by_route_ids.return_value = {
            running_route.route_id: session_status_running
        }

        entity_ids = [running_route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.check_running_routes([running_route])

        # Assert
        assert len(result.successes) == 1
        assert len(result.errors) == 0

    async def test_terminated_session_route_in_errors(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        running_route: RouteData,
        session_status_terminated: MagicMock,
    ) -> None:
        """RR-002: Route with terminated session is in errors.

        Given: Running route with terminated session
        When: Check running routes
        Then: Route in errors list
        """
        # Arrange
        mock_deployment_repo.fetch_session_statuses_by_route_ids.return_value = {
            running_route.route_id: session_status_terminated
        }

        entity_ids = [running_route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.check_running_routes([running_route])

        # Assert
        assert len(result.successes) == 0
        assert len(result.errors) == 1

    async def test_missing_session_route_in_errors(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        running_route: RouteData,
    ) -> None:
        """RR-003: Route with missing session is in errors.

        Given: Running route with no session status
        When: Check running routes
        Then: Route in errors list
        """
        # Arrange - No session status found
        mock_deployment_repo.fetch_session_statuses_by_route_ids.return_value = {}

        entity_ids = [running_route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.check_running_routes([running_route])

        # Assert
        assert len(result.successes) == 0
        assert len(result.errors) == 1

    async def test_multiple_routes_classified_correctly(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        running_routes_multiple: list[RouteData],
        session_status_running: MagicMock,
        session_status_terminated: MagicMock,
    ) -> None:
        """RR-004: Multiple routes are classified correctly.

        Given: Multiple running routes with mixed session status
        When: Check running routes
        Then: Routes classified correctly
        """
        # Arrange
        route1, route2 = running_routes_multiple
        mock_deployment_repo.fetch_session_statuses_by_route_ids.return_value = {
            route1.route_id: session_status_running,
            route2.route_id: session_status_terminated,
        }

        entity_ids = [r.route_id for r in running_routes_multiple]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.check_running_routes(running_routes_multiple)

        # Assert
        assert len(result.successes) == 1
        assert len(result.errors) == 1


# =============================================================================
# TestCleanupRoutesByConfig (RE-001 ~ RE-003)
# =============================================================================


class TestCleanupRoutesByConfig:
    """Tests for cleanup_routes_by_config functionality.

    Verifies the executor correctly filters routes for cleanup.
    """

    async def test_unhealthy_route_marked_for_cleanup(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        unhealthy_route: RouteData,
        cleanup_config_unhealthy_only: MagicMock,
    ) -> None:
        """RE-001: Unhealthy route is marked for cleanup.

        Given: UNHEALTHY route with matching cleanup config
        When: Cleanup routes by config
        Then: Route in successes (marked for cleanup)
        """
        # Arrange
        deployment = MagicMock()
        deployment.id = unhealthy_route.endpoint_id
        deployment.metadata = MagicMock()
        deployment.metadata.resource_group = "default"
        mock_deployment_repo.get_endpoints_by_ids.return_value = [deployment]
        mock_deployment_repo.get_scaling_group_cleanup_configs.return_value = {
            "default": cleanup_config_unhealthy_only
        }

        entity_ids = [unhealthy_route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.cleanup_routes_by_config([unhealthy_route])

        # Assert
        assert len(result.successes) == 1

    async def test_healthy_route_not_marked_for_cleanup(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        healthy_route: RouteData,
        cleanup_config_unhealthy_only: MagicMock,
    ) -> None:
        """RE-002: Healthy route is not marked for cleanup.

        Given: HEALTHY route with cleanup config for UNHEALTHY only
        When: Cleanup routes by config
        Then: Route not in successes
        """
        # Arrange
        deployment = MagicMock()
        deployment.id = healthy_route.endpoint_id
        deployment.metadata = MagicMock()
        deployment.metadata.resource_group = "default"
        mock_deployment_repo.get_endpoints_by_ids.return_value = [deployment]
        mock_deployment_repo.get_scaling_group_cleanup_configs.return_value = {
            "default": cleanup_config_unhealthy_only
        }

        entity_ids = [healthy_route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.cleanup_routes_by_config([healthy_route])

        # Assert
        assert len(result.successes) == 0

    async def test_empty_route_list_returns_empty(
        self,
        route_executor: RouteExecutor,
    ) -> None:
        """RE-003: Empty route list returns empty result.

        Given: Empty route list
        When: Cleanup routes by config
        Then: Empty result
        """
        # Act
        result = await route_executor.cleanup_routes_by_config([])

        # Assert
        assert len(result.successes) == 0
        assert len(result.errors) == 0


# =============================================================================
# TestTerminateRoutes (RT-001 ~ RT-003)
# =============================================================================


class TestTerminateRoutes:
    """Tests for terminate_routes functionality.

    Verifies the executor correctly terminates route sessions.
    """

    async def test_successful_termination(
        self,
        route_executor: RouteExecutor,
        mock_scheduling_controller: AsyncMock,
        terminating_route: RouteData,
    ) -> None:
        """RT-001: Successful route termination.

        Given: TERMINATING route with session
        When: Terminate routes
        Then: Session marked for termination
        """
        entity_ids = [terminating_route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.terminate_routes([terminating_route])

        # Assert
        assert len(result.successes) == 1
        assert len(result.errors) == 0
        mock_scheduling_controller.mark_sessions_for_termination.assert_awaited_once()

        # Verify session_id passed for termination
        call_args = mock_scheduling_controller.mark_sessions_for_termination.call_args
        session_ids = call_args[0][0]
        assert len(session_ids) == 1
        assert terminating_route.session_id in session_ids

    async def test_route_without_session_skipped(
        self,
        route_executor: RouteExecutor,
        mock_scheduling_controller: AsyncMock,
        route_without_session: RouteData,
    ) -> None:
        """RT-002: Route without session is skipped.

        Given: TERMINATING route without session
        When: Terminate routes
        Then: Termination skipped for that route
        """
        entity_ids = [route_without_session.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.terminate_routes([route_without_session])

        # Assert
        assert len(result.successes) == 1  # Still considered success
        # But mark_sessions_for_termination called with empty list
        call_args = mock_scheduling_controller.mark_sessions_for_termination.call_args
        assert len(call_args[0][0]) == 0

    async def test_multiple_routes_terminated(
        self,
        route_executor: RouteExecutor,
        mock_scheduling_controller: AsyncMock,
        terminating_routes_multiple: list[RouteData],
    ) -> None:
        """RT-003: Multiple routes terminated together.

        Given: Multiple TERMINATING routes
        When: Terminate routes
        Then: All sessions marked for termination
        """
        entity_ids = [r.route_id for r in terminating_routes_multiple]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.terminate_routes(terminating_routes_multiple)

        # Assert
        assert len(result.successes) == 2
        mock_scheduling_controller.mark_sessions_for_termination.assert_awaited_once()
        call_args = mock_scheduling_controller.mark_sessions_for_termination.call_args
        assert len(call_args[0][0]) == 2


# =============================================================================
# TestSyncServiceDiscovery (SD-001 ~ SD-004)
# =============================================================================


class TestSyncServiceDiscovery:
    """Tests for sync_service_discovery functionality.

    Verifies the executor correctly syncs routes to service discovery.
    """

    async def test_successful_sync(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_service_discovery: AsyncMock,
        healthy_route: RouteData,
    ) -> None:
        """SD-001: Successful service discovery sync.

        Given: HEALTHY route with session
        When: Sync service discovery
        Then: Route registered with service discovery
        """
        # Arrange
        mock_discovery_info = MagicMock()
        mock_discovery_info.route_id = healthy_route.route_id
        mock_discovery_info.endpoint_id = healthy_route.endpoint_id
        mock_discovery_info.endpoint_name = "test-endpoint"
        mock_discovery_info.kernel_host = "10.0.0.1"
        mock_discovery_info.kernel_port = 8000
        mock_discovery_info.runtime_variant = "vllm"
        mock_deployment_repo.fetch_route_service_discovery_info.return_value = [mock_discovery_info]

        entity_ids = [healthy_route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            await route_executor.sync_service_discovery([healthy_route])

        # Assert
        mock_service_discovery.sync_model_service_routes.assert_awaited_once()

        # Verify discovery info passed to sync
        call_args = mock_service_discovery.sync_model_service_routes.call_args
        discovery_infos = call_args[0][0]
        assert len(discovery_infos) == 1
        assert discovery_infos[0].route_id == healthy_route.route_id

    async def test_route_without_session_skipped(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_service_discovery: AsyncMock,
        route_without_session: RouteData,
    ) -> None:
        """SD-002: Route without session is skipped.

        Given: Route without session
        When: Sync service discovery
        Then: Route not synced
        """
        entity_ids = [route_without_session.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            await route_executor.sync_service_discovery([route_without_session])

        # Assert
        mock_deployment_repo.fetch_route_service_discovery_info.assert_not_awaited()
        mock_service_discovery.sync_model_service_routes.assert_not_awaited()

    async def test_empty_route_list_returns_empty(
        self,
        route_executor: RouteExecutor,
        mock_service_discovery: AsyncMock,
    ) -> None:
        """SD-003: Empty route list returns empty result.

        Given: Empty route list
        When: Sync service discovery
        Then: Empty result, no sync
        """
        # Act
        result = await route_executor.sync_service_discovery([])

        # Assert
        assert len(result.successes) == 0
        mock_service_discovery.sync_model_service_routes.assert_not_awaited()

    async def test_multiple_routes_synced(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_service_discovery: AsyncMock,
        healthy_routes_multiple: list[RouteData],
    ) -> None:
        """SD-004: Multiple routes synced together.

        Given: Multiple HEALTHY routes
        When: Sync service discovery
        Then: All routes synced
        """
        # Arrange
        mock_discovery_infos = []
        for route in healthy_routes_multiple:
            info = MagicMock()
            info.route_id = route.route_id
            info.endpoint_id = route.endpoint_id
            info.endpoint_name = "test-endpoint"
            info.kernel_host = "10.0.0.1"
            info.kernel_port = 8000
            info.runtime_variant = "vllm"
            mock_discovery_infos.append(info)
        mock_deployment_repo.fetch_route_service_discovery_info.return_value = mock_discovery_infos

        entity_ids = [r.route_id for r in healthy_routes_multiple]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            await route_executor.sync_service_discovery(healthy_routes_multiple)

        # Assert
        mock_service_discovery.sync_model_service_routes.assert_awaited_once()
        call_args = mock_service_discovery.sync_model_service_routes.call_args
        assert len(call_args[0][0]) == 2
