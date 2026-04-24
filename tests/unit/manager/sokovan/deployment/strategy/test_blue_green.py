"""Tests for the blue-green FSM evaluation (BEP-1049).

Tests cover:
- FSM state transitions: PROVISIONING, AWAITING_PROMOTION
- Route status classification (HEALTHY, UNHEALTHY, DEGRADED, FAILED_TO_START, …)
- Edge cases and boundary conditions

Note: Rollback is not decided by the FSM — the coordinator's timeout
sweep handles it.  The FSM only returns PROVISIONING or AWAITING_PROMOTION.
Actual promotion (auto or manual) is handled by AwaitingPromotionHandler.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.dto.manager.v2.deployment.types import IntOrPercent
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
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.repositories.deployment.creators import RouteCreatorSpec
from ai.backend.manager.sokovan.deployment.strategy.blue_green import BlueGreenStrategy

ENDPOINT_ID = UUID("aaaaaaaa-0000-0000-0000-aaaaaaaaaaaa")
OLD_REV = UUID("11111111-1111-1111-1111-111111111111")
NEW_REV = UUID("22222222-2222-2222-2222-222222222222")
PROJECT_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
USER_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_deployment(
    *,
    desired: int = 2,
    deploying_revision_id: UUID = NEW_REV,
    current_revision_id: UUID = OLD_REV,
) -> DeploymentInfo:
    return DeploymentInfo(
        id=ENDPOINT_ID,
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
            desired_replica_count=desired,
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
    created_at: datetime | None = None,
) -> RouteInfo:
    is_active = status.is_active()
    return RouteInfo(
        route_id=uuid4(),
        endpoint_id=ENDPOINT_ID,
        session_id=None,
        status=status,
        health_status=health_status,
        traffic_ratio=1.0 if is_active else 0.0,
        created_at=created_at or datetime.now(UTC),
        revision_id=revision_id,
        traffic_status=RouteTrafficStatus.ACTIVE if is_active else RouteTrafficStatus.INACTIVE,
    )


# ===========================================================================
# 1. Basic FSM states
# ===========================================================================


class TestBasicFSMStates:
    """Test fundamental FSM transitions: PROVISIONING and AWAITING_PROMOTION."""

    def test_no_routes_creates_green(self) -> None:
        """First cycle with 0 routes → PROVISIONING with INACTIVE green route creation."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = BlueGreenStrategy().evaluate_cycle(deployment, [], spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING
        assert len(result.route_changes.rollout_specs) == 2

    def test_only_blue_routes_creates_green(self) -> None:
        """Only old-revision routes exist → create all green routes."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
        ]

        result = BlueGreenStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING
        assert len(result.route_changes.rollout_specs) == 2

    def test_green_provisioning_waits(self) -> None:
        """Green routes in PROVISIONING → wait (no create, no drain)."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.PROVISIONING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = BlueGreenStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING
        assert len(result.route_changes.rollout_specs) == 0
        assert len(result.route_changes.drain_route_ids) == 0

    def test_all_green_healthy_auto_promote_awaits(self) -> None:
        """All green HEALTHY + auto_promote → AWAITING_PROMOTION (handler does actual promote)."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = BlueGreenStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_AWAITING_PROMOTION
        assert len(result.route_changes.promote_route_ids) == 0
        assert len(result.route_changes.drain_route_ids) == 0

    def test_all_green_healthy_manual_promote_awaits(self) -> None:
        """All green HEALTHY + manual promote → AWAITING_PROMOTION (no promote/drain)."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=False)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = BlueGreenStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_AWAITING_PROMOTION
        assert len(result.route_changes.promote_route_ids) == 0
        assert len(result.route_changes.drain_route_ids) == 0

    @pytest.mark.parametrize(
        "failed_status",
        [
            pytest.param(RouteStatus.FAILED_TO_START, id="failed_to_start"),
            pytest.param(RouteStatus.TERMINATED, id="terminated"),
        ],
    )
    def test_all_green_failed_waits_for_timeout(self, failed_status: RouteStatus) -> None:
        """All green routes failed → PROVISIONING (coordinator timeout handles rollback)."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = [
            make_route(revision_id=NEW_REV, status=failed_status),
            make_route(revision_id=NEW_REV, status=failed_status),
        ]

        result = BlueGreenStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING
        assert len(result.route_changes.rollout_specs) == 0


# ===========================================================================
# 2. Route status classification
# ===========================================================================


class TestRouteStatusClassification:
    """Test how different route statuses affect classification."""

    def test_degraded_green_treated_as_unhealthy(self) -> None:
        """DEGRADED green routes are treated as unhealthy (still warming up)."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, health_status=RouteHealthStatus.DEGRADED),
        ]

        result = BlueGreenStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING

    def test_not_checked_green_treated_as_unhealthy(self) -> None:
        """NOT_CHECKED green routes are treated as unhealthy (health check pending)."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(
                revision_id=NEW_REV,
                status=RouteStatus.RUNNING,
                health_status=RouteHealthStatus.NOT_CHECKED,
            ),
        ]

        result = BlueGreenStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING

    def test_unhealthy_green_blocks_promotion(self) -> None:
        """UNHEALTHY green routes count as running but not healthy → blocks promotion."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, health_status=RouteHealthStatus.UNHEALTHY),
        ]

        result = BlueGreenStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING
        assert len(result.route_changes.rollout_specs) == 0

    def test_unhealthy_green_prevents_duplicate_creation(self) -> None:
        """UNHEALTHY green routes are counted in total_green_running → no duplicate creation."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = [
            make_route(revision_id=NEW_REV, health_status=RouteHealthStatus.UNHEALTHY),
            make_route(revision_id=NEW_REV, health_status=RouteHealthStatus.UNHEALTHY),
        ]

        result = BlueGreenStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING
        assert len(result.route_changes.rollout_specs) == 0

    @pytest.mark.parametrize(
        "inactive_status",
        [
            pytest.param(RouteStatus.TERMINATING, id="terminating"),
            pytest.param(RouteStatus.TERMINATED, id="terminated"),
        ],
    )
    def test_blue_inactive_not_counted_as_active(self, inactive_status: RouteStatus) -> None:
        """Blue routes in terminal states are not counted as blue_active."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = [
            make_route(revision_id=OLD_REV, status=inactive_status),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = BlueGreenStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_AWAITING_PROMOTION

    def test_partial_green_failure_continues_waiting(self) -> None:
        """Some green failed, some healthy → PROVISIONING (not enough healthy)."""
        deployment = make_deployment(desired=3)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.FAILED_TO_START),
        ]

        result = BlueGreenStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING


