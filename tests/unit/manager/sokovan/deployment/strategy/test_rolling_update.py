"""Tests for the rolling update FSM evaluation (BEP-1049).

Tests cover:
- FSM state transitions: PROVISIONING and COMPLETED
- max_surge / max_unavailable budget calculations
- Multi-cycle progression and termination priority
- Edge cases and boundary conditions

Note: Rollback is not decided by the FSM — the coordinator's timeout
sweep handles it.  The FSM only returns PROVISIONING (with or without
route mutations) or COMPLETED.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.dto.manager.v2.deployment.types import IntOrPercent
from ai.backend.common.types import SessionId
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    DeploymentLifecycleSubStep,
    DeploymentMetadata,
    DeploymentNetworkSpec,
    DeploymentState,
    ReplicaSpec,
    RouteHealthStatus,
    RouteInfo,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.models.deployment_policy import RollingUpdateSpec
from ai.backend.manager.repositories.deployment.creators import RouteCreatorSpec
from ai.backend.manager.sokovan.deployment.exceptions import InvalidEndpointState
from ai.backend.manager.sokovan.deployment.strategy.rolling_update import (
    RollingUpdateStrategy,
)

ENDPOINT_ID = UUID("aaaaaaaa-0000-0000-0000-aaaaaaaaaaaa")


def make_int_or_percent(value: int | float) -> IntOrPercent:
    """Shorthand to build a IntOrPercent from a plain int or float."""
    if isinstance(value, float):
        return IntOrPercent(percent=value)
    return IntOrPercent(count=value)


OLD_REV = UUID("11111111-1111-1111-1111-111111111111")
NEW_REV = UUID("22222222-2222-2222-2222-222222222222")
PROJECT_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
USER_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


# ---------------------------------------------------------------------------
# Test scenario types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RollingUpdateInput:
    """Input conditions for a rolling update cycle test."""

    desired_replicas: int
    max_surge: IntOrPercent
    max_unavailable: IntOrPercent
    old_count: int


@dataclass(frozen=True)
class RollingUpdateExpected:
    """Expected outcomes of a rolling update cycle."""

    create: int
    terminate: int


@dataclass(frozen=True)
class RollingUpdateScenario:
    """A single test case for the rolling update strategy with only old routes."""

    description: str
    input: RollingUpdateInput
    expected: RollingUpdateExpected


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
    status: RouteStatus = RouteStatus.RUNNING,
    health_status: RouteHealthStatus = RouteHealthStatus.HEALTHY,
    endpoint_id: UUID = ENDPOINT_ID,
    route_id: UUID | None = None,
) -> RouteInfo:
    return RouteInfo(
        route_id=route_id or uuid4(),
        endpoint_id=endpoint_id,
        session_id=SessionId(uuid4()),
        status=status,
        health_status=health_status,
        traffic_ratio=1.0 if status.is_active() else 0.0,
        created_at=datetime.now(UTC),
        revision_id=revision_id,
        traffic_status=RouteTrafficStatus.ACTIVE
        if status.is_active()
        else RouteTrafficStatus.INACTIVE,
    )


# ===========================================================================
# 1. Basic FSM states
# ===========================================================================


class TestBasicFSMStates:
    """Test fundamental FSM transitions."""

    def test_no_routes_creates_new(self) -> None:
        """First cycle with 0 routes → PROVISIONING with route creation."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )

        result = RollingUpdateStrategy().evaluate_cycle(deployment, [], spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING
        assert len(result.route_changes.rollout_specs) == 1
        assert len(result.route_changes.drain_route_ids) == 0

    def test_new_provisioning_waits(self) -> None:
        """New routes in PROVISIONING → wait (PROVISIONING sub-step)."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.PROVISIONING),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING
        assert len(result.route_changes.rollout_specs) == 0
        assert len(result.route_changes.drain_route_ids) == 0

    def test_completed_when_all_new_healthy_and_no_old(self) -> None:
        """All old gone + new_healthy >= desired → completed."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_COMPLETED

    @pytest.mark.parametrize(
        "failed_status",
        [
            pytest.param(RouteStatus.FAILED_TO_START, id="failed_to_start"),
            pytest.param(RouteStatus.TERMINATED, id="terminated"),
        ],
    )
    def test_all_new_failed_retries_creation(self, failed_status: RouteStatus) -> None:
        """All new routes failed → FSM retries by creating new routes.

        Rollback is handled by the coordinator's timeout sweep, not the FSM.
        """
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=failed_status),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING


