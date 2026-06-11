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

import pytest

from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.recorder.context import DeploymentRecorderContext
from ai.backend.manager.sokovan.deployment.types import (
    DeploymentExecutionError,
    DeploymentWithHistory,
)

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
        destroying_deployment: DeploymentWithHistory,
        proxy_targets_by_scaling_group: dict[str, ScalingGroupProxyTarget],
    ) -> None:
        """DD-001: Successful deployment destruction.

        Given: DESTROYING deployment
        When: Destroy deployment
        Then: Routes terminated, endpoint unregistered
        """
        # Arrange
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = (
            proxy_targets_by_scaling_group
        )

        async def _fake_dispatch(
            addr: str,
            token: str,
            group: list[DeploymentWithHistory],
            successes: list[DeploymentWithHistory],
            errors: list[object],
        ) -> None:
            successes.extend(group)

        with patch.object(
            deployment_executor, "_dispatch_bulk_unregister", side_effect=_fake_dispatch
        ) as mock_unregister:
            entity_ids = [destroying_deployment.deployment_info.id]
            with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
                # Act
                result = await deployment_executor.destroy_deployment([destroying_deployment])

        # Assert
        assert len(result.successes) == 1
        assert len(result.failures) == 0
        mock_unregister.assert_awaited_once()

        # The destroyed deployment's replica groups are retired (drained + revision cleared).
        mock_deployment_repo.retire_replica_groups_on_destroy.assert_awaited_once_with({
            destroying_deployment.deployment_info.id
        })

    async def test_multiple_deployments_destroyed(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        destroying_deployments_multiple: list[DeploymentWithHistory],
        proxy_targets_by_scaling_group: dict[str, ScalingGroupProxyTarget],
    ) -> None:
        """DD-002: Multiple deployments destroyed in parallel.

        Given: Multiple DESTROYING deployments
        When: Destroy deployments
        Then: All destroyed successfully
        """
        # Arrange
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = (
            proxy_targets_by_scaling_group
        )

        async def _fake_dispatch_multi(
            addr: str,
            token: str,
            group: list[DeploymentWithHistory],
            successes: list[DeploymentWithHistory],
            errors: list[object],
        ) -> None:
            successes.extend(group)

        with patch.object(
            deployment_executor, "_dispatch_bulk_unregister", side_effect=_fake_dispatch_multi
        ):
            entity_ids = [dep.deployment_info.id for dep in destroying_deployments_multiple]
            with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
                # Act
                result = await deployment_executor.destroy_deployment(
                    destroying_deployments_multiple
                )

        # Assert
        assert len(result.successes) == 2
        assert len(result.failures) == 0

    async def test_unregister_failure_captured(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        destroying_deployment: DeploymentWithHistory,
        proxy_targets_by_scaling_group: dict[str, ScalingGroupProxyTarget],
    ) -> None:
        """DD-003: Unregister failure is captured.

        Given: DESTROYING deployment with unregister failure
        When: Destroy deployment
        Then: Error captured in result
        """
        # Arrange
        mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = (
            proxy_targets_by_scaling_group
        )

        async def _fake_dispatch_failure(
            addr: str,
            token: str,
            group: list[DeploymentWithHistory],
            successes: list[DeploymentWithHistory],
            errors: list[object],
        ) -> None:
            for deployment in group:
                errors.append(
                    DeploymentExecutionError(
                        deployment_info=deployment,
                        reason="Failed to unregister endpoint",
                        error_detail="Unregister failed",
                        error_code=None,
                    )
                )

        with patch.object(
            deployment_executor, "_dispatch_bulk_unregister", side_effect=_fake_dispatch_failure
        ):
            entity_ids = [destroying_deployment.deployment_info.id]
            with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
                # Act
                result = await deployment_executor.destroy_deployment([destroying_deployment])

        # Assert
        assert len(result.successes) == 0
        assert len(result.failures) == 1
        assert "Unregister" in result.failures[0].error_detail


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
        ready_deployment: DeploymentWithHistory,
    ) -> None:
        """Autoscaling: Manual scaling applied when no rules.

        Given: Deployment with no autoscaling rules
        When: Calculate desired replicas
        Then: Manual replica count applied
        """
        # Arrange - No autoscaling rules, routes don't match
        mock_deployment_repo.fetch_auto_scaling_rules_by_deployment_ids.return_value = {}
        mock_metrics = MagicMock()
        mock_metrics.routes_by_deployment = {ready_deployment.deployment_info.id: []}  # 0 routes
        mock_deployment_repo.fetch_metrics_for_autoscaling.return_value = mock_metrics

        entity_ids = [ready_deployment.deployment_info.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            # Act
            result = await deployment_executor.calculate_desired_replicas([ready_deployment])

        # Assert
        assert len(result.successes) == 1
        mock_deployment_repo.update_desired_replicas_bulk.assert_awaited_once()

        # Verify replica update contains the deployment id
        call_args = mock_deployment_repo.update_desired_replicas_bulk.call_args
        replica_updates = call_args[0][0]
        assert ready_deployment.deployment_info.id in replica_updates

    async def test_no_change_needed_returns_skipped(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        ready_deployment: DeploymentWithHistory,
    ) -> None:
        """Autoscaling: No change returns skipped.

        Given: Deployment with matching replica count
        When: Calculate desired replicas
        Then: Deployment in skipped list
        """
        # Arrange - Routes match replica count
        mock_deployment_repo.fetch_auto_scaling_rules_by_deployment_ids.return_value = {}
        mock_metrics = MagicMock()
        mock_metrics.routes_by_deployment = {
            ready_deployment.deployment_info.id: [MagicMock(), MagicMock()]
        }  # 2 routes = 2 replicas
        mock_deployment_repo.fetch_metrics_for_autoscaling.return_value = mock_metrics

        entity_ids = [ready_deployment.deployment_info.id]
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
        ready_deployment: DeploymentWithHistory,
    ) -> None:
        """Autoscaling: Calculation failure is captured.

        Given: Deployment with calculation error
        When: Calculate desired replicas
        Then: Error captured in result
        """
        # Arrange
        mock_deployment_repo.fetch_auto_scaling_rules_by_deployment_ids.return_value = {}
        mock_deployment_repo.fetch_metrics_for_autoscaling.side_effect = RuntimeError(
            "Metrics fetch failed"
        )

        entity_ids = [ready_deployment.deployment_info.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            # Act / Assert - Should handle exception
            with pytest.raises(RuntimeError):
                await deployment_executor.calculate_desired_replicas([ready_deployment])

    async def test_current_revision_none_is_skipped_before_calculation(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
        ready_deployment_no_current_revision: DeploymentWithHistory,
    ) -> None:
        """Regression: calculate_desired_replicas must not promote revisionless
        deployments into SCALING.

        Given: READY deployment with current_revision_id = None
        When: calculate_desired_replicas runs
        Then: the deployment is skipped (no desired-replicas write, no
              SCALING transition). Without this guard the manual-scaling
              branch would return replica_count as "desired" and the
              coordinator would flip the deployment into SCALING — where
              ``scale_deployment`` would then skip it forever because it
              also refuses to act on a None revision id.
        """
        mock_deployment_repo.fetch_auto_scaling_rules_by_deployment_ids.return_value = {}
        mock_metrics = MagicMock()
        mock_metrics.routes_by_deployment = {
            ready_deployment_no_current_revision.deployment_info.id: []
        }
        mock_deployment_repo.fetch_metrics_for_autoscaling.return_value = mock_metrics

        entity_ids = [ready_deployment_no_current_revision.deployment_info.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            result = await deployment_executor.calculate_desired_replicas([
                ready_deployment_no_current_revision
            ])

        assert len(result.successes) == 0
        assert len(result.skipped) == 1
        assert (
            result.skipped[0].deployment_info.id
            == ready_deployment_no_current_revision.deployment_info.id
        )
        # Critical: no desired-replica write. That is what was previously
        # flipping the deployment into SCALING and wedging it.
        mock_deployment_repo.update_desired_replicas_bulk.assert_not_awaited()
