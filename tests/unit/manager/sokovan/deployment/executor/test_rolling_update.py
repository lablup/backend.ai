"""Unit tests for rolling update cycle in DeploymentExecutor.

Test Scenarios:
- RU-001: First cycle creates max_surge new routes, no termination
- RU-002: With healthy new routes, terminates old routes respecting max_unavailable
- RU-003: Completion detection when all routes are new-revision and healthy
- RU-004: max_surge=1, max_unavailable=0 (one-at-a-time with extra capacity)
- RU-005: max_surge=0, max_unavailable=1 (one-at-a-time replace)
- RU-006: Rollback when new routes all fail and rollback_on_failure=True
- RU-007: No rollback stays in DEPLOYING when rollback_on_failure=False
- RU-008: No-op when deploying_revision is None (edge case)
- RU-009: Multi-cycle simulation (successive calls show progress)
- RU-010: Concurrent old/new routes with mixed health statuses
- RU-011: max_surge=0, max_unavailable=0 raises InvalidRollingUpdateParameters
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from dateutil.tz import tzutc

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentPolicySearchResult,
    DeploymentState,
    ReplicaSpec,
    RouteInfo,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.models.deployment_policy import (
    DeploymentPolicyData,
    RollingUpdateSpec,
)
from ai.backend.manager.sokovan.deployment.executor import DeploymentExecutor
from ai.backend.manager.sokovan.deployment.recorder.context import DeploymentRecorderContext

# =============================================================================
# Helpers
# =============================================================================


def _create_deploying_deployment(
    deployment_id: UUID | None = None,
    replica_count: int = 3,
    current_revision_id: UUID | None = None,
    deploying_revision_id: UUID | None = None,
) -> DeploymentInfo:
    dep_id = deployment_id or uuid4()
    current_rev = current_revision_id or uuid4()
    deploying_rev = deploying_revision_id or uuid4()
    revision = MagicMock()

    return DeploymentInfo(
        id=dep_id,
        metadata=DeploymentMetadata(
            name="test-deployment",
            domain="default",
            project=uuid4(),
            resource_group="default",
            created_user=uuid4(),
            session_owner=uuid4(),
            created_at=datetime.now(tzutc()),
            revision_history_limit=10,
        ),
        state=DeploymentState(
            lifecycle=EndpointLifecycle.DEPLOYING,
            retry_count=0,
        ),
        replica_spec=ReplicaSpec(
            replica_count=replica_count,
        ),
        network=DeploymentNetworkSpec(
            open_to_public=False,
            url="http://test.endpoint",
        ),
        model_revisions=[revision],
        current_revision_id=current_rev,
        deploying_revision_id=deploying_rev,
    )


def _create_route_info(
    endpoint_id: UUID,
    revision_id: UUID | None = None,
    status: RouteStatus = RouteStatus.HEALTHY,
    route_id: UUID | None = None,
) -> RouteInfo:
    return RouteInfo(
        route_id=route_id or uuid4(),
        endpoint_id=endpoint_id,
        session_id=None,
        status=status,
        traffic_ratio=1.0,
        created_at=datetime.now(tzutc()),
        revision_id=revision_id,
        traffic_status=RouteTrafficStatus.ACTIVE,
    )


def _create_policy_search_result(
    policies: list[DeploymentPolicyData],
) -> DeploymentPolicySearchResult:
    return DeploymentPolicySearchResult(
        items=policies,
        total_count=len(policies),
        has_next_page=False,
        has_previous_page=False,
    )


def _create_policy(
    endpoint_id: UUID,
    max_surge: int = 1,
    max_unavailable: int = 0,
    rollback_on_failure: bool = False,
) -> DeploymentPolicyData:
    return DeploymentPolicyData(
        id=uuid4(),
        endpoint=endpoint_id,
        strategy=DeploymentStrategy.ROLLING,
        strategy_spec=RollingUpdateSpec(max_surge=max_surge, max_unavailable=max_unavailable),
        rollback_on_failure=rollback_on_failure,
        created_at=datetime.now(tzutc()),
        updated_at=datetime.now(tzutc()),
    )


# =============================================================================
# Test Class
# =============================================================================


class TestRollingUpdateCycle:
    """Tests for execute_rolling_update_cycle functionality."""

    async def test_ru001_first_cycle_creates_new_routes(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """RU-001: First cycle creates max_surge new routes, no termination.

        Given: 3 old routes (healthy), 0 new routes, max_surge=2
        When: Execute rolling update cycle
        Then: 2 new routes created, 0 old routes terminated
        """
        deployment = _create_deploying_deployment(replica_count=3)
        old_routes = [
            _create_route_info(deployment.id, deployment.current_revision_id, RouteStatus.HEALTHY)
            for _ in range(3)
        ]
        policy = _create_policy(deployment.id, max_surge=2, max_unavailable=1)

        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            deployment.id: old_routes
        }
        mock_deployment_repo.search_deployment_policies.return_value = _create_policy_search_result([
            policy
        ])

        entity_ids = [deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            result = await deployment_executor.execute_rolling_update_cycle([deployment])

        # Should be skipped (in-progress, not complete)
        assert len(result.skipped) == 1
        assert len(result.successes) == 0

        # Verify scale_routes was called
        mock_deployment_repo.scale_routes.assert_awaited_once()
        call_args = mock_deployment_repo.scale_routes.call_args
        scale_out_creators = call_args[0][0]
        # Should create max_surge=2 new routes
        assert len(scale_out_creators) == 2

    async def test_ru002_terminates_old_routes_when_new_are_healthy(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """RU-002: With healthy new routes, terminates old routes respecting max_unavailable.

        Given: 2 old routes (healthy), 2 new routes (healthy), target=3, max_unavailable=1
        When: Execute rolling update cycle
        Then: Old routes terminated respecting max_unavailable
        """
        deployment = _create_deploying_deployment(replica_count=3)
        old_routes = [
            _create_route_info(deployment.id, deployment.current_revision_id, RouteStatus.HEALTHY)
            for _ in range(2)
        ]
        new_routes = [
            _create_route_info(deployment.id, deployment.deploying_revision_id, RouteStatus.HEALTHY)
            for _ in range(2)
        ]

        policy = _create_policy(deployment.id, max_surge=1, max_unavailable=1)

        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            deployment.id: old_routes + new_routes
        }
        mock_deployment_repo.search_deployment_policies.return_value = _create_policy_search_result([
            policy
        ])

        entity_ids = [deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            result = await deployment_executor.execute_rolling_update_cycle([deployment])

        # Should be in-progress (not yet complete)
        assert len(result.skipped) == 1
        mock_deployment_repo.scale_routes.assert_awaited_once()

    async def test_ru003_completion_detected(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """RU-003: Completion detection when all routes are new-revision and healthy.

        Given: 0 old routes, 3 new routes (healthy), target=3
        When: Execute rolling update cycle
        Then: Deployment marked as complete (success)
        """
        deployment = _create_deploying_deployment(replica_count=3)
        new_routes = [
            _create_route_info(deployment.id, deployment.deploying_revision_id, RouteStatus.HEALTHY)
            for _ in range(3)
        ]

        policy = _create_policy(deployment.id, max_surge=1, max_unavailable=0)

        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            deployment.id: new_routes
        }
        mock_deployment_repo.search_deployment_policies.return_value = _create_policy_search_result([
            policy
        ])

        entity_ids = [deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            result = await deployment_executor.execute_rolling_update_cycle([deployment])

        # Should be complete
        assert len(result.successes) == 1
        assert len(result.skipped) == 0
        mock_deployment_repo.complete_rolling_update_bulk.assert_awaited_once()

    async def test_ru004_one_at_a_time_with_surge(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """RU-004: max_surge=1, max_unavailable=0.

        Given: 3 old routes (healthy), 0 new routes, target=3, max_surge=1, max_unavailable=0
        When: Execute rolling update cycle
        Then: Creates 1 new route, no old routes terminated yet
        """
        deployment = _create_deploying_deployment(replica_count=3)
        old_routes = [
            _create_route_info(deployment.id, deployment.current_revision_id, RouteStatus.HEALTHY)
            for _ in range(3)
        ]

        policy = _create_policy(deployment.id, max_surge=1, max_unavailable=0)

        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            deployment.id: old_routes
        }
        mock_deployment_repo.search_deployment_policies.return_value = _create_policy_search_result([
            policy
        ])

        entity_ids = [deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            result = await deployment_executor.execute_rolling_update_cycle([deployment])

        assert len(result.skipped) == 1
        mock_deployment_repo.scale_routes.assert_awaited_once()
        call_args = mock_deployment_repo.scale_routes.call_args
        creators = call_args[0][0]
        assert len(creators) == 1

    async def test_ru005_one_at_a_time_replace(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """RU-005: max_surge=0, max_unavailable=1.

        Given: 3 old routes (healthy), 0 new routes, target=3, max_surge=0, max_unavailable=1
        When: Execute rolling update cycle
        Then: No new routes created (max_surge=0 limits to 0 pending new routes which is already met),
              but we can still create up to target_count - total_new = 3
              Actually max_surge=0 means min(0-0, 3-0) = 0 new routes.
        """
        deployment = _create_deploying_deployment(replica_count=3)
        old_routes = [
            _create_route_info(deployment.id, deployment.current_revision_id, RouteStatus.HEALTHY)
            for _ in range(3)
        ]

        policy = _create_policy(deployment.id, max_surge=0, max_unavailable=1)

        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            deployment.id: old_routes
        }
        mock_deployment_repo.search_deployment_policies.return_value = _create_policy_search_result([
            policy
        ])

        entity_ids = [deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            result = await deployment_executor.execute_rolling_update_cycle([deployment])

        # With max_surge=0, no new routes can be created
        assert len(result.skipped) == 1

    async def test_ru006_rollback_on_all_new_routes_failed(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """RU-006: Rollback when new routes all fail and rollback_on_failure=True.

        Given: 3 old routes (healthy), 2 new routes (FAILED_TO_START), rollback_on_failure=True
        When: Execute rolling update cycle
        Then: New routes terminated, deployment goes to success (transitions to READY)
        """
        deployment = _create_deploying_deployment(replica_count=3)
        old_routes = [
            _create_route_info(deployment.id, deployment.current_revision_id, RouteStatus.HEALTHY)
            for _ in range(3)
        ]
        new_failed_routes = [
            _create_route_info(
                deployment.id, deployment.deploying_revision_id, RouteStatus.FAILED_TO_START
            )
            for _ in range(2)
        ]

        policy = _create_policy(
            deployment.id, max_surge=2, max_unavailable=1, rollback_on_failure=True
        )

        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            deployment.id: old_routes + new_failed_routes
        }
        mock_deployment_repo.search_deployment_policies.return_value = _create_policy_search_result([
            policy
        ])

        entity_ids = [deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            result = await deployment_executor.execute_rolling_update_cycle([deployment])

        # Should be in successes (rollback completes the rolling update)
        assert len(result.successes) == 1
        assert len(result.skipped) == 0
        mock_deployment_repo.scale_routes.assert_awaited_once()
        mock_deployment_repo.complete_rolling_update_bulk.assert_awaited_once()

    async def test_ru007_no_rollback_stays_deploying(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """RU-007: No rollback stays in DEPLOYING when rollback_on_failure=False.

        Given: 3 old routes (healthy), 2 new routes (FAILED_TO_START), rollback_on_failure=False
        When: Execute rolling update cycle
        Then: Deployment stays in skipped (DEPLOYING)
        """
        deployment = _create_deploying_deployment(replica_count=3)
        old_routes = [
            _create_route_info(deployment.id, deployment.current_revision_id, RouteStatus.HEALTHY)
            for _ in range(3)
        ]
        new_failed_routes = [
            _create_route_info(
                deployment.id, deployment.deploying_revision_id, RouteStatus.FAILED_TO_START
            )
            for _ in range(2)
        ]

        policy = _create_policy(
            deployment.id, max_surge=2, max_unavailable=1, rollback_on_failure=False
        )

        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            deployment.id: old_routes + new_failed_routes
        }
        mock_deployment_repo.search_deployment_policies.return_value = _create_policy_search_result([
            policy
        ])

        entity_ids = [deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            result = await deployment_executor.execute_rolling_update_cycle([deployment])

        # Should be in skipped (stays DEPLOYING, may create more new routes)
        assert len(result.skipped) == 1
        assert len(result.successes) == 0

    async def test_ru008_no_deploying_revision_completes(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """RU-008: No-op when deploying_revision is None (edge case).

        Given: Deployment in DEPLOYING but deploying_revision_id is None
        When: Execute rolling update cycle
        Then: Treated as complete (success)
        """
        dep_id = uuid4()
        deployment = DeploymentInfo(
            id=dep_id,
            metadata=DeploymentMetadata(
                name="test",
                domain="default",
                project=uuid4(),
                resource_group="default",
                created_user=uuid4(),
                session_owner=uuid4(),
                created_at=datetime.now(tzutc()),
                revision_history_limit=10,
            ),
            state=DeploymentState(lifecycle=EndpointLifecycle.DEPLOYING, retry_count=0),
            replica_spec=ReplicaSpec(replica_count=3),
            network=DeploymentNetworkSpec(open_to_public=False),
            model_revisions=[MagicMock()],
            current_revision_id=uuid4(),
            deploying_revision_id=None,
        )

        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {dep_id: []}
        mock_deployment_repo.search_deployment_policies.return_value = (
            _create_policy_search_result([])
        )

        entity_ids = [dep_id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            result = await deployment_executor.execute_rolling_update_cycle([deployment])

        # Should be treated as complete
        assert len(result.successes) == 1
        assert len(result.skipped) == 0

    async def test_ru009_multi_cycle_progress(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """RU-009: Multi-cycle simulation - successive calls show progress.

        Cycle 1: 3 old, 0 new → creates 1 new (max_surge=1)
        Cycle 2: 3 old, 1 new (healthy) → creates 1 new, terminates 1 old
        """
        deployment = _create_deploying_deployment(replica_count=3)
        policy = _create_policy(deployment.id, max_surge=1, max_unavailable=1)

        # Cycle 1: all old routes
        old_routes = [
            _create_route_info(deployment.id, deployment.current_revision_id, RouteStatus.HEALTHY)
            for _ in range(3)
        ]
        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            deployment.id: old_routes
        }
        mock_deployment_repo.search_deployment_policies.return_value = _create_policy_search_result([
            policy
        ])

        entity_ids = [deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            result1 = await deployment_executor.execute_rolling_update_cycle([deployment])

        assert len(result1.skipped) == 1
        call_args1 = mock_deployment_repo.scale_routes.call_args
        creators1 = call_args1[0][0]
        assert len(creators1) == 1  # max_surge=1

        # Cycle 2: 3 old + 1 new healthy
        mock_deployment_repo.scale_routes.reset_mock()
        new_route = _create_route_info(
            deployment.id, deployment.deploying_revision_id, RouteStatus.HEALTHY
        )
        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            deployment.id: old_routes + [new_route]
        }

        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            result2 = await deployment_executor.execute_rolling_update_cycle([deployment])

        assert len(result2.skipped) == 1
        mock_deployment_repo.scale_routes.assert_awaited_once()

    async def test_ru010_mixed_health_statuses(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """RU-010: Concurrent old/new routes with mixed health statuses.

        Given: 2 old (1 healthy, 1 unhealthy), 2 new (1 healthy, 1 provisioning)
        When: Execute rolling update cycle
        Then: Proper handling of mixed statuses
        """
        deployment = _create_deploying_deployment(replica_count=3)
        old_healthy = _create_route_info(
            deployment.id, deployment.current_revision_id, RouteStatus.HEALTHY
        )
        old_unhealthy = _create_route_info(
            deployment.id, deployment.current_revision_id, RouteStatus.UNHEALTHY
        )
        new_healthy = _create_route_info(
            deployment.id, deployment.deploying_revision_id, RouteStatus.HEALTHY
        )
        new_provisioning = _create_route_info(
            deployment.id, deployment.deploying_revision_id, RouteStatus.PROVISIONING
        )

        policy = _create_policy(deployment.id, max_surge=2, max_unavailable=1)

        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            deployment.id: [old_healthy, old_unhealthy, new_healthy, new_provisioning]
        }
        mock_deployment_repo.search_deployment_policies.return_value = _create_policy_search_result([
            policy
        ])

        entity_ids = [deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            result = await deployment_executor.execute_rolling_update_cycle([deployment])

        # Should be in-progress
        assert len(result.skipped) == 1
        assert len(result.successes) == 0

    async def test_ru011_zero_surge_zero_unavailable_raises_error(
        self,
        deployment_executor: DeploymentExecutor,
        mock_deployment_repo: AsyncMock,
    ) -> None:
        """RU-011: max_surge=0, max_unavailable=0 raises InvalidRollingUpdateParameters.

        Given: 3 old routes (healthy), 0 new routes, max_surge=0, max_unavailable=0
        When: Execute rolling update cycle
        Then: Deployment goes to errors with InvalidRollingUpdateParameters
        """
        deployment = _create_deploying_deployment(replica_count=3)
        old_routes = [
            _create_route_info(deployment.id, deployment.current_revision_id, RouteStatus.HEALTHY)
            for _ in range(3)
        ]

        policy = _create_policy(deployment.id, max_surge=0, max_unavailable=0)

        mock_deployment_repo.fetch_active_routes_by_endpoint_ids.return_value = {
            deployment.id: old_routes
        }
        mock_deployment_repo.search_deployment_policies.return_value = _create_policy_search_result([
            policy
        ])

        entity_ids = [deployment.id]
        with DeploymentRecorderContext.scope("test", entity_ids=entity_ids):
            result = await deployment_executor.execute_rolling_update_cycle([deployment])

        # Should be in errors (invalid parameters)
        assert len(result.errors) == 1
        assert len(result.skipped) == 0
        assert len(result.successes) == 0
