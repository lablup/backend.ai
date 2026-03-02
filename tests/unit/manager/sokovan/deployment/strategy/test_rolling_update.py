"""Comprehensive tests for the rolling update FSM evaluation (BEP-1049).

Tests cover:
- Various max_surge / max_unavailable combinations
- Single and multi-replica scenarios
- FSM state transitions: PROVISIONING, PROGRESSING, ROLLED_BACK, completed
- Edge cases: no routes, all failed, mixed statuses
- Termination priority ordering
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.types import SessionId
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentState,
    DeploymentSubStep,
    ReplicaSpec,
    RouteInfo,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.models.deployment_policy import RollingUpdateSpec
from ai.backend.manager.repositories.deployment.creators import RouteCreatorSpec
from ai.backend.manager.sokovan.deployment.strategy.rolling_update import (
    rolling_update_evaluate,
)
from ai.backend.manager.sokovan.deployment.strategy.types import CycleEvaluationResult

ENDPOINT_ID = UUID("aaaaaaaa-0000-0000-0000-aaaaaaaaaaaa")
OLD_REV = UUID("11111111-1111-1111-1111-111111111111")
NEW_REV = UUID("22222222-2222-2222-2222-222222222222")
PROJECT_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
USER_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


def make_deployment(
    *,
    desired: int = 1,
    deploying_revision_id: UUID = NEW_REV,
    current_revision_id: UUID = OLD_REV,
    endpoint_id: UUID = ENDPOINT_ID,
) -> DeploymentInfo:
    return DeploymentInfo(
        id=endpoint_id,
        metadata=DeploymentMetadata(
            name="test-deploy",
            domain="default",
            project=PROJECT_ID,
            resource_group="default",
            created_user=USER_ID,
            session_owner=USER_ID,
            created_at=datetime.now(UTC),
            revision_history_limit=5,
        ),
        state=DeploymentState(
            lifecycle=EndpointLifecycle.DEPLOYING,
            retry_count=0,
        ),
        replica_spec=ReplicaSpec(
            replica_count=desired,
        ),
        network=DeploymentNetworkSpec(open_to_public=False),
        model_revisions=[],
        current_revision_id=current_revision_id,
        deploying_revision_id=deploying_revision_id,
    )


def make_route(
    *,
    revision_id: UUID,
    status: RouteStatus = RouteStatus.HEALTHY,
    endpoint_id: UUID = ENDPOINT_ID,
    route_id: UUID | None = None,
) -> RouteInfo:
    return RouteInfo(
        route_id=route_id or uuid4(),
        endpoint_id=endpoint_id,
        session_id=SessionId(uuid4()),
        status=status,
        traffic_ratio=1.0 if status.is_active() else 0.0,
        created_at=datetime.now(UTC),
        revision_id=revision_id,
        traffic_status=RouteTrafficStatus.ACTIVE
        if status.is_active()
        else RouteTrafficStatus.INACTIVE,
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _count_scale_out(result: CycleEvaluationResult) -> int:
    return len(result.route_changes.scale_out_specs)


def _scale_in_ids(result: CycleEvaluationResult) -> list[UUID]:
    return result.route_changes.scale_in_route_ids


# ===========================================================================
# 1. Basic FSM states
# ===========================================================================


class TestBasicFSMStates:
    """Test fundamental FSM transitions."""

    def test_no_routes_initial_cycle_creates_new(self) -> None:
        """First cycle with 0 routes → PROGRESSING, creates desired count."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)

        result = rolling_update_evaluate(deployment, [], spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed
        assert _count_scale_out(result) == 1
        assert len(_scale_in_ids(result)) == 0

    def test_new_provisioning_waits(self) -> None:
        """New routes in PROVISIONING → wait (PROVISIONING sub-step)."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.PROVISIONING),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed
        assert _count_scale_out(result) == 0
        assert len(_scale_in_ids(result)) == 0

    def test_completed_when_all_new_healthy_and_no_old(self) -> None:
        """All old gone + new_healthy >= desired → completed."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert result.completed
        assert result.sub_step == DeploymentSubStep.PROGRESSING

    def test_rollback_when_all_new_failed(self) -> None:
        """All new routes failed → ROLLED_BACK."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.FAILED_TO_START),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK
        assert not result.completed

    def test_rollback_with_terminated_new_routes(self) -> None:
        """New routes in TERMINATED also count as failed."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.TERMINATED),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK


# ===========================================================================
# 2. max_surge variations
# ===========================================================================


class TestMaxSurge:
    """Test max_surge parameter controls."""

    def test_surge_1_desired_1_creates_1(self) -> None:
        """surge=1, desired=1: 1 old → create 1 new (total=2 allowed)."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY)]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert _count_scale_out(result) == 1

    def test_surge_2_desired_3_creates_2(self) -> None:
        """surge=2, desired=3: 3 old → max_total=5, can create 2."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=2, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert _count_scale_out(result) == 2

    def test_surge_0_desired_3_no_create_without_unavailable(self) -> None:
        """surge=0, unavailable=0: cannot create new (no budget)."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=0, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # max_total = 3+0 = 3, current_total = 3, can_create = 0
        assert _count_scale_out(result) == 0
        # min_available = 3-0 = 3, available=3, can_terminate = 0
        assert len(_scale_in_ids(result)) == 0

    def test_surge_3_desired_2_caps_at_desired(self) -> None:
        """surge=3, desired=2: creates at most desired - already_new."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(max_surge=3, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # max_total = 5, current_total = 2, can_create = 3
        # still_needed = 2 - 0 = 2 → min(3,2) = 2
        assert _count_scale_out(result) == 2

    def test_surge_already_at_max_no_create(self) -> None:
        """Already at max_total → no new creates."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # max_total = 3, current = 3 → can_create = 0
        assert _count_scale_out(result) == 0


# ===========================================================================
# 3. max_unavailable variations
# ===========================================================================


class TestMaxUnavailable:
    """Test max_unavailable parameter controls."""

    def test_unavailable_0_no_terminate_until_new_healthy(self) -> None:
        """unavailable=0: only terminate when new routes are healthy."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # min_available = 2-0 = 2, available = 0(new_healthy) + 2(old) = 2
        # can_terminate = 2 - 2 = 0
        assert len(_scale_in_ids(result)) == 0

    def test_unavailable_1_terminates_1_old(self) -> None:
        """unavailable=1: can terminate 1 old even without new ready."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=1)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # min_available = 3-1 = 2, available = 0+3 = 3, can_terminate = 1
        assert len(_scale_in_ids(result)) == 1

    def test_unavailable_2_terminates_2_old(self) -> None:
        """unavailable=2: can terminate up to 2 old routes."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=0, max_unavailable=2)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # min_available = 3-2 = 1, available = 0+3 = 3, can_terminate = 2
        assert len(_scale_in_ids(result)) == 2
        # max_total = 3+0 = 3, current = 3, can_create = 0
        # But still_needed = 3 → min(0, 3) = 0
        assert _count_scale_out(result) == 0

    def test_unavailable_with_new_healthy_allows_more_termination(self) -> None:
        """With new healthy routes, more old can be terminated."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # min_available = 3, available = 1(new_healthy)+3(old) = 4
        # can_terminate = 4 - 3 = 1
        assert len(_scale_in_ids(result)) == 1

    def test_unavailable_exceeds_desired_floors_to_zero(self) -> None:
        """unavailable > desired → min_available floors to 0."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(max_surge=0, max_unavailable=5)
        routes = [make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY)]

        result = rolling_update_evaluate(deployment, routes, spec)

        # min_available = max(0, 1-5) = 0, available = 0+1 = 1
        # can_terminate = 1 - 0 = 1
        assert len(_scale_in_ids(result)) == 1