# ===========================================================================
# 3. Edge cases
# ===========================================================================


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_single_replica_deployment(self) -> None:
        """desired=1 with 1 blue + 1 green healthy → AWAITING_PROMOTION."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING),
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = BlueGreenStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_AWAITING_PROMOTION

    def test_partial_green_healthy_waits(self) -> None:
        """1 of 2 green healthy → PROVISIONING (waiting for the other)."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = [
            make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING),
        ]

        result = BlueGreenStrategy().evaluate_cycle(deployment, routes, spec)

        assert result.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING

    def test_deploying_revision_none_rejected(self) -> None:
        """If deploying_revision_id is None, evaluate_cycle raises."""
        deployment = make_deployment(desired=1, deploying_revision_id=None)  # type: ignore[arg-type]
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)
        routes = [make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING)]

        with pytest.raises(Exception):  # InvalidEndpointState
            BlueGreenStrategy().evaluate_cycle(deployment, routes, spec)

    def test_wrong_spec_type_rejected(self) -> None:
        """Passing non-BlueGreenSpec raises TypeError."""
        deployment = make_deployment(desired=1)
        spec = RollingUpdateSpec(
            max_surge=IntOrPercent(count=1), max_unavailable=IntOrPercent(count=0)
        )
        routes: list[RouteInfo] = []

        with pytest.raises(TypeError, match="Expected BlueGreenSpec"):
            BlueGreenStrategy().evaluate_cycle(deployment, routes, spec)