# ===========================================================================
# 2. Surge and unavailability budget
# ===========================================================================


ROLLING_UPDATE_SCENARIOS = [
    # -- max_surge controls creation --
    RollingUpdateScenario(
        description=(
            "max_surge=1 allows exactly 1 extra route beyond desired."
            " With 1 old route and desired=1, max_total=2 so 1 new route is created."
            " No termination because max_unavailable=0 and no new healthy routes exist yet."
        ),
        input=RollingUpdateInput(
            desired_replicas=1,
            max_surge=make_int_or_percent(1),
            max_unavailable=make_int_or_percent(0),
            old_count=1,
        ),
        expected=RollingUpdateExpected(create=1, terminate=0),
    ),
    RollingUpdateScenario(
        description=(
            "max_surge=2 with desired=3 and 3 old routes: max_total=5, current=3,"
            " so can_create=2. still_needed=3 (no new yet), min(2,3)=2 routes created."
        ),
        input=RollingUpdateInput(
            desired_replicas=3,
            max_surge=make_int_or_percent(2),
            max_unavailable=make_int_or_percent(0),
            old_count=3,
        ),
        expected=RollingUpdateExpected(create=2, terminate=0),
    ),
    RollingUpdateScenario(
        description=(
            "max_surge=3 exceeds desired=2: max_total=5, can_create=3,"
            " but still_needed=2 (only 2 new routes needed), so creation is capped at 2."
        ),
        input=RollingUpdateInput(
            desired_replicas=2,
            max_surge=make_int_or_percent(3),
            max_unavailable=make_int_or_percent(0),
            old_count=2,
        ),
        expected=RollingUpdateExpected(create=2, terminate=0),
    ),
    # -- max_unavailable controls termination --
    RollingUpdateScenario(
        description=(
            "max_unavailable=0 means zero downtime: min_available equals desired=2."
            " With 2 old routes and 0 new healthy, available=2=min_available,"
            " so no old route can be terminated yet."
        ),
        input=RollingUpdateInput(
            desired_replicas=2,
            max_surge=make_int_or_percent(1),
            max_unavailable=make_int_or_percent(0),
            old_count=2,
        ),
        expected=RollingUpdateExpected(create=1, terminate=0),
    ),
    RollingUpdateScenario(
        description=(
            "max_unavailable=1 allows 1 route to be unavailable: min_available=3-1=2."
            " With 3 old routes and 0 new healthy, available=3, can_terminate=3-2=1."
        ),
        input=RollingUpdateInput(
            desired_replicas=3,
            max_surge=make_int_or_percent(1),
            max_unavailable=make_int_or_percent(1),
            old_count=3,
        ),
        expected=RollingUpdateExpected(create=1, terminate=1),
    ),
    # -- combined surge + unavailable --
    RollingUpdateScenario(
        description=(
            "Both parameters act simultaneously: max_surge=2 allows 2 new creations"
            " (max_total=6, current=4, can_create=2) while max_unavailable=1"
            " allows terminating 1 old (min_available=3, available=4, can_terminate=1)."
        ),
        input=RollingUpdateInput(
            desired_replicas=4,
            max_surge=make_int_or_percent(2),
            max_unavailable=make_int_or_percent(1),
            old_count=4,
        ),
        expected=RollingUpdateExpected(create=2, terminate=1),
    ),
    RollingUpdateScenario(
        description=(
            "Aggressive rollout: max_surge=3 and max_unavailable=2 with desired=3."
            " All 3 new routes created at once (max_total=6, can_create=3=still_needed)"
            " and 2 old terminated immediately (min_available=1, available=3, can_terminate=2)."
        ),
        input=RollingUpdateInput(
            desired_replicas=3,
            max_surge=make_int_or_percent(3),
            max_unavailable=make_int_or_percent(2),
            old_count=3,
        ),
        expected=RollingUpdateExpected(create=3, terminate=2),
    ),
    # -- boundary: unavailable > desired --
    RollingUpdateScenario(
        description=(
            "max_unavailable=5 exceeds desired=1: min_available=max(0, 1-5)=0."
            " The operator has opted into full unavailability,"
            " so the single old route can be terminated immediately."
        ),
        input=RollingUpdateInput(
            desired_replicas=1,
            max_surge=make_int_or_percent(0),
            max_unavailable=make_int_or_percent(5),
            old_count=1,
        ),
        expected=RollingUpdateExpected(create=0, terminate=1),
    ),
]