# ===========================================================================
# 4. Combined surge + unavailable
# ===========================================================================


class TestCombinedSurgeAndUnavailable:
    """Test combinations of max_surge and max_unavailable."""

    def test_surge_1_unavailable_1_desired_3(self) -> None:
        """surge=1, unavailable=1, desired=3 with 3 old routes."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=1)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # max_total = 4, current = 3, can_create = 1, still_needed = 3 → create 1
        assert _count_scale_out(result) == 1
        # min_available = 2, available = 0+3 = 3, can_terminate = 1
        assert len(_scale_in_ids(result)) == 1

    def test_surge_2_unavailable_1_desired_4(self) -> None:
        """surge=2, unavailable=1, desired=4 with 4 old routes."""
        deployment = make_deployment(desired=4)
        spec = RollingUpdateSpec(max_surge=2, max_unavailable=1)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # max_total = 6, current = 4, can_create = 2, still_needed = 4 → 2
        assert _count_scale_out(result) == 2
        # min_available = 3, available = 0+4 = 4, can_terminate = 1
        assert len(_scale_in_ids(result)) == 1

    def test_aggressive_strategy_surge_3_unavail_2_desired_3(self) -> None:
        """Aggressive: surge=3, unavailable=2, desired=3 with 3 old."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=3, max_unavailable=2)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # max_total = 6, current = 3, can_create = 3, still_needed = 3 → 3
        assert _count_scale_out(result) == 3
        # min_available = 1, available = 0+3 = 3, can_terminate = 2
        assert len(_scale_in_ids(result)) == 2


