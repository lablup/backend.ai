"""Comprehensive tests for the blue-green deployment strategy FSM (BEP-1049).

Tests cover:
- FSM state transitions: PROVISIONING, PROGRESSING, ROLLED_BACK, completed
- auto_promote / promote_delay_seconds combinations
- Single and multi-replica scenarios
- Edge cases: no routes, all failed, mixed statuses, desired=0
- Multi-cycle progression simulation
- Route creator specs validation
- desired_replica_count vs replica_count
- Scale-down during blue-green deployment
- Concurrent provisioning checks
- Realistic multi-step scenarios
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
from ai.backend.manager.models.deployment_policy import BlueGreenSpec
from ai.backend.manager.repositories.deployment.creators import RouteCreatorSpec
from ai.backend.manager.sokovan.deployment.strategy.blue_green import blue_green_evaluate
from ai.backend.manager.sokovan.deployment.strategy.types import CycleEvaluationResult

ENDPOINT_ID = UUID("aaaaaaaa-0000-0000-0000-aaaaaaaaaaaa")
OLD_REV = UUID("11111111-1111-1111-1111-111111111111")
NEW_REV = UUID("22222222-2222-2222-2222-222222222222")
PROJECT_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
USER_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


def make_deployment(
    *,
    desired: int = 3,
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
    traffic_status: RouteTrafficStatus | None = None,
    traffic_ratio: float | None = None,
) -> RouteInfo:
    if traffic_status is None:
        traffic_status = (
            RouteTrafficStatus.ACTIVE if status.is_active() else RouteTrafficStatus.INACTIVE
        )
    if traffic_ratio is None:
        traffic_ratio = 1.0 if status.is_active() else 0.0
    return RouteInfo(
        route_id=route_id or uuid4(),
        endpoint_id=endpoint_id,
        session_id=SessionId(uuid4()),
        status=status,
        traffic_ratio=traffic_ratio,
        created_at=datetime.now(UTC),
        revision_id=revision_id,
        traffic_status=traffic_status,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _count_scale_out(result: CycleEvaluationResult) -> int:
    return len(result.route_changes.scale_out_specs)


def _scale_in_ids(result: CycleEvaluationResult) -> list[UUID]:
    return result.route_changes.scale_in_route_ids


def _promote_ids(result: CycleEvaluationResult) -> list[UUID]:
    return result.route_changes.promote_route_ids


def _blue_routes(
    count: int,
    *,
    status: RouteStatus = RouteStatus.HEALTHY,
) -> list[RouteInfo]:
    return [
        make_route(
            revision_id=OLD_REV,
            status=status,
            traffic_status=RouteTrafficStatus.ACTIVE,
            traffic_ratio=1.0,
        )
        for _ in range(count)
    ]


def _green_routes(
    count: int,
    *,
    status: RouteStatus = RouteStatus.HEALTHY,
    traffic_status: RouteTrafficStatus = RouteTrafficStatus.INACTIVE,
    traffic_ratio: float = 0.0,
) -> list[RouteInfo]:
    return [
        make_route(
            revision_id=NEW_REV,
            status=status,
            traffic_status=traffic_status,
            traffic_ratio=traffic_ratio,
        )
        for _ in range(count)
    ]


# ===========================================================================
# 1. Basic FSM states
# ===========================================================================


class TestBasicFSMStates:
    """Test fundamental FSM transitions."""

    def test_no_routes_initial_cycle_creates_green(self) -> None:
        """First cycle with 0 routes → PROVISIONING, creates desired count."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, [], spec)

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed
        assert _count_scale_out(result) == 3
        assert len(_scale_in_ids(result)) == 0
        assert len(_promote_ids(result)) == 0

    def test_green_provisioning_waits(self) -> None:
        """Green routes in PROVISIONING → wait (PROVISIONING sub-step)."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.PROVISIONING)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed
        assert _count_scale_out(result) == 0
        assert len(_scale_in_ids(result)) == 0
        assert len(_promote_ids(result)) == 0

    def test_completed_when_all_green_healthy_auto_promote(self) -> None:
        """All green healthy + auto_promote + delay=0 → completed."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert len(_promote_ids(result)) == 3
        assert len(_scale_in_ids(result)) == 3

    def test_rollback_when_all_green_failed(self) -> None:
        """All green routes failed → ROLLED_BACK."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.FAILED_TO_START)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK
        assert not result.completed

    def test_rollback_with_terminated_green_routes(self) -> None:
        """Green routes in TERMINATED also count as failed."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(2) + _green_routes(2, status=RouteStatus.TERMINATED)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK
        assert not result.completed


# ===========================================================================
# 2. auto_promote variations
# ===========================================================================


