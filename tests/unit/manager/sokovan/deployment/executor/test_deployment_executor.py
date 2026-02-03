"""Unit tests for Sokovan DeploymentExecutor.

Based on BEP-1033 test scenarios for deployment executor testing.

Test Scenarios:
- CD-001 ~ CD-003: Check Pending Deployments
- CR-001 ~ CR-004: Check Replica Deployments
- SC-001 ~ SC-004: Scaling Deployments
- DD-001 ~ DD-003: Destroying Deployments
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.recorder.context import DeploymentRecorderContext

# =============================================================================
# TestCheckPendingDeployments (CD-001 ~ CD-003)
# =============================================================================


class TestCheckPendingDeployments:
    """Tests for check_pending_deployments functionality.

    Verifies the executor correctly registers endpoints for PENDING deployments.
    """

    async def test_successful_endpoint_registration(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        pending_deployment: DeploymentInfo,
        proxy_targets_by_scaling_group: dict[str, ScalingGroupProxyTarget],
    ) -> None:
        """CD-001: Successful endpoint registration for new deployment.

        Given: PENDING deployment with valid revision
        When: Check pending deployments
        Then: Endpoint registered, URL updated
        """
        # Arrange
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = (
            proxy_targets_by_scaling_group
        )

        # Mock _register_endpoint via patching
        expected_url = "http://endpoint.test/v1"
        with patch.object(
            deployment_executor, "_register_endpoint", return_value=expected_url
        ) as mock_register:
            entity_ids = [pending_deployment.id]
            with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
                # Act
                result = await deployment_executor.check_pending_deployments([pending_deployment])

        # Assert
        assert len(result.successes) == 1
        assert len(result.errors) == 0
        mock_register.assert_awaited_once()
        mock_deployment_repo.update_endpoint_urls_bulk.assert_awaited_once()

        # Verify URL update contains the deployment id and expected URL
        call_args = mock_deployment_repo.update_endpoint_urls_bulk.call_args
        url_updates = call_args[0][0]
        assert pending_deployment.id in url_updates
        assert url_updates[pending_deployment.id] == expected_url

    async def test_deployment_without_revision_skipped(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        pending_deployment_no_revision: DeploymentInfo,
        proxy_targets_by_scaling_group: dict[str, ScalingGroupProxyTarget],
    ) -> None:
        """CD-002: Deployment without target revision is skipped.

        Given: PENDING deployment without target revision
        When: Check pending deployments
        Then: Deployment skipped (no endpoint registration)
        """
        # Arrange
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = (
            proxy_targets_by_scaling_group
        )

        entity_ids = [pending_deployment_no_revision.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await deployment_executor.check_pending_deployments([
                pending_deployment_no_revision
            ])

        # Assert - No successful registrations
        assert len(result.successes) == 0
        assert len(result.errors) == 0
        mock_deployment_repo.update_endpoint_urls_bulk.assert_not_awaited()

    async def test_no_proxy_target_deployment_skipped(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        pending_deployment: DeploymentInfo,
    ) -> None:
        """CD-003: Deployment with no proxy target is skipped.

        Given: PENDING deployment with no available proxy target
        When: Check pending deployments
        Then: Deployment skipped
        """
        # Arrange - Proxy target key exists but with None/empty value
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {
            "default": None,
        }

        entity_ids = [pending_deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await deployment_executor.check_pending_deployments([pending_deployment])

        # Assert
        assert len(result.successes) == 0
        assert len(result.errors) == 0

    async def test_endpoint_registration_failure_captured(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        pending_deployment: DeploymentInfo,
        proxy_targets_by_scaling_group: dict[str, ScalingGroupProxyTarget],
    ) -> None:
        """CD-003 (alt): Endpoint registration failure is captured as error.

        Given: PENDING deployment with registration failure
        When: Check pending deployments
        Then: Error captured in result
        """
        # Arrange
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = (
            proxy_targets_by_scaling_group
        )

        with patch.object(
            deployment_executor,
            "_register_endpoint",
            side_effect=RuntimeError("Registration failed"),
        ):
            entity_ids = [pending_deployment.id]
            with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
                # Act
                result = await deployment_executor.check_pending_deployments([pending_deployment])

        # Assert
        assert len(result.successes) == 0
        assert len(result.errors) == 1
        assert "Registration failed" in result.errors[0].reason


# =============================================================================
# TestCheckReadyDeployments (CR-001 ~ CR-004)
# =============================================================================


class TestCheckReadyDeployments:
    """Tests for check_ready_deployments_that_need_scaling functionality.

    Verifies the executor correctly checks replica counts.
    """

    async def test_replica_count_matches(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        ready_deployment: DeploymentInfo,
    ) -> None:
        """CR-001: Replica count matches target.

        Given: READY deployment with matching replica count
        When: Check ready deployments
        Then: No error, deployment in successes
        """
        # Arrange - Routes matching replica count
        mock_route = MagicMock()
        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            ready_deployment.id: [mock_route, mock_route]  # 2 routes = 2 target
        }

        entity_ids = [ready_deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await deployment_executor.check_ready_deployments_that_need_scaling([
                ready_deployment
            ])

        # Assert
        assert len(result.successes) == 1
        assert len(result.errors) == 0

    async def test_replica_count_mismatch_captured(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        ready_deployment: DeploymentInfo,
    ) -> None:
        """CR-002: Replica count mismatch is captured as error.

        Given: READY deployment with fewer routes than target
        When: Check ready deployments
        Then: Error captured (ReplicaCountMismatch)
        """
        # Arrange - Fewer routes than target
        mock_route = MagicMock()
        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            ready_deployment.id: [mock_route]  # 1 route != 2 target
        }

        entity_ids = [ready_deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await deployment_executor.check_ready_deployments_that_need_scaling([
                ready_deployment
            ])

        # Assert
        assert len(result.successes) == 0
        assert len(result.errors) == 1
        assert "Mismatched" in result.errors[0].reason

    async def test_empty_deployment_list(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """CR-003: Empty deployment list returns empty result.

        Given: Empty deployment list
        When: Check ready deployments
        Then: Empty result
        """
        with DeploymentRecorderContext.scope("test", entity_ids=[]):
            # Act
            result = await deployment_executor.check_ready_deployments_that_need_scaling([])

        # Assert
        assert len(result.successes) == 0
        assert len(result.errors) == 0


# =============================================================================
# TestScaleDeployment (SC-001 ~ SC-004)
# =============================================================================


class TestScaleDeployment:
    """Tests for scale_deployment functionality.

    Verifies the executor correctly handles scale up/down operations.
    """

    async def test_scale_out_creates_routes(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        ready_deployment_needs_scale_up: DeploymentInfo,
    ) -> None:
        """SC-001: Scale out creates new routes.

        Given: Deployment with fewer routes than target (1 route, target 3)
        When: Scale deployment
        Then: 2 new routes created (scale_out_creators has 2 items)
        """
        # Arrange - 1 route exists, target is 3, so need 2 new routes
        mock_route = MagicMock()
        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            ready_deployment_needs_scale_up.id: [mock_route]
        }

        entity_ids = [ready_deployment_needs_scale_up.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await deployment_executor.scale_deployment([ready_deployment_needs_scale_up])

        # Assert
        assert len(result.successes) == 1
        mock_deployment_repo.scale_routes.assert_awaited_once()

        # Verify scale_out count: target(3) - current(1) = 2 new routes
        call_args = mock_deployment_repo.scale_routes.call_args
        scale_out_creators = call_args[0][0]
        assert len(scale_out_creators) == 2

    async def test_scale_in_terminates_routes(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        ready_deployment_needs_scale_down: DeploymentInfo,
    ) -> None:
        """SC-002: Scale in terminates excess routes.

        Given: Deployment with more routes than target (3 routes, target 1)
        When: Scale deployment
        Then: 2 excess routes marked for termination
        """
        # Arrange - 3 routes exist, target is 1, so need to terminate 2 routes
        mock_route1 = MagicMock()
        mock_route1.route_id = uuid4()
        mock_route1.status = MagicMock()
        mock_route1.status.termination_priority = MagicMock(return_value=1)
        mock_route2 = MagicMock()
        mock_route2.route_id = uuid4()
        mock_route2.status = MagicMock()
        mock_route2.status.termination_priority = MagicMock(return_value=2)
        mock_route3 = MagicMock()
        mock_route3.route_id = uuid4()
        mock_route3.status = MagicMock()
        mock_route3.status.termination_priority = MagicMock(return_value=3)

        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            ready_deployment_needs_scale_down.id: [mock_route1, mock_route2, mock_route3]
        }

        entity_ids = [ready_deployment_needs_scale_down.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await deployment_executor.scale_deployment([ready_deployment_needs_scale_down])

        # Assert
        assert len(result.successes) == 1
        mock_deployment_repo.scale_routes.assert_awaited_once()

        # Verify scale_in count: current(3) - target(1) = 2 routes terminated
        call_args = mock_deployment_repo.scale_routes.call_args
        scale_in_updater = call_args[0][1]
        # scale_in_updater contains RouteConditions.by_ids with 2 route ids
        assert scale_in_updater is not None

    async def test_no_scaling_needed_returns_skipped(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        ready_deployment: DeploymentInfo,
    ) -> None:
        """SC-003: No scaling needed returns skipped.

        Given: Deployment with matching route count
        When: Scale deployment
        Then: Deployment in skipped list
        """
        # Arrange - Routes match target
        mock_route1 = MagicMock()
        mock_route2 = MagicMock()
        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            ready_deployment.id: [mock_route1, mock_route2]
        }

        entity_ids = [ready_deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await deployment_executor.scale_deployment([ready_deployment])

        # Assert
        assert len(result.successes) == 0
        assert len(result.skipped) == 1

    async def test_scaling_failure_captured(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        ready_deployment_needs_scale_up: DeploymentInfo,
    ) -> None:
        """SC-004: Scaling failure is captured.

        Given: Deployment with scaling error
        When: Scale deployment
        Then: Error captured in result
        """
        # Arrange - Route fetch raises exception
        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {}

        entity_ids = [ready_deployment_needs_scale_up.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await deployment_executor.scale_deployment([ready_deployment_needs_scale_up])

        # Assert - KeyError since deployment.id not in empty dict
        assert len(result.errors) == 1


# =============================================================================
# TestDestroyDeployment (DD-001 ~ DD-003)
# =============================================================================


class TestDestroyDeployment:
    """Tests for destroy_deployment functionality.

    Verifies the executor correctly handles deployment destruction.
    """

    async def test_successful_destruction(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        destroying_deployment: DeploymentInfo,
        proxy_targets_by_scaling_group: dict[str, ScalingGroupProxyTarget],
    ) -> None:
        """DD-001: Successful deployment destruction.

        Given: DESTROYING deployment
        When: Destroy deployment
        Then: Routes terminated, endpoint unregistered
        """
        # Arrange
        mock_route = MagicMock()
        mock_route.route_id = uuid4()
        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            destroying_deployment.id: [mock_route]
        }
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = (
            proxy_targets_by_scaling_group
        )

        with patch.object(
            deployment_executor, "_unregister_endpoint", return_value=None
        ) as mock_unregister:
            entity_ids = [destroying_deployment.id]
            with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
                # Act
                result = await deployment_executor.destroy_deployment([destroying_deployment])

        # Assert
        assert len(result.successes) == 1
        assert len(result.errors) == 0
        mock_deployment_repo.mark_terminating_route_status_bulk.assert_awaited_once()
        mock_unregister.assert_awaited_once()

        # Verify 1 route marked for termination
        call_args = mock_deployment_repo.mark_terminating_route_status_bulk.call_args
        route_ids = call_args[0][0]
        assert len(route_ids) == 1
        assert mock_route.route_id in route_ids

    async def test_multiple_deployments_destroyed(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        destroying_deployments_multiple: list[DeploymentInfo],
        proxy_targets_by_scaling_group: dict[str, ScalingGroupProxyTarget],
    ) -> None:
        """DD-002: Multiple deployments destroyed in parallel.

        Given: Multiple DESTROYING deployments
        When: Destroy deployments
        Then: All destroyed successfully
        """
        # Arrange
        routes_map = {}
        for deployment in destroying_deployments_multiple:
            mock_route = MagicMock()
            mock_route.route_id = uuid4()
            routes_map[deployment.id] = [mock_route]

        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = routes_map
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = (
            proxy_targets_by_scaling_group
        )

        with patch.object(deployment_executor, "_unregister_endpoint", return_value=None):
            entity_ids = [d.id for d in destroying_deployments_multiple]
            with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
                # Act
                result = await deployment_executor.destroy_deployment(
                    destroying_deployments_multiple
                )

        # Assert
        assert len(result.successes) == 2
        assert len(result.errors) == 0

    async def test_unregister_failure_captured(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        destroying_deployment: DeploymentInfo,
        proxy_targets_by_scaling_group: dict[str, ScalingGroupProxyTarget],
    ) -> None:
        """DD-003: Unregister failure is captured.

        Given: DESTROYING deployment with unregister failure
        When: Destroy deployment
        Then: Error captured in result
        """
        # Arrange
        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            destroying_deployment.id: []
        }
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = (
            proxy_targets_by_scaling_group
        )

        with patch.object(
            deployment_executor,
            "_unregister_endpoint",
            side_effect=RuntimeError("Unregister failed"),
        ):
            entity_ids = [destroying_deployment.id]
            with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
                # Act
                result = await deployment_executor.destroy_deployment([destroying_deployment])

        # Assert
        assert len(result.successes) == 0
        assert len(result.errors) == 1
        assert "Unregister" in result.errors[0].error_detail


# =============================================================================
# TestCalculateDesiredReplicas (Autoscaling)
# =============================================================================


class TestCalculateDesiredReplicas:
    """Tests for calculate_desired_replicas functionality.

    Verifies the executor correctly calculates desired replica counts.
    """

    async def test_manual_scaling_applied(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        ready_deployment: DeploymentInfo,
    ) -> None:
        """Autoscaling: Manual scaling applied when no rules.

        Given: Deployment with no autoscaling rules
        When: Calculate desired replicas
        Then: Manual replica count applied
        """
        # Arrange - No autoscaling rules, routes don't match
        mock_deployment_repo.fetch_auto_scaling_rules_by_endpoint_ids.return_value = {}
        mock_metrics = MagicMock()
        mock_metrics.routes_by_endpoint = {ready_deployment.id: []}  # 0 routes
        mock_deployment_repo.fetch_metrics_for_autoscaling.return_value = mock_metrics

        entity_ids = [ready_deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await deployment_executor.calculate_desired_replicas([ready_deployment])

        # Assert
        assert len(result.successes) == 1
        mock_deployment_repo.update_desired_replicas_bulk.assert_awaited_once()

        # Verify replica update contains the deployment id
        call_args = mock_deployment_repo.update_desired_replicas_bulk.call_args
        replica_updates = call_args[0][0]
        assert ready_deployment.id in replica_updates

    async def test_no_change_needed_returns_skipped(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        ready_deployment: DeploymentInfo,
    ) -> None:
        """Autoscaling: No change returns skipped.

        Given: Deployment with matching replica count
        When: Calculate desired replicas
        Then: Deployment in skipped list
        """
        # Arrange - Routes match replica count
        mock_deployment_repo.fetch_auto_scaling_rules_by_endpoint_ids.return_value = {}
        mock_metrics = MagicMock()
        mock_metrics.routes_by_endpoint = {
            ready_deployment.id: [MagicMock(), MagicMock()]
        }  # 2 routes = 2 replicas
        mock_deployment_repo.fetch_metrics_for_autoscaling.return_value = mock_metrics

        entity_ids = [ready_deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await deployment_executor.calculate_desired_replicas([ready_deployment])

        # Assert
        assert len(result.skipped) == 1
        mock_deployment_repo.update_desired_replicas_bulk.assert_not_awaited()

    async def test_calculation_failure_captured(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        ready_deployment: DeploymentInfo,
    ) -> None:
        """Autoscaling: Calculation failure is captured.

        Given: Deployment with calculation error
        When: Calculate desired replicas
        Then: Error captured in result
        """
        # Arrange
        mock_deployment_repo.fetch_auto_scaling_rules_by_endpoint_ids.return_value = {}
        mock_deployment_repo.fetch_metrics_for_autoscaling.side_effect = RuntimeError(
            "Metrics fetch failed"
        )

        entity_ids = [ready_deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            # Act / Assert - Should handle exception
            with pytest.raises(RuntimeError):
                await deployment_executor.calculate_desired_replicas([ready_deployment])