# ===========================================================================
# 5. Multi-cycle progression
# ===========================================================================


class TestMultiCycleProgression:
    """Simulate multiple evaluation cycles."""

    def test_cycle_2_after_new_routes_become_healthy(self) -> None:
        """After new routes become healthy, old ones can be terminated."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # max_total = 4, current = 3, can_create = 1, still_needed = 2 → 1
        assert _count_scale_out(result) == 1
        # min_available = 3, available = 1+2 = 3, can_terminate = 0
        # Wait, that's wrong: available = 1(new_healthy) + 2(old) = 3
        # can_terminate = 3 - 3 = 0
        assert len(_scale_in_ids(result)) == 0

    def test_cycle_3_with_2_new_healthy(self) -> None:
        """2 new healthy, 2 old: can terminate 1 old and create 1 new."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # max_total = 4, current = 4, can_create = 0
        assert _count_scale_out(result) == 0
        # min_available = 3, available = 2+2 = 4, can_terminate = 1
        assert len(_scale_in_ids(result)) == 1

    def test_final_cycle_completes(self) -> None:
        """3 new healthy, 0 old → completed."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert result.completed

    def test_not_completed_when_old_still_exists(self) -> None:
        """Even with enough new, old still exists → not completed."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert not result.completed
        # Should terminate the old route
        assert len(_scale_in_ids(result)) == 1


# ===========================================================================
# 6. Mixed route statuses
# ===========================================================================


class TestMixedRouteStatuses:
    """Test with routes in various statuses."""

    def test_degraded_new_counts_as_healthy(self) -> None:
        """DEGRADED new routes count as active (is_active=True)."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.DEGRADED),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert result.completed

    def test_unhealthy_new_counts_as_healthy(self) -> None:
        """UNHEALTHY new routes count as active."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.UNHEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert result.completed

    def test_old_terminating_not_counted_as_active(self) -> None:
        """Old routes in TERMINATING are not counted as old_active."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.TERMINATING),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # old_active = 0 (terminating doesn't count), new_healthy = 1 >= desired
        assert result.completed

    def test_old_terminated_not_counted(self) -> None:
        """Old routes in TERMINATED are not counted as old_active."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.TERMINATED),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert result.completed

    def test_mixed_old_statuses_counts_only_active(self) -> None:
        """Only active old routes are counted in old_active."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.TERMINATING),
            make_route(revision_id=OLD_REV, status=RouteStatus.TERMINATED),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # old_active = 1 (only HEALTHY), total_new_live = 0
        # max_total = 3, current = 1, can_create = 2, still_needed = 2 → 2
        assert _count_scale_out(result) == 2

    def test_mix_of_failed_and_healthy_new_not_rollback(self) -> None:
        """Some new failed, some new healthy → no rollback (live routes exist)."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(max_surge=2, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.FAILED_TO_START),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # total_new_live = 1 (healthy) > 0, so NOT rolled back
        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed


# ===========================================================================
# 7. Termination priority ordering
# ===========================================================================