# ===========================================================================
# 4. Route creator specs validation
# ===========================================================================


class TestRouteCreatorSpecs:
    """Validate that route creator specs have correct fields."""

    def test_creator_specs_use_deploying_revision(self) -> None:
        """Created green routes should use the deploying revision metadata."""
        deployment = make_deployment(desired=1)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = BlueGreenStrategy().evaluate_cycle(deployment, [], spec)

        assert len(result.route_changes.rollout_specs) == 1
        creator_spec = result.route_changes.rollout_specs[0].spec
        assert isinstance(creator_spec, RouteCreatorSpec)
        assert creator_spec.revision_id == NEW_REV
        assert creator_spec.endpoint_id == ENDPOINT_ID
        assert creator_spec.session_owner_id == USER_ID
        assert creator_spec.domain == "default"
        assert creator_spec.project_id == PROJECT_ID

    def test_green_routes_created_as_inactive(self) -> None:
        """Green routes must be created with INACTIVE traffic status and ratio 0.0."""
        deployment = make_deployment(desired=2)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = BlueGreenStrategy().evaluate_cycle(deployment, [], spec)

        for creator in result.route_changes.rollout_specs:
            creator_spec = creator.spec
            assert isinstance(creator_spec, RouteCreatorSpec)
            assert creator_spec.traffic_status == RouteTrafficStatus.INACTIVE
            assert creator_spec.traffic_ratio == 0.0


# ===========================================================================
# 5. Realistic multi-step scenario (desired=3)
# ===========================================================================


class TestRealisticScenario:
    """Simulate a realistic blue-green deployment across multiple cycles."""

    def test_step_by_step_blue_green(self) -> None:
        """Full simulation: create → provision → awaiting_promotion."""
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        # Cycle 1: 3 blue, no green → create 3 INACTIVE green routes
        deployment = make_deployment(desired=3)
        blue_routes = [
            make_route(revision_id=OLD_REV, status=RouteStatus.RUNNING) for _ in range(3)
        ]
        result_1 = BlueGreenStrategy().evaluate_cycle(deployment, blue_routes, spec)
        assert result_1.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING
        assert len(result_1.route_changes.rollout_specs) == 3

        # Cycle 2: 3 blue + 3 green PROVISIONING → wait
        routes_2 = [
            *blue_routes,
            *[make_route(revision_id=NEW_REV, status=RouteStatus.PROVISIONING) for _ in range(3)],
        ]
        result_2 = BlueGreenStrategy().evaluate_cycle(deployment, routes_2, spec)
        assert result_2.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING
        assert len(result_2.route_changes.rollout_specs) == 0

        # Cycle 3: 3 blue + 2 green HEALTHY + 1 green PROVISIONING → still waiting
        routes_3 = [
            *blue_routes,
            *[make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING) for _ in range(2)],
            make_route(revision_id=NEW_REV, status=RouteStatus.PROVISIONING),
        ]
        result_3 = BlueGreenStrategy().evaluate_cycle(deployment, routes_3, spec)
        assert result_3.sub_step == DeploymentLifecycleSubStep.DEPLOYING_PROVISIONING

        # Cycle 4: 3 blue + 3 green HEALTHY → AWAITING_PROMOTION
        routes_4 = [
            *blue_routes,
            *[make_route(revision_id=NEW_REV, status=RouteStatus.RUNNING) for _ in range(3)],
        ]
        result_4 = BlueGreenStrategy().evaluate_cycle(deployment, routes_4, spec)
        assert result_4.sub_step == DeploymentLifecycleSubStep.DEPLOYING_AWAITING_PROMOTION