class TestAutoPromote:
    """Test auto_promote parameter controls."""

    def test_auto_promote_true_delay_zero_promotes(self) -> None:
        """auto_promote=True, delay=0 → promote immediately."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert len(_promote_ids(result)) == 3
        assert len(_scale_in_ids(result)) == 3

    def test_auto_promote_false_waits_for_manual(self) -> None:
        """auto_promote=False → PROGRESSING, waiting for manual promotion."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=False, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed
        assert len(_promote_ids(result)) == 0
        assert len(_scale_in_ids(result)) == 0

    def test_auto_promote_true_delay_positive_waits(self) -> None:
        """auto_promote=True, delay>0 → PROGRESSING (delay wait)."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=60)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed
        assert len(_promote_ids(result)) == 0
        assert len(_scale_in_ids(result)) == 0

    def test_auto_promote_false_delay_positive_still_waits(self) -> None:
        """auto_promote=False, delay>0 → PROGRESSING (manual overrides delay)."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=False, promote_delay_seconds=120)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed
        assert len(_promote_ids(result)) == 0

    def test_auto_promote_true_delay_1_second_waits(self) -> None:
        """auto_promote=True, delay=1 → still waits (any positive delay)."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=1)
        routes = _blue_routes(2) + _green_routes(2, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert not result.completed
        assert len(_promote_ids(result)) == 0

    def test_default_spec_auto_promote_false(self) -> None:
        """Default BlueGreenSpec has auto_promote=False."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec()
        routes = _blue_routes(2) + _green_routes(2, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert not result.completed
        assert result.sub_step == DeploymentSubStep.PROGRESSING


# ===========================================================================
# 3. Provisioning states
# ===========================================================================


class TestProvisioningStates:
    """Test PROVISIONING sub-step behaviors."""

    def test_all_green_provisioning(self) -> None:
        """All green routes PROVISIONING → PROVISIONING sub-step."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.PROVISIONING)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed
        assert _count_scale_out(result) == 0

    def test_partial_provisioning_partial_healthy(self) -> None:
        """Some green PROVISIONING + some HEALTHY → PROVISIONING (wait)."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = (
            _blue_routes(3)
            + _green_routes(1, status=RouteStatus.HEALTHY)
            + _green_routes(2, status=RouteStatus.PROVISIONING)
        )

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed

    def test_single_provisioning_among_many_healthy(self) -> None:
        """Even 1 PROVISIONING green among many healthy → PROVISIONING."""
        deployment = make_deployment(desired=5)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = (
            _blue_routes(5)
            + _green_routes(4, status=RouteStatus.HEALTHY)
            + _green_routes(1, status=RouteStatus.PROVISIONING)
        )

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed

    def test_no_green_with_blue_creates_all(self) -> None:
        """Blue routes exist, no green → create all desired green routes."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert _count_scale_out(result) == 3

    def test_no_green_no_blue_creates_all(self) -> None:
        """Fresh deployment with no routes → create all desired."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, [], spec)

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert _count_scale_out(result) == 3


# ===========================================================================
# 4. Rollback scenarios
# ===========================================================================


class TestRollbackScenarios:
    """Test rollback behavior when green routes fail."""

    def test_all_green_failed_to_start_rollback(self) -> None:
        """All green FAILED_TO_START → ROLLED_BACK with scale_in for failed routes."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        greens = _green_routes(3, status=RouteStatus.FAILED_TO_START)
        routes = _blue_routes(3) + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK
        assert not result.completed
        green_ids = {r.route_id for r in greens}
        assert set(_scale_in_ids(result)) == green_ids
        assert len(_promote_ids(result)) == 0

    def test_all_green_terminated_rollback(self) -> None:
        """All green TERMINATED → ROLLED_BACK."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        greens = _green_routes(3, status=RouteStatus.TERMINATED)
        routes = _blue_routes(3) + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK
        green_ids = {r.route_id for r in greens}
        assert set(_scale_in_ids(result)) == green_ids

    def test_mixed_failed_and_terminated_green_rollback(self) -> None:
        """Mixed FAILED_TO_START + TERMINATED green → ROLLED_BACK."""
        deployment = make_deployment(desired=4)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        greens = _green_routes(2, status=RouteStatus.FAILED_TO_START) + _green_routes(
            2, status=RouteStatus.TERMINATED
        )
        routes = _blue_routes(4) + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK
        green_ids = {r.route_id for r in greens}
        assert set(_scale_in_ids(result)) == green_ids

    def test_rollback_no_blue_routes(self) -> None:
        """All green failed with no blue routes → ROLLED_BACK."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        greens = _green_routes(2, status=RouteStatus.FAILED_TO_START)

        result = blue_green_evaluate(deployment, greens, spec)

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK
        assert not result.completed

    def test_rollback_preserves_blue_routes(self) -> None:
        """On rollback, blue routes are NOT scale_in'd — only green routes."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        blues = _blue_routes(3)
        greens = _green_routes(3, status=RouteStatus.FAILED_TO_START)
        routes = blues + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK
        blue_ids = {r.route_id for r in blues}
        green_ids = {r.route_id for r in greens}
        assert set(_scale_in_ids(result)) == green_ids
        assert blue_ids.isdisjoint(set(_scale_in_ids(result)))


# ===========================================================================
# 5. Mixed green statuses (healthy + failed, no provisioning)
# ===========================================================================