class TestTerminationPriority:
    """Test that old routes are terminated in priority order."""

    def test_unhealthy_terminated_before_healthy(self) -> None:
        """UNHEALTHY old routes should be terminated before HEALTHY ones."""
        unhealthy_id = UUID("00000000-0000-0000-0000-000000000001")
        healthy_id = UUID("00000000-0000-0000-0000-000000000002")

        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(max_surge=0, max_unavailable=1)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY, route_id=healthy_id),
            make_route(revision_id=OLD_REV, status=RouteStatus.UNHEALTHY, route_id=unhealthy_id),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert len(_scale_in_ids(result)) == 1
        assert _scale_in_ids(result)[0] == unhealthy_id

    def test_degraded_before_healthy(self) -> None:
        """DEGRADED old routes terminated before HEALTHY ones."""
        degraded_id = UUID("00000000-0000-0000-0000-000000000001")
        healthy_id = UUID("00000000-0000-0000-0000-000000000002")

        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(max_surge=0, max_unavailable=1)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY, route_id=healthy_id),
            make_route(revision_id=OLD_REV, status=RouteStatus.DEGRADED, route_id=degraded_id),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert len(_scale_in_ids(result)) == 1
        assert _scale_in_ids(result)[0] == degraded_id

    def test_priority_order_unhealthy_degraded_provisioning_healthy(self) -> None:
        """Full priority order: unhealthy < degraded < provisioning < healthy."""
        unhealthy_id = UUID("00000000-0000-0000-0000-000000000001")
        degraded_id = UUID("00000000-0000-0000-0000-000000000002")
        provisioning_id = UUID("00000000-0000-0000-0000-000000000003")
        healthy_id = UUID("00000000-0000-0000-0000-000000000004")

        deployment = make_deployment(desired=4)
        spec = RollingUpdateSpec(max_surge=0, max_unavailable=3)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY, route_id=healthy_id),
            make_route(
                revision_id=OLD_REV, status=RouteStatus.PROVISIONING, route_id=provisioning_id
            ),
            make_route(revision_id=OLD_REV, status=RouteStatus.DEGRADED, route_id=degraded_id),
            make_route(revision_id=OLD_REV, status=RouteStatus.UNHEALTHY, route_id=unhealthy_id),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        terminated = _scale_in_ids(result)
        assert len(terminated) == 3
        assert terminated[0] == unhealthy_id
        assert terminated[1] == degraded_id
        assert terminated[2] == provisioning_id


# ===========================================================================
# 8. Edge cases
# ===========================================================================


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_desired_0_no_routes_completed(self) -> None:
        """desired=0, no routes → completed (vacuously true)."""
        deployment = make_deployment(desired=0)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)

        result = rolling_update_evaluate(deployment, [], spec)

        assert result.completed

    def test_more_new_healthy_than_desired_still_completes(self) -> None:
        """new_healthy > desired and no old → completed."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(max_surge=2, max_unavailable=0)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert result.completed

    def test_no_routes_no_failed_creates_new(self) -> None:
        """Empty routes list → PROGRESSING with scale out."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=2, max_unavailable=1)

        result = rolling_update_evaluate(deployment, [], spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        # max_total = 5, current = 0, can_create = 5, still_needed = 3 → 3
        assert _count_scale_out(result) == 3

    def test_only_failed_new_no_old_rolls_back(self) -> None:
        """Only failed new routes, no old → ROLLED_BACK."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.FAILED_TO_START),
            make_route(revision_id=NEW_REV, status=RouteStatus.FAILED_TO_START),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK

    def test_all_old_inactive_no_new_creates_desired(self) -> None:
        """All old routes are inactive (terminated), no new → create desired."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.TERMINATED),
            make_route(revision_id=OLD_REV, status=RouteStatus.TERMINATED),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # old_active = 0, no new → max_total = 3, current = 0, can_create = 3
        # still_needed = 2, min(3, 2) = 2
        assert _count_scale_out(result) == 2

    def test_large_desired_surge_1_unavailable_0_creates_exactly_1(self) -> None:
        """Large desired with conservative settings creates exactly 1."""
        deployment = make_deployment(desired=10)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY) for _ in range(10)]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert _count_scale_out(result) == 1
        assert len(_scale_in_ids(result)) == 0

    def test_deploying_rev_none_all_routes_classified_as_old(self) -> None:
        """If deploying_revision_id is None, all routes are old (r.revision_id != None)."""
        deployment = make_deployment(desired=1, deploying_revision_id=None)  # type: ignore[arg-type]
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY)]

        result = rolling_update_evaluate(deployment, routes, spec)

        # All classified as old, no new → PROGRESSING with create
        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert _count_scale_out(result) == 1

    def test_route_without_revision_classified_as_old(self) -> None:
        """Routes with revision_id=None are classified as old."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [make_route(revision_id=None, status=RouteStatus.HEALTHY)]  # type: ignore[arg-type]

        result = rolling_update_evaluate(deployment, routes, spec)

        # revision_id=None != NEW_REV, so classified as old
        assert _count_scale_out(result) == 1

    def test_provisioning_prioritized_over_completion_check(self) -> None:
        """PROVISIONING check comes before completion check."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.PROVISIONING),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # Even though new_healthy >= desired, PROVISIONING takes precedence
        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed


# ===========================================================================
# 9. Route creator specs validation
# ===========================================================================