class TestSurgeAndUnavailabilityBudget:
    """Test max_surge and max_unavailable parameter controls."""

    @pytest.mark.parametrize(
        "scenario",
        ROLLING_UPDATE_SCENARIOS,
        ids=[s.description for s in ROLLING_UPDATE_SCENARIOS],
    )
    def test_budget_with_old_routes_only(self, scenario: RollingUpdateScenario) -> None:
        """Verify creation/termination counts based on surge and unavailability budgets."""
        deployment = make_deployment(desired=scenario.input.desired_replicas)
        spec = RollingUpdateSpec(
            max_surge=scenario.input.max_surge,
            max_unavailable=scenario.input.max_unavailable,
        )
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING)
            for _ in range(scenario.input.old_count)
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert len(result.route_changes.rollout_specs) == scenario.expected.create
        assert len(result.route_changes.drain_route_ids) == scenario.expected.terminate

    def test_surge_already_at_max_no_create(self) -> None:
        """Already at max_total → no new creates."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert len(result.route_changes.rollout_specs) == 0

    def test_new_healthy_allows_more_termination(self) -> None:
        """With new healthy routes, more old can be terminated."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert len(result.route_changes.drain_route_ids) == 1

    def test_surge_and_unavailable_both_zero_rejected(self) -> None:
        """surge=0, unavailable=0: rejected by Pydantic validation."""
        with pytest.raises(ValueError, match="max_surge or max_unavailable must be positive"):
            RollingUpdateSpec(
                max_surge=make_int_or_percent(0), max_unavailable=make_int_or_percent(0)
            )

    def test_surge_and_unavailable_both_zero_float_rejected(self) -> None:
        """surge=0.0, unavailable=0.0: rejected by Pydantic validation."""
        with pytest.raises(ValueError, match="max_surge or max_unavailable must be positive"):
            RollingUpdateSpec(
                max_surge=make_int_or_percent(0.0), max_unavailable=make_int_or_percent(0.0)
            )

    def test_surge_and_unavailable_mixed_zero_rejected(self) -> None:
        """surge=0, unavailable=0.0: rejected by Pydantic validation."""
        with pytest.raises(ValueError, match="max_surge or max_unavailable must be positive"):
            RollingUpdateSpec(
                max_surge=make_int_or_percent(0), max_unavailable=make_int_or_percent(0.0)
            )


# ===========================================================================
# 3. Multi-cycle progression
# ===========================================================================


class TestMultiCycleProgression:
    """Simulate multiple evaluation cycles."""

    def test_new_healthy_enables_further_creation(self) -> None:
        """After new routes become healthy, more new routes can be created."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert len(result.route_changes.rollout_specs) == 1
        assert len(result.route_changes.drain_route_ids) == 0

    def test_multiple_new_healthy_enables_old_termination(self) -> None:
        """2 new healthy, 2 old: can terminate 1 old."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert len(result.route_changes.rollout_specs) == 0
        assert len(result.route_changes.drain_route_ids) == 1

    def test_not_completed_when_old_still_exists(self) -> None:
        """Even with enough new healthy, old still exists → not completed."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING
        assert len(result.route_changes.drain_route_ids) == 1


# ===========================================================================
# 4. Route status classification
# ===========================================================================


class TestRouteStatusClassification:
    """Test how different route statuses affect classification."""

    def test_degraded_new_waits_provisioning(self) -> None:
        """DEGRADED new routes are treated as PROVISIONING (still warming up)."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(
                revision_id=NEW_REV,
                status=RouteStatus.RUNNING,
                health_status=RouteHealthStatus.DEGRADED,
            ),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING

    def test_unhealthy_new_retries(self) -> None:
        """All new UNHEALTHY → PROVISIONING (retries, timeout handles rollback)."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(
                revision_id=NEW_REV,
                status=RouteStatus.RUNNING,
                health_status=RouteHealthStatus.UNHEALTHY,
            ),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING

    @pytest.mark.parametrize(
        "inactive_status",
        [
            pytest.param(RouteStatus.TERMINATING, id="terminating"),
            pytest.param(RouteStatus.TERMINATED, id="terminated"),
        ],
    )
    def test_old_inactive_not_counted_as_active(self, inactive_status: RouteStatus) -> None:
        """Old routes in terminal states are not counted as old_active."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=OLD_REV, status=inactive_status),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_COMPLETED

    def test_partial_new_failure_continues_progress(self) -> None:
        """Some new failed, some healthy → no rollback (live routes exist)."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(2), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.FAILED_TO_START),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING

    def test_old_provisioning_counted_as_active(self) -> None:
        """Old routes in PROVISIONING are counted as old_active."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.PROVISIONING),
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING


# ===========================================================================
# 5. Termination priority ordering
# ===========================================================================


class TestTerminationPriority:
    """Test that old routes are terminated in priority order."""

    def test_full_priority_order(self) -> None:
        """Termination order: PROVISIONING(0) → UNHEALTHY(1) → DEGRADED(2) → HEALTHY(4).

        Non-RUNNING routes (priority 0) are terminated first, then by health status.
        """
        unhealthy_id = UUID("00000000-0000-0000-0000-000000000001")
        degraded_id = UUID("00000000-0000-0000-0000-000000000002")
        provisioning_id = UUID("00000000-0000-0000-0000-000000000003")
        healthy_id = UUID("00000000-0000-0000-0000-000000000004")

        deployment = make_deployment(desired=4)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(0), max_unavailable=make_int_or_percent(3)
        )
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING, route_id=healthy_id),
            make_route(
                revision_id=OLD_REV,
                status=RouteStatus.PROVISIONING,
                route_id=provisioning_id,
            ),
            make_route(
                revision_id=OLD_REV,
                status=RouteStatus.RUNNING,
                health_status=RouteHealthStatus.DEGRADED,
                route_id=degraded_id,
            ),
            make_route(
                revision_id=OLD_REV,
                status=RouteStatus.RUNNING,
                health_status=RouteHealthStatus.UNHEALTHY,
                route_id=unhealthy_id,
            ),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        terminated = result.route_changes.drain_route_ids
        assert len(terminated) == 3
        assert terminated[0] == provisioning_id
        assert terminated[1] == unhealthy_id
        assert terminated[2] == degraded_id