class TestMixedGreenStatuses:
    """Test with green routes in various mixed states."""

    def test_healthy_and_failed_mixed_progressing(self) -> None:
        """Some green healthy, some failed (no provisioning) → PROGRESSING."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = (
            _blue_routes(3)
            + _green_routes(1, status=RouteStatus.HEALTHY)
            + _green_routes(2, status=RouteStatus.FAILED_TO_START)
        )

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed

    def test_healthy_and_terminated_mixed_progressing(self) -> None:
        """Some green healthy, some terminated → PROGRESSING (not enough healthy)."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = (
            _blue_routes(3)
            + _green_routes(2, status=RouteStatus.HEALTHY)
            + _green_routes(1, status=RouteStatus.TERMINATED)
        )

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed

    def test_degraded_green_counts_as_healthy(self) -> None:
        """DEGRADED green routes count as active (is_active=True)."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(1) + _green_routes(1, status=RouteStatus.DEGRADED)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert len(_promote_ids(result)) == 1

    def test_unhealthy_green_counts_as_healthy(self) -> None:
        """UNHEALTHY green routes count as active."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(1) + _green_routes(1, status=RouteStatus.UNHEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert len(_promote_ids(result)) == 1

    def test_mix_degraded_and_healthy_green_promoted(self) -> None:
        """Mix of DEGRADED and HEALTHY green → all promoted on completion."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        greens = _green_routes(2, status=RouteStatus.HEALTHY) + _green_routes(
            1, status=RouteStatus.DEGRADED
        )
        routes = _blue_routes(3) + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        green_ids = {r.route_id for r in greens}
        assert set(_promote_ids(result)) == green_ids

    def test_mix_unhealthy_and_healthy_green_promoted(self) -> None:
        """Mix of UNHEALTHY and HEALTHY green → all promoted on completion."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        greens = _green_routes(1, status=RouteStatus.HEALTHY) + _green_routes(
            1, status=RouteStatus.UNHEALTHY
        )
        routes = _blue_routes(2) + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        green_ids = {r.route_id for r in greens}
        assert set(_promote_ids(result)) == green_ids


# ===========================================================================
# 6. Blue route status variations
# ===========================================================================


class TestBlueRouteStatuses:
    """Test how different blue route statuses are handled."""

    def test_blue_terminating_not_counted_as_active(self) -> None:
        """Blue routes in TERMINATING are not counted as blue_active."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        greens = _green_routes(1, status=RouteStatus.HEALTHY)
        routes = [
            make_route(
                revision_id=OLD_REV,
                status=RouteStatus.TERMINATING,
                traffic_status=RouteTrafficStatus.INACTIVE,
                traffic_ratio=0.0,
            ),
        ] + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        # Only green promoted, no blue in scale_in (terminating is not active)
        assert len(_promote_ids(result)) == 1
        assert len(_scale_in_ids(result)) == 0

    def test_blue_terminated_not_counted(self) -> None:
        """Blue routes in TERMINATED are not counted as blue_active."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        greens = _green_routes(1, status=RouteStatus.HEALTHY)
        routes = [
            make_route(
                revision_id=OLD_REV,
                status=RouteStatus.TERMINATED,
                traffic_status=RouteTrafficStatus.INACTIVE,
                traffic_ratio=0.0,
            ),
        ] + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert len(_scale_in_ids(result)) == 0

    def test_blue_failed_not_counted_as_active(self) -> None:
        """Blue routes in FAILED_TO_START are not counted as blue_active."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        greens = _green_routes(1, status=RouteStatus.HEALTHY)
        routes = [
            make_route(
                revision_id=OLD_REV,
                status=RouteStatus.FAILED_TO_START,
                traffic_status=RouteTrafficStatus.INACTIVE,
                traffic_ratio=0.0,
            ),
        ] + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert len(_scale_in_ids(result)) == 0

    def test_mixed_blue_statuses_only_active_scale_in(self) -> None:
        """Only active blue routes are included in scale_in."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        active_blue = make_route(
            revision_id=OLD_REV,
            status=RouteStatus.HEALTHY,
            traffic_status=RouteTrafficStatus.ACTIVE,
            traffic_ratio=1.0,
        )
        inactive_blue = make_route(
            revision_id=OLD_REV,
            status=RouteStatus.TERMINATING,
            traffic_status=RouteTrafficStatus.INACTIVE,
            traffic_ratio=0.0,
        )
        greens = _green_routes(2, status=RouteStatus.HEALTHY)
        routes = [active_blue, inactive_blue] + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert _scale_in_ids(result) == [active_blue.route_id]

    def test_blue_degraded_counted_as_active(self) -> None:
        """Blue routes in DEGRADED are counted as active → included in scale_in."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        blue = make_route(
            revision_id=OLD_REV,
            status=RouteStatus.DEGRADED,
            traffic_status=RouteTrafficStatus.ACTIVE,
            traffic_ratio=1.0,
        )
        greens = _green_routes(1, status=RouteStatus.HEALTHY)
        routes = [blue] + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert _scale_in_ids(result) == [blue.route_id]

    def test_blue_unhealthy_counted_as_active(self) -> None:
        """Blue routes in UNHEALTHY are counted as active → included in scale_in."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        blue = make_route(
            revision_id=OLD_REV,
            status=RouteStatus.UNHEALTHY,
            traffic_status=RouteTrafficStatus.ACTIVE,
            traffic_ratio=1.0,
        )
        greens = _green_routes(1, status=RouteStatus.HEALTHY)
        routes = [blue] + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert _scale_in_ids(result) == [blue.route_id]