class TestRouteCreatorSpecs:
    """Validate that route creator specs have correct fields."""

    def test_creator_specs_use_deploying_revision(self) -> None:
        """Created routes should use the deploying revision."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)

        result = rolling_update_evaluate(deployment, [], spec)

        assert _count_scale_out(result) == 1
        creator_spec = result.route_changes.scale_out_specs[0].spec
        assert isinstance(creator_spec, RouteCreatorSpec)
        assert creator_spec.revision_id == NEW_REV
        assert creator_spec.endpoint_id == ENDPOINT_ID
        assert creator_spec.session_owner_id == USER_ID
        assert creator_spec.domain == "default"
        assert creator_spec.project_id == PROJECT_ID

    def test_multiple_creators_all_correct(self) -> None:
        """Multiple creators all have correct metadata."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=3, max_unavailable=0)

        result = rolling_update_evaluate(deployment, [], spec)

        assert _count_scale_out(result) == 3
        for creator in result.route_changes.scale_out_specs:
            creator_spec = creator.spec
            assert isinstance(creator_spec, RouteCreatorSpec)
            assert creator_spec.revision_id == NEW_REV
            assert creator_spec.endpoint_id == ENDPOINT_ID


# ===========================================================================
# 10. Realistic multi-step scenario (desired=5)
# ===========================================================================


class TestRealisticScenario:
    """Simulate a realistic rolling update with desired=5, surge=2, unavail=1."""

    def test_step_by_step_rolling_update(self) -> None:
        """Full simulation of a rolling update across multiple cycles."""
        deployment = make_deployment(desired=5)
        spec = RollingUpdateSpec(max_surge=2, max_unavailable=1)

        # Cycle 1: 5 old, 0 new
        old_routes = [make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY) for _ in range(5)]
        r1 = rolling_update_evaluate(deployment, old_routes, spec)

        # max_total = 7, current = 5, can_create = 2, still_needed = 5 → 2
        assert _count_scale_out(r1) == 2
        # min_available = 4, available = 0+5 = 5, can_terminate = 1
        assert len(_scale_in_ids(r1)) == 1

        # Cycle 2: 4 old, 2 new healthy
        routes_c2 = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]
        r2 = rolling_update_evaluate(deployment, routes_c2, spec)

        # max_total = 7, current = 6, can_create = 1, still_needed = 3 → 1
        assert _count_scale_out(r2) == 1
        # min_available = 4, available = 2+4 = 6, can_terminate = 2
        assert len(_scale_in_ids(r2)) == 2

        # Cycle 3: 2 old, 3 new healthy
        routes_c3 = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]
        r3 = rolling_update_evaluate(deployment, routes_c3, spec)

        # max_total = 7, current = 5, can_create = 2, still_needed = 2 → 2
        assert _count_scale_out(r3) == 2
        # min_available = 4, available = 3+2 = 5, can_terminate = 1
        assert len(_scale_in_ids(r3)) == 1

        # Cycle 4: 1 old, 5 new healthy
        routes_c4 = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]
        r4 = rolling_update_evaluate(deployment, routes_c4, spec)

        # can_create = 0 (still_needed = 0), can_terminate = 1
        assert _count_scale_out(r4) == 0
        assert len(_scale_in_ids(r4)) == 1
        assert not r4.completed

        # Cycle 5: 0 old, 5 new healthy → completed
        routes_c5 = [
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]
        r5 = rolling_update_evaluate(deployment, routes_c5, spec)

        assert r5.completed


# ===========================================================================
# 11. Deadlock and stall detection
# ===========================================================================


class TestDeadlockAndStall:
    """Test scenarios where the FSM could potentially stall."""

    def test_surge_0_unavailable_0_deadlock(self) -> None:
        """Both surge=0 and unavailable=0 → no progress possible (deadlock).

        This is a configuration error: at least one must be > 0 for progress.
        The FSM correctly returns PROGRESSING with no changes.
        """
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=0, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert _count_scale_out(result) == 0
        assert len(_scale_in_ids(result)) == 0
        # This is a known deadlock — no progress is possible.

    def test_surge_0_unavailable_1_terminates_first_then_creates(self) -> None:
        """surge=0, unavailable=1 → terminate 1, then next cycle creates 1.

        This pattern kills old routes before creating new ones (downtime-tolerant).
        """
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=0, max_unavailable=1)

        # Cycle 1: 3 old → terminate 1, create 0
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
        ]
        r1 = rolling_update_evaluate(deployment, routes, spec)
        assert _count_scale_out(r1) == 0
        assert len(_scale_in_ids(r1)) == 1

        # Cycle 2: 2 old → now we can create 1
        routes_c2 = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
        ]
        r2 = rolling_update_evaluate(deployment, routes_c2, spec)
        # max_total = 3, current = 2, can_create = 1, still_needed = 3 → 1
        assert _count_scale_out(r2) == 1
        # min_available = 2, available = 0+2 = 2, can_terminate = 0
        assert len(_scale_in_ids(r2)) == 0

    def test_partial_new_failure_continues_progress(self) -> None:
        """Some new routes fail while others succeed → continue, no rollback."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=2, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.FAILED_TO_START),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # total_new_live = 1 > 0, so NOT rolled back
        assert result.sub_step == DeploymentSubStep.PROGRESSING
        # still_needed = 3-1 = 2, max_total=5, current=4 → can_create = 1
        assert _count_scale_out(result) == 1

    def test_new_routes_exceed_desired_no_extra_create(self) -> None:
        """More new_live than desired → no extra creation (still_needed < 0)."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(max_surge=2, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # still_needed = 2-3 = -1 → to_create = max(0, ...) = 0
        assert _count_scale_out(result) == 0
        # min_available = 2, available = 3+1 = 4, can_terminate = 2 → min(2, 1) = 1
        assert len(_scale_in_ids(result)) == 1