# ===========================================================================
# 6. Edge cases
# ===========================================================================


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_desired_0_no_routes_completed(self) -> None:
        """desired=0, no routes → completed (vacuously true)."""
        deployment = make_deployment(desired=0)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )

        result = RollingUpdateStrategy().evaluate_cycle(deployment, [], spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_COMPLETED

    def test_more_new_healthy_than_desired_still_completes(self) -> None:
        """new_healthy > desired and no old → completed."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(2), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_COMPLETED

    def test_only_failed_new_no_old_rolls_back(self) -> None:
        """Only failed new routes, no old → PROVISIONING (retries creation)."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.FAILED_TO_START),
            make_route(revision_id=NEW_REV, status=RouteStatus.FAILED_TO_START),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING

    def test_all_old_inactive_no_new_creates_desired(self) -> None:
        """All old routes are terminated, no new → create desired."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.TERMINATED),
            make_route(revision_id=OLD_REV, status=RouteStatus.TERMINATED),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert len(result.route_changes.rollout_specs) == 2

    def test_deploying_rev_none_rejected(self) -> None:
        """If deploying_revision_id is None, evaluate_cycle raises."""
        deployment = make_deployment(desired=1, deploying_revision_id=None)  # type: ignore[arg-type]
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING)]

        with pytest.raises(InvalidEndpointState):
            RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

    def test_provisioning_prioritized_over_completion_check(self) -> None:
        """PROVISIONING check comes before completion check in FSM."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.PROVISIONING),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING


# ===========================================================================
# 7. Route creator specs validation
# ===========================================================================


class TestRouteCreatorSpecs:
    """Validate that route creator specs have correct fields."""

    def test_creator_specs_use_deploying_revision(self) -> None:
        """Created routes should use the deploying revision metadata."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )

        result = RollingUpdateStrategy().evaluate_cycle(deployment, [], spec)

        assert len(result.route_changes.rollout_specs) == 1
        creator_spec = result.route_changes.rollout_specs[0].spec
        assert isinstance(creator_spec, RouteCreatorSpec)
        assert creator_spec.revision_id == NEW_REV
        assert creator_spec.endpoint_id == ENDPOINT_ID
        assert creator_spec.session_owner_id == USER_ID
        assert creator_spec.domain == "default"
        assert creator_spec.project_id == PROJECT_ID


# ===========================================================================
# 8. Realistic multi-step scenario (desired=5)
# ===========================================================================


class TestRealisticScenario:
    """Simulate a realistic rolling update with desired=5, surge=2, unavail=1."""

    def test_step_by_step_rolling_update(self) -> None:
        """Full simulation of a rolling update across multiple cycles."""
        deployment = make_deployment(desired=5)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(2), max_unavailable=make_int_or_percent(1)
        )

        # Cycle 1: 5 old → create 2, terminate 1
        old_routes = [make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING) for _ in range(5)]
        r1 = RollingUpdateStrategy().evaluate_cycle(deployment, old_routes, spec)
        assert len(r1.route_changes.rollout_specs) == 2
        assert len(r1.route_changes.drain_route_ids) == 1

        # Cycle 2: 4 old, 2 new healthy → create 1, terminate 2
        routes_c2 = [
            *[make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING) for _ in range(4)],
            *[make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING) for _ in range(2)],
        ]
        r2 = RollingUpdateStrategy().evaluate_cycle(deployment, routes_c2, spec)
        assert len(r2.route_changes.rollout_specs) == 1
        assert len(r2.route_changes.drain_route_ids) == 2

        # Cycle 3: 2 old, 3 new healthy → create 2, terminate 1
        routes_c3 = [
            *[make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING) for _ in range(2)],
            *[make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING) for _ in range(3)],
        ]
        r3 = RollingUpdateStrategy().evaluate_cycle(deployment, routes_c3, spec)
        assert len(r3.route_changes.rollout_specs) == 2
        assert len(r3.route_changes.drain_route_ids) == 1

        # Cycle 4: 1 old, 5 new healthy → create 0, terminate 1
        routes_c4 = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            *[make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING) for _ in range(5)],
        ]
        r4 = RollingUpdateStrategy().evaluate_cycle(deployment, routes_c4, spec)
        assert len(r4.route_changes.rollout_specs) == 0
        assert len(r4.route_changes.drain_route_ids) == 1
        assert r4.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING

        # Cycle 5: 0 old, 5 new healthy → completed
        routes_c5 = [make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING) for _ in range(5)]
        r5 = RollingUpdateStrategy().evaluate_cycle(deployment, routes_c5, spec)
        assert r5.sub_step == DeploymentLifecycleSubStep.DEPLOYING_COMPLETED


# ===========================================================================
# 9. Deadlock prevention
# ===========================================================================


class TestDeadlockPrevention:
    """Test scenarios where the FSM could potentially stall."""

    def test_surge_0_terminates_first_then_creates(self) -> None:
        """surge=0, unavailable=1 → terminate first, next cycle creates."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(0), max_unavailable=make_int_or_percent(1)
        )

        # Cycle 1: 3 old → terminate 1, create 0
        routes = [make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING) for _ in range(3)]
        r1 = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)
        assert len(r1.route_changes.rollout_specs) == 0
        assert len(r1.route_changes.drain_route_ids) == 1

        # Cycle 2: 2 old → create 1, terminate 0
        routes_c2 = [make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING) for _ in range(2)]
        r2 = RollingUpdateStrategy().evaluate_cycle(deployment, routes_c2, spec)
        assert len(r2.route_changes.rollout_specs) == 1
        assert len(r2.route_changes.drain_route_ids) == 0

    def test_new_routes_exceed_desired_no_extra_create(self) -> None:
        """More new_live than desired → no extra creation (still_needed < 0)."""
        deployment = make_deployment(desired=2)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(2), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert len(result.route_changes.rollout_specs) == 0
        assert len(result.route_changes.drain_route_ids) == 1

    def test_provisioning_blocks_all_further_actions(self) -> None:
        """Any new route in PROVISIONING → wait, even if old can be terminated."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(2), max_unavailable=make_int_or_percent(1)
        )
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.PROVISIONING),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING
        assert len(result.route_changes.rollout_specs) == 0
        assert len(result.route_changes.drain_route_ids) == 0


# ===========================================================================
# 10. desired_replica_count resolution
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
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING)]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert len(result.route_changes.rollout_specs) == 3

    def test_replica_count_used_when_no_desired(self) -> None:
        """When desired_replica_count is None, uses replica_count."""
        deployment = make_deployment(desired=2)
        deployment.replica_spec = ReplicaSpec(
            replica_count=2,
            desired_replica_count=None,
        )
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_COMPLETED


# ===========================================================================
# 11. Scale changes during rolling update
# ===========================================================================


class TestScaleChangeDuringRollingUpdate:
    """Test behavior when desired changes during rolling update."""

    def test_desired_reduced_terminates_excess_old(self) -> None:
        """If desired is lowered, more old can be terminated."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0)
        )
        routes = [make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING) for _ in range(3)]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert len(result.route_changes.rollout_specs) == 0
        assert len(result.route_changes.drain_route_ids) == 2

    def test_desired_increased_creates_more(self) -> None:
        """If desired is raised, more new routes are created."""
        deployment = make_deployment(desired=5)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(2), max_unavailable=make_int_or_percent(0)
        )
        routes = [make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING) for _ in range(2)]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert len(result.route_changes.rollout_specs) == 5


# ===========================================================================
# 12. Fractional (float) max_surge / max_unavailable
# ===========================================================================


class TestFractionSpec:
    """Test RollingUpdateSpec with float fraction values."""

    def test_fraction_max_surge_accepted(self) -> None:
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(0.25), max_unavailable=make_int_or_percent(0)
        )
        assert spec.max_surge.is_percent
        assert spec.max_surge.percent == 0.25

    def test_fraction_max_unavailable_accepted(self) -> None:
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0.5)
        )
        assert spec.max_unavailable.is_percent
        assert spec.max_unavailable.percent == 0.5

    def test_resolve_max_surge_rounds_up(self) -> None:
        """0.25 of 10 = 2.5 → rounds up to 3."""
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(0.25), max_unavailable=make_int_or_percent(1)
        )
        assert spec.resolve_max_surge(10) == 3

    def test_resolve_max_unavailable_rounds_down(self) -> None:
        """0.25 of 10 = 2.5 → rounds down to 2."""
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1), max_unavailable=make_int_or_percent(0.25)
        )
        assert spec.resolve_max_unavailable(10) == 2

    def test_resolve_exact_fraction(self) -> None:
        """0.5 of 4 = 2.0 → exactly 2 for both."""
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(0.5), max_unavailable=make_int_or_percent(0.5)
        )
        assert spec.resolve_max_surge(4) == 2
        assert spec.resolve_max_unavailable(4) == 2

    def test_resolve_full_fraction(self) -> None:
        """1.0 of 5 = 5."""
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(1.0), max_unavailable=make_int_or_percent(1.0)
        )
        assert spec.resolve_max_surge(5) == 5
        assert spec.resolve_max_unavailable(5) == 5

    def test_resolve_zero_fraction(self) -> None:
        """0.0 of anything = 0."""
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(0.0), max_unavailable=make_int_or_percent(1)
        )
        assert spec.resolve_max_surge(10) == 0

    def test_resolve_integer_passthrough(self) -> None:
        """Integer values pass through unchanged regardless of desired."""
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(3), max_unavailable=make_int_or_percent(2)
        )
        assert spec.resolve_max_surge(100) == 3
        assert spec.resolve_max_unavailable(100) == 2

    def test_fraction_over_1_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RollingUpdateSpec(
                max_surge=make_int_or_percent(1.5), max_unavailable=make_int_or_percent(0)
            )

    def test_negative_fraction_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RollingUpdateSpec(
                max_surge=make_int_or_percent(-0.1), max_unavailable=make_int_or_percent(0)
            )


class TestFractionStrategy:
    """Test rolling update strategy evaluation with fractional specs."""

    def test_fraction_surge_creates_correct_routes(self) -> None:
        """0.25 surge with 4 desired → max_surge=1 (ceil(1.0))."""
        deployment = make_deployment(desired=4)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(0.25), max_unavailable=make_int_or_percent(0.25)
        )
        routes = [make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING) for _ in range(4)]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING
        assert len(result.route_changes.rollout_specs) == 1

    def test_fraction_unavailable_terminates_correct_routes(self) -> None:
        """0.5 unavailable with 4 desired → max_unavailable=2.

        4 old + 2 new healthy = 6 available, min_available = 4-2 = 2
        can_terminate = 6-2 = 4, but old=4 so terminate up to 4.
        """
        deployment = make_deployment(desired=4)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(0.5), max_unavailable=make_int_or_percent(0.5)
        )
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert len(result.route_changes.drain_route_ids) == 4

    def test_small_fraction_with_few_replicas(self) -> None:
        """0.1 surge with 3 desired → ceil(0.3) = 1."""
        deployment = make_deployment(desired=3)
        spec = RollingUpdateSpec(
            max_surge=make_int_or_percent(0.1), max_unavailable=make_int_or_percent(0)
        )
        routes = [make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING) for _ in range(3)]

        result = RollingUpdateStrategy().evaluate_cycle(deployment, routes, spec)

        assert len(result.route_changes.rollout_specs) == 1