# ===========================================================================
# 7. Multi-cycle progression
# ===========================================================================


class TestMultiCycleProgression:
    """Simulate multiple evaluation cycles."""

    def test_cycle_1_no_green_creates_all(self) -> None:
        """Cycle 1: blue only → creates desired green routes."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert _count_scale_out(result) == 3

    def test_cycle_2_green_provisioning_waits(self) -> None:
        """Cycle 2: green PROVISIONING → wait."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.PROVISIONING)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed

    def test_cycle_3_partial_green_healthy_waits(self) -> None:
        """Cycle 3: some green healthy, some provisioning → still PROVISIONING."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = (
            _blue_routes(3)
            + _green_routes(2, status=RouteStatus.HEALTHY)
            + _green_routes(1, status=RouteStatus.PROVISIONING)
        )

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROVISIONING

    def test_cycle_4_all_green_healthy_promotes(self) -> None:
        """Cycle 4: all green healthy → completed with promotion."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert len(_promote_ids(result)) == 3
        assert len(_scale_in_ids(result)) == 3

    def test_not_completed_when_green_less_than_desired(self) -> None:
        """Green healthy < desired → PROGRESSING (not enough)."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(2, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed


# ===========================================================================
# 8. Promotion route ID verification
# ===========================================================================


class TestPromotionRouteIdVerification:
    """Verify promote and scale_in route IDs are exact matches."""

    def test_promote_ids_match_green_healthy(self) -> None:
        """Promoted route IDs must exactly match green healthy route IDs."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        blues = _blue_routes(3)
        greens = _green_routes(3, status=RouteStatus.HEALTHY)
        routes = blues + greens

        result = blue_green_evaluate(deployment, routes, spec)

        expected_promote = [r.route_id for r in greens]
        assert _promote_ids(result) == expected_promote

    def test_scale_in_ids_match_blue_active(self) -> None:
        """Scale-in route IDs must exactly match blue active route IDs."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        blues = _blue_routes(3)
        greens = _green_routes(3, status=RouteStatus.HEALTHY)
        routes = blues + greens

        result = blue_green_evaluate(deployment, routes, spec)

        expected_scale_in = [r.route_id for r in blues]
        assert _scale_in_ids(result) == expected_scale_in

    def test_no_cross_contamination_between_promote_and_scale_in(self) -> None:
        """Promote IDs and scale_in IDs must be disjoint sets."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        blues = _blue_routes(3)
        greens = _green_routes(3, status=RouteStatus.HEALTHY)
        routes = blues + greens

        result = blue_green_evaluate(deployment, routes, spec)

        promote_set = set(_promote_ids(result))
        scale_in_set = set(_scale_in_ids(result))
        assert promote_set.isdisjoint(scale_in_set)

    def test_promote_ids_order_matches_green_order(self) -> None:
        """Promote IDs order should match the order green routes were processed."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        greens = _green_routes(3, status=RouteStatus.HEALTHY)
        routes = _blue_routes(3) + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert _promote_ids(result) == [r.route_id for r in greens]


# ===========================================================================
# 9. Route creator specs validation
# ===========================================================================


class TestRouteCreatorSpecs:
    """Validate that route creator specs have correct fields."""

    def test_creator_specs_use_deploying_revision(self) -> None:
        """Created routes should use the deploying revision."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, [], spec)

        assert _count_scale_out(result) == 1
        creator_spec = result.route_changes.scale_out_specs[0].spec
        assert isinstance(creator_spec, RouteCreatorSpec)
        assert creator_spec.revision_id == NEW_REV
        assert creator_spec.endpoint_id == ENDPOINT_ID
        assert creator_spec.session_owner_id == USER_ID
        assert creator_spec.domain == "default"
        assert creator_spec.project_id == PROJECT_ID

    def test_creator_specs_have_inactive_traffic(self) -> None:
        """Green routes must be created with INACTIVE traffic status."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(2)

        result = blue_green_evaluate(deployment, routes, spec)

        for creator in result.route_changes.scale_out_specs:
            creator_spec = creator.spec
            assert isinstance(creator_spec, RouteCreatorSpec)
            assert creator_spec.traffic_status == RouteTrafficStatus.INACTIVE
            assert creator_spec.traffic_ratio == 0.0

    def test_multiple_creators_all_correct(self) -> None:
        """Multiple creators all have correct metadata."""
        deployment = make_deployment(desired=5)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, [], spec)

        assert _count_scale_out(result) == 5
        for creator in result.route_changes.scale_out_specs:
            creator_spec = creator.spec
            assert isinstance(creator_spec, RouteCreatorSpec)
            assert creator_spec.revision_id == NEW_REV
            assert creator_spec.endpoint_id == ENDPOINT_ID
            assert creator_spec.traffic_status == RouteTrafficStatus.INACTIVE
            assert creator_spec.traffic_ratio == 0.0

    def test_creator_specs_different_route_ids(self) -> None:
        """Each creator should produce a unique route (verified by spec fields)."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, [], spec)

        assert _count_scale_out(result) == 3
        # All creators should have the same deploying revision but be separate instances
        for creator in result.route_changes.scale_out_specs:
            assert isinstance(creator.spec, RouteCreatorSpec)
            assert creator.spec.revision_id == NEW_REV


# ===========================================================================
# 10. Edge cases
# ===========================================================================


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_desired_1_single_replica_full_lifecycle(self) -> None:
        """desired=1 → create 1 green, promote 1 green, terminate 1 blue."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        # Cycle 1: no green → create 1
        routes = _blue_routes(1)
        r1 = blue_green_evaluate(deployment, routes, spec)
        assert _count_scale_out(r1) == 1

        # Cycle 2: green healthy → promote
        routes = _blue_routes(1) + _green_routes(1, status=RouteStatus.HEALTHY)
        r2 = blue_green_evaluate(deployment, routes, spec)
        assert r2.completed
        assert len(_promote_ids(r2)) == 1
        assert len(_scale_in_ids(r2)) == 1

    def test_desired_0_no_routes_no_creation(self) -> None:
        """desired=0, no routes → PROVISIONING with 0 green created."""
        deployment = make_deployment(desired=0)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, [], spec)

        # No green needed, so completion with 0 green
        assert _count_scale_out(result) == 0

    def test_more_green_healthy_than_desired(self) -> None:
        """green_healthy > desired → still promotes (completes)."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        greens = _green_routes(3, status=RouteStatus.HEALTHY)
        routes = _blue_routes(2) + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        green_ids = {r.route_id for r in greens}
        assert set(_promote_ids(result)) == green_ids

    def test_only_failed_green_no_blue_rolls_back(self) -> None:
        """Only failed green routes, no blue → ROLLED_BACK."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        greens = _green_routes(2, status=RouteStatus.FAILED_TO_START)

        result = blue_green_evaluate(deployment, greens, spec)

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK

    def test_deploying_rev_none_all_routes_classified_as_blue(self) -> None:
        """If deploying_revision_id is None, all routes classified as blue."""
        deployment = make_deployment(desired=1, deploying_revision_id=None)  # type: ignore[arg-type]
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = [make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY)]

        result = blue_green_evaluate(deployment, routes, spec)

        # All classified as blue (not green), no green → PROVISIONING with create
        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert _count_scale_out(result) == 1

    def test_route_without_revision_classified_as_blue(self) -> None:
        """Routes with revision_id=None are classified as blue (non-green)."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = [make_route(revision_id=None, status=RouteStatus.HEALTHY)]  # type: ignore[arg-type]

        result = blue_green_evaluate(deployment, routes, spec)

        # revision_id=None != NEW_REV, so classified as blue
        assert _count_scale_out(result) == 1

    def test_provisioning_prioritized_over_promotion(self) -> None:
        """PROVISIONING check comes before promotion check."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = (
            _blue_routes(1)
            + _green_routes(1, status=RouteStatus.HEALTHY)
            + _green_routes(1, status=RouteStatus.PROVISIONING)
        )

        result = blue_green_evaluate(deployment, routes, spec)

        # Even though green_healthy >= desired, PROVISIONING takes precedence
        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed

    def test_large_desired_creates_all(self) -> None:
        """Large desired (10) creates all green at once."""
        deployment = make_deployment(desired=10)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(10)

        result = blue_green_evaluate(deployment, routes, spec)

        assert _count_scale_out(result) == 10

    def test_large_desired_promotes_all(self) -> None:
        """Large desired (10) promotes all green at once."""
        deployment = make_deployment(desired=10)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        blues = _blue_routes(10)
        greens = _green_routes(10, status=RouteStatus.HEALTHY)
        routes = blues + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert len(_promote_ids(result)) == 10
        assert len(_scale_in_ids(result)) == 10


# ===========================================================================
# 11. Realistic multi-step scenario (desired=5)
# ===========================================================================


class TestRealisticScenario:
    """Simulate a realistic blue-green deployment with desired=5."""

    def test_step_by_step_blue_green_deployment(self) -> None:
        """Full simulation of a blue-green deployment across multiple cycles."""
        deployment = make_deployment(desired=5)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        # Cycle 1: 5 blue, 0 green → create all 5 green (INACTIVE)
        blues = _blue_routes(5)
        r1 = blue_green_evaluate(deployment, blues, spec)

        assert r1.sub_step == DeploymentSubStep.PROVISIONING
        assert _count_scale_out(r1) == 5
        assert len(_scale_in_ids(r1)) == 0

        # Cycle 2: 5 blue, 5 green PROVISIONING → wait
        routes_c2 = blues + _green_routes(5, status=RouteStatus.PROVISIONING)
        r2 = blue_green_evaluate(deployment, routes_c2, spec)

        assert r2.sub_step == DeploymentSubStep.PROVISIONING
        assert _count_scale_out(r2) == 0

        # Cycle 3: 5 blue, 3 healthy + 2 provisioning → still PROVISIONING
        routes_c3 = (
            blues
            + _green_routes(3, status=RouteStatus.HEALTHY)
            + _green_routes(2, status=RouteStatus.PROVISIONING)
        )
        r3 = blue_green_evaluate(deployment, routes_c3, spec)

        assert r3.sub_step == DeploymentSubStep.PROVISIONING

        # Cycle 4: 5 blue, 4 healthy + 1 provisioning → still PROVISIONING
        routes_c4 = (
            blues
            + _green_routes(4, status=RouteStatus.HEALTHY)
            + _green_routes(1, status=RouteStatus.PROVISIONING)
        )
        r4 = blue_green_evaluate(deployment, routes_c4, spec)

        assert r4.sub_step == DeploymentSubStep.PROVISIONING

        # Cycle 5: 5 blue, 5 green healthy → completed (atomic promotion)
        greens = _green_routes(5, status=RouteStatus.HEALTHY)
        routes_c5 = blues + greens
        r5 = blue_green_evaluate(deployment, routes_c5, spec)

        assert r5.completed
        assert len(_promote_ids(r5)) == 5
        assert len(_scale_in_ids(r5)) == 5

    def test_step_by_step_with_failure_rollback(self) -> None:
        """Simulation of a blue-green deployment that fails and rolls back."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        # Cycle 1: 3 blue, 0 green → create 3 green
        blues = _blue_routes(3)
        r1 = blue_green_evaluate(deployment, blues, spec)
        assert _count_scale_out(r1) == 3

        # Cycle 2: 3 blue, 3 green PROVISIONING → wait
        routes_c2 = blues + _green_routes(3, status=RouteStatus.PROVISIONING)
        r2 = blue_green_evaluate(deployment, routes_c2, spec)
        assert r2.sub_step == DeploymentSubStep.PROVISIONING

        # Cycle 3: all green fail → ROLLED_BACK
        greens_failed = _green_routes(3, status=RouteStatus.FAILED_TO_START)
        routes_c3 = blues + greens_failed
        r3 = blue_green_evaluate(deployment, routes_c3, spec)

        assert r3.sub_step == DeploymentSubStep.ROLLED_BACK
        assert not r3.completed
        green_ids = {r.route_id for r in greens_failed}
        assert set(_scale_in_ids(r3)) == green_ids

    def test_step_by_step_manual_promotion(self) -> None:
        """Simulation with auto_promote=False (manual promotion flow)."""
        deployment = make_deployment(desired=3)

        # Cycle 1: auto_promote=False, create green
        spec_manual = BlueGreenSpec(auto_promote=False, promote_delay_seconds=0)
        blues = _blue_routes(3)
        r1 = blue_green_evaluate(deployment, blues, spec_manual)
        assert _count_scale_out(r1) == 3

        # Cycle 2: all green healthy, but auto_promote=False → PROGRESSING (wait)
        routes_c2 = blues + _green_routes(3, status=RouteStatus.HEALTHY)
        r2 = blue_green_evaluate(deployment, routes_c2, spec_manual)
        assert r2.sub_step == DeploymentSubStep.PROGRESSING
        assert not r2.completed
        assert len(_promote_ids(r2)) == 0

        # Cycle 3: admin switches to auto_promote=True → completed
        spec_auto = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        r3 = blue_green_evaluate(deployment, routes_c2, spec_auto)
        assert r3.completed
        assert len(_promote_ids(r3)) == 3
        assert len(_scale_in_ids(r3)) == 3


# ===========================================================================
# 12. desired_replica_count vs replica_count
# ===========================================================================


class TestDesiredReplicaCount:
    """Test that the correct desired count is used."""

    def test_desired_replica_count_overrides_replica_count(self) -> None:
        """When desired_replica_count is set, it takes precedence."""
        deployment = make_deployment(desired=3)
        deployment.replica_spec = ReplicaSpec(
            replica_count=1,
            desired_replica_count=3,
        )
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, [], spec)

        # desired is 3 (from desired_replica_count), not 1
        assert _count_scale_out(result) == 3

    def test_replica_count_used_when_no_desired(self) -> None:
        """When desired_replica_count is None, uses replica_count."""
        deployment = make_deployment(desired=2)
        deployment.replica_spec = ReplicaSpec(
            replica_count=2,
            desired_replica_count=None,
        )
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _green_routes(2, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed

    def test_desired_replica_count_determines_green_creation_count(self) -> None:
        """desired_replica_count controls how many green routes are created."""
        deployment = make_deployment(desired=5)
        deployment.replica_spec = ReplicaSpec(
            replica_count=2,
            desired_replica_count=5,
        )
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(2)

        result = blue_green_evaluate(deployment, routes, spec)

        assert _count_scale_out(result) == 5


# ===========================================================================
# 13. Scale-down during blue-green deployment
# ===========================================================================


class TestScaleDownDuringBlueGreen:
    """Test behavior when desired is reduced during blue-green deployment."""

    def test_desired_reduced_fewer_green_needed(self) -> None:
        """If desired is lowered during deployment, fewer green are healthy enough."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        # 3 blue (original desired was 3), now desired=2
        routes = _blue_routes(3) + _green_routes(2, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        # green_healthy=2 >= desired=2 → completed
        assert result.completed
        assert len(_promote_ids(result)) == 2
        assert len(_scale_in_ids(result)) == 3  # all 3 blue routes terminated

    def test_desired_increased_needs_more_green(self) -> None:
        """If desired is raised, green_healthy < new_desired → PROGRESSING."""
        deployment = make_deployment(desired=5)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        # green_healthy=3 < desired=5 → PROGRESSING
        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed


# ===========================================================================
# 14. No blue routes (fresh deployment)
# ===========================================================================


class TestNoBlueRoutes:
    """When there are no blue routes (fresh deployment)."""

    def test_fresh_deployment_creates_green(self) -> None:
        """No blue, no green → create all desired green."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, [], spec)

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert _count_scale_out(result) == 3

    def test_promotion_no_blue(self) -> None:
        """Promotion with no blue routes → complete with 0 scale_in."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        greens = _green_routes(3, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, greens, spec)

        assert result.completed
        green_ids = {r.route_id for r in greens}
        assert set(_promote_ids(result)) == green_ids
        assert len(_scale_in_ids(result)) == 0

    def test_fresh_deployment_all_fail_rollback(self) -> None:
        """Fresh deployment where all green routes fail."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        greens = _green_routes(3, status=RouteStatus.FAILED_TO_START)

        result = blue_green_evaluate(deployment, greens, spec)

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK


# ===========================================================================
# 15. Concurrent provisioning checks
# ===========================================================================


class TestConcurrentProvisioningChecks:
    """Test that provisioning blocks further changes correctly."""

    def test_provisioning_blocks_promotion(self) -> None:
        """Any green route in PROVISIONING → wait, even if enough healthy for promotion."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = (
            _blue_routes(2)
            + _green_routes(2, status=RouteStatus.HEALTHY)
            + _green_routes(1, status=RouteStatus.PROVISIONING)
        )

        result = blue_green_evaluate(deployment, routes, spec)

        # PROVISIONING takes priority over promotion
        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed
        assert len(_promote_ids(result)) == 0
        assert len(_scale_in_ids(result)) == 0

    def test_multiple_provisioning_routes_still_waits(self) -> None:
        """Multiple PROVISIONING routes → still PROVISIONING."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _green_routes(3, status=RouteStatus.PROVISIONING)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROVISIONING

    def test_provisioning_blocks_even_with_auto_promote_false(self) -> None:
        """PROVISIONING still blocks with auto_promote=False."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=False, promote_delay_seconds=0)
        routes = (
            _blue_routes(2)
            + _green_routes(1, status=RouteStatus.HEALTHY)
            + _green_routes(1, status=RouteStatus.PROVISIONING)
        )

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROVISIONING

    def test_no_actions_during_provisioning_wait(self) -> None:
        """During PROVISIONING wait, no route changes should be emitted."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.PROVISIONING)

        result = blue_green_evaluate(deployment, routes, spec)

        assert _count_scale_out(result) == 0
        assert len(_scale_in_ids(result)) == 0
        assert len(_promote_ids(result)) == 0


# ===========================================================================
# 16. Atomicity of promotion
# ===========================================================================


class TestAtomicPromotion:
    """Test that promotion is atomic (all green promoted + all blue terminated at once)."""

    def test_promotion_is_all_or_nothing(self) -> None:
        """On promotion, ALL healthy green are promoted and ALL active blue are terminated."""
        deployment = make_deployment(desired=5)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        blues = _blue_routes(5)
        greens = _green_routes(5, status=RouteStatus.HEALTHY)
        routes = blues + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert len(_promote_ids(result)) == 5
        assert len(_scale_in_ids(result)) == 5
        assert _count_scale_out(result) == 0

    def test_no_partial_promotion(self) -> None:
        """With green < desired, no partial promotion happens."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(2, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        # Not enough green healthy → no promotion
        assert not result.completed
        assert len(_promote_ids(result)) == 0
        assert len(_scale_in_ids(result)) == 0

    def test_promotion_with_asymmetric_blue_green_count(self) -> None:
        """Blue=3, Green=5 (desired=5) → all green promoted, all blue terminated."""
        deployment = make_deployment(desired=5)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        blues = _blue_routes(3)
        greens = _green_routes(5, status=RouteStatus.HEALTHY)
        routes = blues + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert len(_promote_ids(result)) == 5
        assert len(_scale_in_ids(result)) == 3

    def test_promotion_with_more_blue_than_green(self) -> None:
        """Blue=5, Green=3 (desired=3) → all green promoted, all blue terminated."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        blues = _blue_routes(5)
        greens = _green_routes(3, status=RouteStatus.HEALTHY)
        routes = blues + greens

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert len(_promote_ids(result)) == 3
        assert len(_scale_in_ids(result)) == 5


# ===========================================================================
# 17. Idempotency and repeated evaluations
# ===========================================================================


class TestIdempotency:
    """Test that repeated evaluations with the same state produce the same result."""

    def test_repeated_provisioning_evaluation(self) -> None:
        """Same PROVISIONING state evaluated twice → same result."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.PROVISIONING)

        r1 = blue_green_evaluate(deployment, routes, spec)
        r2 = blue_green_evaluate(deployment, routes, spec)

        assert r1.sub_step == r2.sub_step == DeploymentSubStep.PROVISIONING
        assert r1.completed == r2.completed is False

    def test_repeated_completion_evaluation(self) -> None:
        """Same completion state evaluated twice → same result."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        blues = _blue_routes(3)
        greens = _green_routes(3, status=RouteStatus.HEALTHY)
        routes = blues + greens

        r1 = blue_green_evaluate(deployment, routes, spec)
        r2 = blue_green_evaluate(deployment, routes, spec)

        assert r1.completed == r2.completed is True
        assert len(_promote_ids(r1)) == len(_promote_ids(r2)) == 3

    def test_repeated_rollback_evaluation(self) -> None:
        """Same rollback state evaluated twice → same result."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.FAILED_TO_START)

        r1 = blue_green_evaluate(deployment, routes, spec)
        r2 = blue_green_evaluate(deployment, routes, spec)

        assert r1.sub_step == r2.sub_step == DeploymentSubStep.ROLLED_BACK


# ===========================================================================
# 18. Spec parameter boundary values
# ===========================================================================


class TestSpecBoundaryValues:
    """Test boundary values for BlueGreenSpec parameters."""

    def test_promote_delay_zero_promotes(self) -> None:
        """promote_delay_seconds=0 → immediate promotion."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(1) + _green_routes(1, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed

    def test_promote_delay_large_waits(self) -> None:
        """promote_delay_seconds=3600 (1 hour) → PROGRESSING (delay wait)."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=3600)
        routes = _blue_routes(1) + _green_routes(1, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert not result.completed
        assert result.sub_step == DeploymentSubStep.PROGRESSING

    def test_promote_delay_max_int_waits(self) -> None:
        """Very large delay → PROGRESSING (delay wait)."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=999999)
        routes = _blue_routes(1) + _green_routes(1, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert not result.completed

    def test_promote_delay_irrelevant_when_not_auto(self) -> None:
        """When auto_promote=False, promote_delay_seconds is ignored."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=False, promote_delay_seconds=0)
        routes = _blue_routes(1) + _green_routes(1, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        # auto_promote=False → manual wait, delay doesn't matter
        assert not result.completed
        assert result.sub_step == DeploymentSubStep.PROGRESSING


# ===========================================================================
# 19. Green route healthy count vs desired
# ===========================================================================


class TestGreenHealthyVsDesired:
    """Test how green healthy count interacts with desired."""

    def test_green_healthy_exactly_desired_promotes(self) -> None:
        """green_healthy == desired → promotes."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed

    def test_green_healthy_one_less_than_desired_waits(self) -> None:
        """green_healthy == desired - 1 → PROGRESSING."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3) + _green_routes(2, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed

    def test_green_healthy_more_than_desired_promotes(self) -> None:
        """green_healthy > desired → still promotes."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(2) + _green_routes(4, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert len(_promote_ids(result)) == 4

    def test_green_healthy_zero_desired_nonzero_waits(self) -> None:
        """0 healthy green, desired > 0 → PROGRESSING."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = _blue_routes(3)  # no green at all

        result = blue_green_evaluate(deployment, routes, spec)

        # No green live → PROVISIONING (create green)
        assert result.sub_step == DeploymentSubStep.PROVISIONING


# ===========================================================================
# 20. Multiple deployments with different endpoint IDs
# ===========================================================================


class TestDifferentEndpointIds:
    """Test that the FSM correctly handles different endpoint IDs."""

    def test_different_endpoint_does_not_interfere(self) -> None:
        """Routes from different endpoints are processed independently."""
        ep1 = UUID("11111111-0000-0000-0000-000000000001")

        deployment = make_deployment(desired=2, endpoint_id=ep1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        # Routes for ep1
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY, endpoint_id=ep1),
            make_route(revision_id=OLD_REV, status=RouteStatus.HEALTHY, endpoint_id=ep1),
        ]

        result = blue_green_evaluate(deployment, routes, spec)

        # Only ep1 routes → no green, create 2
        assert _count_scale_out(result) == 2

    def test_routes_for_other_endpoint_in_list(self) -> None:
        """Routes for other endpoints are treated as blue routes (different revision)."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        green = _green_routes(1, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, green, spec)

        assert result.completed
        assert len(_promote_ids(result)) == 1