# ===========================================================================
# 12. desired_replica_count vs replica_count
# ===========================================================================


class TestDesiredReplicaCount:
    """Test that the correct desired count is used."""

    def test_desired_replica_count_overrides_replica_count(self) -> None:
        """When desired_replica_count is set, it takes precedence."""
        deployment = make_deployment(desired=3)
        # Override desired_replica_count
        deployment.replica_spec = ReplicaSpec(
            replica_count=1,
            desired_replica_count=3,
        )
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY)]

        result = rolling_update_evaluate(deployment, routes, spec)

        # desired is 3 (from desired_replica_count), not 1
        # max_total = 4, current = 1, can_create = 3, still_needed = 3 → 3
        assert _count_scale_out(result) == 3

    def test_replica_count_used_when_no_desired(self) -> None:
        """When desired_replica_count is None, uses replica_count."""
        deployment = make_deployment(desired=2)
        deployment.replica_spec = ReplicaSpec(
            replica_count=2,
            desired_replica_count=None,
        )
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert result.completed


# ===========================================================================
# 13. Scale-down during rolling update
# ===========================================================================


class TestScaleDownDuringRollingUpdate:
    """Test behavior when desired is reduced during rolling update."""

    def test_desired_reduced_terminates_excess_old(self) -> None:
        """If desired is lowered, more old can be terminated."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # max_total = 2, current = 3 → can_create = max(0, -1) = 0
        assert _count_scale_out(result) == 0
        # Wait: still_needed = 1 - 0 = 1, but can_create is capped by max_total
        # max_total = 2, current = 3 → can_create = -1 → to_create = max(0, min(-1, 1)) = 0
        # min_available = 1, available = 0+3 = 3, can_terminate = 2
        assert len(_scale_in_ids(result)) == 2

    def test_desired_increased_creates_more(self) -> None:
        """If desired is raised, more new routes are created."""
        deployment = make_deployment(desired=5)
        spec = RollingUpdateSpec(max_surge=2, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # max_total = 7, current = 2, can_create = 5, still_needed = 5 → 5
        assert _count_scale_out(result) == 5


# ===========================================================================
# 14. Concurrent provisioning and termination
# ===========================================================================


class TestConcurrentOperations:
    """Test that provisioning blocks further changes correctly."""

    def test_provisioning_blocks_all_further_actions(self) -> None:
        """Any new route in PROVISIONING → wait, even if old can be terminated."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=2, max_unavailable=1)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
            make_route(revision_id=NEW_REV, status=RouteStatus.PROVISIONING),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # PROVISIONING takes priority over all other decisions
        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert _count_scale_out(result) == 0
        assert len(_scale_in_ids(result)) == 0

    def test_multiple_provisioning_routes_still_waits(self) -> None:
        """Multiple PROVISIONING routes → still PROVISIONING."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(max_surge=3, max_unavailable=3)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.PROVISIONING),
            make_route(revision_id=NEW_REV, status=RouteStatus.PROVISIONING),
            make_route(revision_id=NEW_REV, status=RouteStatus.PROVISIONING),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROVISIONING

    def test_old_provisioning_counted_as_active(self) -> None:
        """Old routes in PROVISIONING are counted as old_active."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(max_surge=1, max_unavailable=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.PROVISIONING),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY),
        ]

        result = rolling_update_evaluate(deployment, routes, spec)

        # old_active = 2 (both PROVISIONING and HEALTHY are active)
        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed
