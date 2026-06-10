"""Unit tests for Sokovan RouteExecutor.

Based on BEP-1033 test scenarios for route executor testing.

Test Scenarios:
- RP-001 ~ RP-004: Route Provisioning
- RH-001 ~ RH-004: Route Health Check
- RR-001 ~ RR-004: Running Route Check
- RE-001 ~ RE-003: Route Eviction
- RT-001 ~ RT-003: Route Termination
- SD-001 ~ SD-004: Service Discovery Sync
- AP-001 ~ AP-004: AppProxy Sync
"""

from __future__ import annotations

import dataclasses
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.clients.valkey_client.valkey_schedule import (
    ReplicaHealthStatus as ValkeyReplicaHealthStatus,
)
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.response import (
    BulkUpdateRoutesResponse,
)
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import UpdatedRoutesItem
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.model_serving.types import AppProxyRouteEntry
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
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

    @pytest.mark.skip(
        reason=(
            "Rewrite pending: the new provision_routes path builds a full"
            " SessionSpec draft (DeploymentSessionDraftBuilder) that validates"
            " mount/model fields. MagicMock deployments no longer satisfy the"
            " pydantic validation, so mocks must be replaced with typed"
            " DeploymentInfo/ModelRevisionSpec fixtures."
        ),
    )
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
        deployment.id = provisioning_route.deployment_id
        mock_deployment_repo.get_deployments_by_ids.return_value = [deployment]

        expected_session_id = SessionId(uuid4())
        mock_scheduling_controller.enqueue_session_from_draft.return_value = expected_session_id

        entity_ids = [provisioning_route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.provision_routes([provisioning_route])

        # Assert
        assert len(result.successes) == 1
        assert len(result.errors) == 0
        mock_scheduling_controller.enqueue_session_from_draft.assert_awaited_once()
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
        deployment.id = provisioning_route_with_session.deployment_id
        mock_deployment_repo.get_deployments_by_ids.return_value = [deployment]

        entity_ids = [provisioning_route_with_session.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.provision_routes([provisioning_route_with_session])

        # Assert
        assert len(result.successes) == 1
        mock_scheduling_controller.enqueue_session_from_draft.assert_not_awaited()

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
        mock_deployment_repo.get_deployments_by_ids.return_value = []  # No deployment found

        entity_ids = [provisioning_route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.provision_routes([provisioning_route])

        # Assert
        assert len(result.successes) == 0
        assert len(result.errors) == 1

    @pytest.mark.skip(
        reason=(
            "Rewrite pending: same DeploymentSessionDraftBuilder validation"
            " issue as test_successful_provisioning."
        ),
    )
    async def test_provision_route_passes_revision_id_to_context(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_scheduling_controller: AsyncMock,
        provisioning_route: RouteData,
    ) -> None:
        """RP-004: Provisioning passes route's revision_id to fetch_deployment_context."""
        # Arrange
        explicit_revision_id = DeploymentRevisionID(uuid4())
        route = dataclasses.replace(provisioning_route, revision_id=explicit_revision_id)
        deployment = MagicMock()
        deployment.id = route.deployment_id
        mock_deployment_repo.get_deployments_by_ids.return_value = [deployment]

        entity_ids = [route.route_id]
        with RouteRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await route_executor.provision_routes([route])

        # Assert
        assert len(result.successes) == 1
        assert len(result.errors) == 0
        mock_deployment_repo.fetch_deployment_context.assert_awaited_once_with(
            deployment,
            revision_id=explicit_revision_id,
        )


# =============================================================================
# TestCheckRouteHealth (RH-001 ~ RH-004)
# =============================================================================


class TestCheckRouteHealth:
    """Tests for check_route_health functionality.

    Verifies the executor correctly checks route health via Valkey
    using RouteHealthStatus TTL-based classification.
    """

    async def test_healthy_route_in_successes(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
        healthy_route: RouteData,
    ) -> None:
        """RH-001: Healthy route is in successes.

        Given: Route with RouteHealthStatus(healthy=True) in Valkey
        When: Check route health
        Then: Route in successes list
        """
        route = dataclasses.replace(healthy_route, health_check=ModelHealthCheck(enable=True))
        status = ValkeyReplicaHealthStatus(
            replica_id=route.route_id,
            healthy=True,
            last_check=995,
        )
        mock_valkey_schedule.get_route_health_statuses_batch.return_value = {route.route_id: status}

        with RouteRecorderContext.scope("test", entity_ids=[route.route_id]):
            result = await route_executor.check_route_health([route])

        assert len(result.successes) == 1
        assert len(result.errors) == 0
        assert len(result.stale) == 0

    async def test_unhealthy_route_in_errors(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
        healthy_route: RouteData,
    ) -> None:
        """RH-002: Route whose failures exhausted max_retries is in errors.

        Given: Enabled health check with max_retries=1 and a failing status
               whose consecutive_failures reached the budget
        When: Check route health
        Then: Route in errors list
        """
        route = dataclasses.replace(
            healthy_route, health_check=ModelHealthCheck(enable=True, max_retries=1)
        )
        status = ValkeyReplicaHealthStatus(
            replica_id=route.route_id,
            healthy=False,
            last_check=995,
            consecutive_failures=1,
        )
        mock_valkey_schedule.get_route_health_statuses_batch.return_value = {route.route_id: status}

        with RouteRecorderContext.scope("test", entity_ids=[route.route_id]):
            result = await route_executor.check_route_health([route])

        assert len(result.successes) == 0
        assert len(result.errors) == 1
        assert len(result.stale) == 0

    async def test_disabled_health_check_is_skipped(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
        healthy_route: RouteData,
    ) -> None:
        """A route with health_check present but enable=False is skipped (unmanaged)."""
        route = dataclasses.replace(healthy_route, health_check=ModelHealthCheck(enable=False))
        mock_valkey_schedule.get_route_health_statuses_batch.return_value = {}

        with RouteRecorderContext.scope("test", entity_ids=[route.route_id]):
            result = await route_executor.check_route_health([route])

        assert len(result.successes) == 0
        assert len(result.errors) == 0
        assert len(result.stale) == 0

    async def test_absent_health_check_is_skipped(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
        healthy_route: RouteData,
    ) -> None:
        """A route with no health check is skipped, neither HEALTHY nor DEGRADED."""
        mock_valkey_schedule.get_route_health_statuses_batch.return_value = {}

        with RouteRecorderContext.scope("test", entity_ids=[healthy_route.route_id]):
            result = await route_executor.check_route_health([healthy_route])

        assert len(result.successes) == 0
        assert len(result.errors) == 0
        assert len(result.stale) == 0

    async def test_failing_route_within_retry_budget_stays_healthy(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
        healthy_route: RouteData,
    ) -> None:
        """A failing probe below max_retries keeps the route HEALTHY (within budget)."""
        route = dataclasses.replace(
            healthy_route, health_check=ModelHealthCheck(enable=True, max_retries=3)
        )
        status = ValkeyReplicaHealthStatus(
            replica_id=route.route_id,
            healthy=False,
            last_check=995,
            consecutive_failures=2,
        )
        mock_valkey_schedule.get_route_health_statuses_batch.return_value = {route.route_id: status}

        with RouteRecorderContext.scope("test", entity_ids=[route.route_id]):
            result = await route_executor.check_route_health([route])

        assert len(result.successes) == 1
        assert len(result.errors) == 0
        assert len(result.stale) == 0

    async def test_failing_route_exhausts_retries_in_errors(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
        healthy_route: RouteData,
    ) -> None:
        """Once consecutive_failures reaches max_retries the route is UNHEALTHY."""
        route = dataclasses.replace(
            healthy_route, health_check=ModelHealthCheck(enable=True, max_retries=3)
        )
        status = ValkeyReplicaHealthStatus(
            replica_id=route.route_id,
            healthy=False,
            last_check=995,
            consecutive_failures=3,
        )
        mock_valkey_schedule.get_route_health_statuses_batch.return_value = {route.route_id: status}

        with RouteRecorderContext.scope("test", entity_ids=[route.route_id]):
            result = await route_executor.check_route_health([route])

        assert len(result.successes) == 0
        assert len(result.errors) == 1
        assert len(result.stale) == 0

    async def test_stale_route_in_stale_list(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
        healthy_route: RouteData,
    ) -> None:
        """RH-003: Enabled-health-check route with expired TTL (no key) is in stale list.

        Given: Route with an active health check whose RouteHealthStatus
               TTL has expired (key absent)
        When: Check route health
        Then: Route in stale list (DEGRADED)
        """
        route = dataclasses.replace(healthy_route, health_check=ModelHealthCheck(enable=True))
        mock_valkey_schedule.get_route_health_statuses_batch.return_value = {}

        with RouteRecorderContext.scope("test", entity_ids=[route.route_id]):
            result = await route_executor.check_route_health([route])

        assert len(result.successes) == 0
        assert len(result.errors) == 0
        assert len(result.stale) == 1

    async def test_missing_health_data_treated_as_stale(
        self,
        route_executor: RouteExecutor,
        mock_valkey_schedule: AsyncMock,
        healthy_route: RouteData,
    ) -> None:
        """RH-004: Missing health data for an active health check is treated as stale.

        Given: Route with an active health check and no RouteHealthStatus in Valkey
        When: Check route health
        Then: Route in stale list
        """
        route = dataclasses.replace(healthy_route, health_check=ModelHealthCheck(enable=True))
        mock_valkey_schedule.get_route_health_statuses_batch.return_value = {}

        with RouteRecorderContext.scope("test", entity_ids=[route.route_id]):
            result = await route_executor.check_route_health([route])

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
        current_revision_mock = MagicMock()
        current_revision_mock.id = unhealthy_route.revision_id

        deployment = MagicMock()
        deployment.id = unhealthy_route.deployment_id
        deployment.metadata = MagicMock()
        deployment.metadata.resource_group = "default"
        deployment.current_revision = current_revision_mock
        deployment.deploying_revision = None
        mock_deployment_repo.get_deployments_by_ids.return_value = [deployment]
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
        current_revision_mock = MagicMock()
        current_revision_mock.id = healthy_route.revision_id

        deployment = MagicMock()
        deployment.id = healthy_route.deployment_id
        deployment.metadata = MagicMock()
        deployment.metadata.resource_group = "default"
        deployment.current_revision = current_revision_mock
        deployment.deploying_revision = None
        mock_deployment_repo.get_deployments_by_ids.return_value = [deployment]
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

    async def test_orphan_revision_route_marked_for_cleanup(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        cleanup_config_unhealthy_only: MagicMock,
    ) -> None:
        """RE-004: Route whose revision is neither current nor deploying is evicted.

        Given: HEALTHY RUNNING route whose revision_id matches neither
            ``current_revision_id`` nor ``deploying_revision_id`` of its
            endpoint (e.g. leftover from a preempted rollout)
        When: Cleanup routes by config
        Then: Route is in successes (orphan eviction), independent of
            the scaling group's health policy.
        """
        deployment_id = DeploymentID(uuid4())
        current_revision_id = DeploymentRevisionID(uuid4())
        deploying_revision_id = DeploymentRevisionID(uuid4())
        orphan_route = RouteData(
            route_id=ReplicaID(uuid4()),
            deployment_id=deployment_id,
            session_id=SessionId(uuid4()),
            status=RouteStatus.RUNNING,
            health_status=RouteHealthStatus.HEALTHY,
            traffic_ratio=1.0,
            created_at=datetime.now(tzutc()),
            revision_id=DeploymentRevisionID(uuid4()),  # neither current nor deploying
            traffic_status=RouteTrafficStatus.ACTIVE,
            health_check=None,
        )

        current_revision_mock = MagicMock()
        current_revision_mock.id = current_revision_id
        deploying_revision_mock = MagicMock()
        deploying_revision_mock.id = deploying_revision_id

        deployment = MagicMock()
        deployment.id = deployment_id
        deployment.metadata = MagicMock()
        deployment.metadata.resource_group = "default"
        deployment.current_revision = current_revision_mock
        deployment.deploying_revision = deploying_revision_mock
        mock_deployment_repo.get_deployments_by_ids.return_value = [deployment]
        mock_deployment_repo.get_scaling_group_cleanup_configs.return_value = {
            "default": cleanup_config_unhealthy_only
        }

        with RouteRecorderContext.scope("test", entity_ids=[orphan_route.route_id]):
            result = await route_executor.cleanup_routes_by_config([orphan_route])

        assert len(result.successes) == 1
        assert result.successes[0].route_id == orphan_route.route_id

    async def test_provisioning_route_for_deploying_revision_kept(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        cleanup_config_unhealthy_only: MagicMock,
    ) -> None:
        """RE-005: PROVISIONING route on the deploying revision is not orphan.

        Given: PROVISIONING route whose ``revision_id`` matches the
            endpoint's ``deploying_revision_id`` (active rollout)
        When: Cleanup routes by config
        Then: Route is not flagged — neither orphan nor health-policy match.
        """
        deployment_id = DeploymentID(uuid4())
        deploying_revision_id = DeploymentRevisionID(uuid4())
        provisioning_route = RouteData(
            route_id=ReplicaID(uuid4()),
            deployment_id=deployment_id,
            session_id=None,
            status=RouteStatus.PROVISIONING,
            health_status=RouteHealthStatus.NOT_CHECKED,
            traffic_ratio=1.0,
            created_at=datetime.now(tzutc()),
            revision_id=deploying_revision_id,
            traffic_status=RouteTrafficStatus.INACTIVE,
            health_check=None,
        )

        deploying_revision_mock = MagicMock()
        deploying_revision_mock.id = deploying_revision_id

        deployment = MagicMock()
        deployment.id = deployment_id
        deployment.metadata = MagicMock()
        deployment.metadata.resource_group = "default"
        deployment.current_revision = None
        deployment.deploying_revision = deploying_revision_mock
        mock_deployment_repo.get_deployments_by_ids.return_value = [deployment]
        mock_deployment_repo.get_scaling_group_cleanup_configs.return_value = {
            "default": cleanup_config_unhealthy_only
        }

        with RouteRecorderContext.scope("test", entity_ids=[provisioning_route.route_id]):
            result = await route_executor.cleanup_routes_by_config([provisioning_route])

        assert len(result.successes) == 0

    async def test_orphan_check_skipped_when_no_known_revisions(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        cleanup_config_unhealthy_only: MagicMock,
    ) -> None:
        """RE-006: Endpoint with no current/deploying revisions skips orphan check.

        Given: An endpoint that has no ``current_revision_id`` and no
            ``deploying_revision_id`` yet (transient bootstrap state)
            with a HEALTHY RUNNING route attached
        When: Cleanup routes by config
        Then: The route is not evicted — the orphan check needs at least
            one known valid revision before it can declare orphans.
        """
        deployment_id = DeploymentID(uuid4())
        bootstrap_route = RouteData(
            route_id=ReplicaID(uuid4()),
            deployment_id=deployment_id,
            session_id=SessionId(uuid4()),
            status=RouteStatus.RUNNING,
            health_status=RouteHealthStatus.HEALTHY,
            traffic_ratio=1.0,
            created_at=datetime.now(tzutc()),
            revision_id=DeploymentRevisionID(uuid4()),
            traffic_status=RouteTrafficStatus.ACTIVE,
            health_check=None,
        )

        deployment = MagicMock()
        deployment.id = deployment_id
        deployment.metadata = MagicMock()
        deployment.metadata.resource_group = "default"
        deployment.current_revision = None
        deployment.deploying_revision = None
        mock_deployment_repo.get_deployments_by_ids.return_value = [deployment]
        mock_deployment_repo.get_scaling_group_cleanup_configs.return_value = {
            "default": cleanup_config_unhealthy_only
        }

        with RouteRecorderContext.scope("test", entity_ids=[bootstrap_route.route_id]):
            result = await route_executor.cleanup_routes_by_config([bootstrap_route])

        assert len(result.successes) == 0


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
        session_owner_uuid = uuid4()
        project_uuid = uuid4()
        mock_discovery_info = MagicMock()
        mock_discovery_info.route_id = healthy_route.route_id
        mock_discovery_info.deployment_id = healthy_route.deployment_id
        mock_discovery_info.endpoint_name = "test-endpoint"
        mock_discovery_info.kernel_host = "10.0.0.1"
        mock_discovery_info.kernel_port = 8000
        mock_discovery_info.runtime_variant = "vllm"
        mock_discovery_info.session_owner = session_owner_uuid
        mock_discovery_info.project = project_uuid
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
        assert discovery_infos[0].labels["session_owner"] == str(session_owner_uuid)
        assert discovery_infos[0].labels["project"] == str(project_uuid)

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
            info.deployment_id = route.deployment_id
            info.endpoint_name = "test-endpoint"
            info.kernel_host = "10.0.0.1"
            info.kernel_port = 8000
            info.runtime_variant = "vllm"
            info.session_owner = uuid4()
            info.project = uuid4()
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


# =============================================================================
# TestSyncAppproxy (AP-001 ~ AP-004)
# =============================================================================


def _route_for_endpoint(endpoint_id: DeploymentID) -> RouteData:
    return RouteData(
        route_id=ReplicaID(uuid4()),
        deployment_id=endpoint_id,
        session_id=SessionId(uuid4()),
        status=RouteStatus.RUNNING,
        health_status=RouteHealthStatus.HEALTHY,
        traffic_ratio=1.0,
        revision_id=DeploymentRevisionID(uuid4()),
        created_at=datetime.now(tzutc()),
        traffic_status=RouteTrafficStatus.ACTIVE,
        health_check=None,
    )


def _make_deployment_mock(deployment_id: UUID, resource_group: str) -> MagicMock:
    """Tiny stand-in for DeploymentInfo so sync_appproxy can read ``id`` and ``metadata.resource_group`` without dragging the full constructor."""
    deployment = MagicMock()
    deployment.id = deployment_id
    deployment.metadata.resource_group = resource_group
    return deployment


def _wire_proxy_target(
    mock_deployment_repo: AsyncMock,
    endpoint_ids: list[DeploymentID],
    *,
    resource_group: str = "default",
    addr: str = "http://appproxy:5000",
    token: str = "test-token",
) -> None:
    """Wire deployment / proxy lookups so sync_appproxy can resolve every endpoint.

    Pulled out so each test only declares the input that matters and not
    the chain of mock returns the executor walks before the HTTP call.
    """
    deployments = [_make_deployment_mock(UUID(str(eid)), resource_group) for eid in endpoint_ids]
    mock_deployment_repo.get_deployments_by_ids.return_value = deployments
    mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {
        resource_group: ScalingGroupProxyTarget(addr=addr, api_token=token),
    }
    mock_deployment_repo.fetch_route_connection_infos.return_value = {
        UUID(str(eid)): [
            AppProxyRouteEntry(
                session_id=uuid4(),
                route_id=uuid4(),
                kernel_host="10.0.0.1",
                kernel_port=8000,
            )
        ]
        for eid in endpoint_ids
    }


def _bulk_response(items: list[UpdatedRoutesItem]) -> BulkUpdateRoutesResponse:
    return BulkUpdateRoutesResponse(endpoints=items)


class TestSyncAppproxy:
    """Tests for sync_appproxy functionality.

    Verifies the executor groups routes by endpoint, resolves the proxy
    target, and issues exactly one bulk routes-sync HTTP call per
    AppProxy target instead of one event per endpoint.
    """

    async def test_empty_routes_is_noop(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_appproxy_client_pool: MagicMock,
    ) -> None:
        """AP-001: Empty route list is a no-op."""
        result = await route_executor.sync_appproxy([])

        assert result.successes == []
        assert result.errors == []
        mock_deployment_repo.get_deployments_by_ids.assert_not_awaited()
        mock_appproxy_client_pool.load_client.assert_not_called()

    async def test_single_endpoint_pushes_once(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_appproxy_client_pool: MagicMock,
    ) -> None:
        """AP-002: Multiple HEALTHY routes for one endpoint trigger one bulk call.

        Two routes for the same endpoint must collapse into a single
        bulk routes-sync HTTP request — that's the whole point of moving
        from per-endpoint events to a bulk endpoint.
        """
        endpoint_id = DeploymentID(uuid4())
        routes = [_route_for_endpoint(endpoint_id), _route_for_endpoint(endpoint_id)]
        _wire_proxy_target(mock_deployment_repo, [endpoint_id])
        client = mock_appproxy_client_pool.load_client.return_value
        client.bulk_update_routes.return_value = _bulk_response([
            UpdatedRoutesItem(deployment_id=endpoint_id, success=True)
        ])

        result = await route_executor.sync_appproxy(routes)

        assert len(result.successes) == 2
        assert result.errors == []
        client.bulk_update_routes.assert_awaited_once()
        request = client.bulk_update_routes.await_args.args[0]
        assert [item.deployment_id for item in request.endpoints] == [endpoint_id]

    async def test_multiple_endpoints_share_one_call(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_appproxy_client_pool: MagicMock,
    ) -> None:
        """AP-003: Routes for distinct endpoints sharing one proxy target use one call."""
        endpoint_ids = [DeploymentID(uuid4()) for _ in range(3)]
        routes = [_route_for_endpoint(eid) for eid in endpoint_ids]
        _wire_proxy_target(mock_deployment_repo, endpoint_ids)
        client = mock_appproxy_client_pool.load_client.return_value
        client.bulk_update_routes.return_value = _bulk_response([
            UpdatedRoutesItem(deployment_id=eid, success=True) for eid in endpoint_ids
        ])

        result = await route_executor.sync_appproxy(routes)

        assert len(result.successes) == 3
        client.bulk_update_routes.assert_awaited_once()
        request = client.bulk_update_routes.await_args.args[0]
        assert {item.deployment_id for item in request.endpoints} == set(endpoint_ids)

    async def test_per_endpoint_failure_isolated(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_appproxy_client_pool: MagicMock,
    ) -> None:
        """AP-004: One endpoint marked failed by AppProxy doesn't drop other successes."""
        endpoint_ids = [DeploymentID(uuid4()) for _ in range(3)]
        routes = [_route_for_endpoint(eid) for eid in endpoint_ids]
        _wire_proxy_target(mock_deployment_repo, endpoint_ids)
        client = mock_appproxy_client_pool.load_client.return_value
        client.bulk_update_routes.return_value = _bulk_response([
            UpdatedRoutesItem(deployment_id=endpoint_ids[0], success=False, error="circuit gone"),
            UpdatedRoutesItem(deployment_id=endpoint_ids[1], success=True),
            UpdatedRoutesItem(deployment_id=endpoint_ids[2], success=True),
        ])

        result = await route_executor.sync_appproxy(routes)

        assert len(result.successes) == 2
        assert len(result.errors) == 1
        assert result.errors[0].route_info.deployment_id == endpoint_ids[0]
