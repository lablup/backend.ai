"""Unit tests for the blue-green deployment strategy FSM (BEP-1049)."""

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

# ── Helpers ──


def _make_deployment(
    *,
    desired: int = 3,
    deploying_revision_id: UUID | None = None,
    current_revision_id: UUID | None = None,
) -> DeploymentInfo:
    endpoint_id = uuid4()
    return DeploymentInfo(
        id=endpoint_id,
        metadata=DeploymentMetadata(
            name="test-deployment",
            domain="default",
            project=uuid4(),
            resource_group="default",
            created_user=uuid4(),
            session_owner=uuid4(),
            created_at=datetime.now(UTC),
            revision_history_limit=5,
        ),
        state=DeploymentState(
            lifecycle=EndpointLifecycle.DEPLOYING,
            retry_count=0,
        ),
        replica_spec=ReplicaSpec(replica_count=desired),
        network=DeploymentNetworkSpec(
            open_to_public=False,
        ),
        model_revisions=[],
        current_revision_id=current_revision_id or uuid4(),
        deploying_revision_id=deploying_revision_id or uuid4(),
    )


def _make_route(
    *,
    endpoint_id: UUID,
    revision_id: UUID | None = None,
    status: RouteStatus = RouteStatus.HEALTHY,
    traffic_status: RouteTrafficStatus = RouteTrafficStatus.ACTIVE,
    traffic_ratio: float = 1.0,
) -> RouteInfo:
    return RouteInfo(
        route_id=uuid4(),
        endpoint_id=endpoint_id,
        session_id=SessionId(uuid4()),
        status=status,
        traffic_ratio=traffic_ratio,
        created_at=datetime.now(UTC),
        revision_id=revision_id,
        traffic_status=traffic_status,
    )


def _blue_routes(
    deployment: DeploymentInfo,
    count: int,
    *,
    status: RouteStatus = RouteStatus.HEALTHY,
) -> list[RouteInfo]:
    return [
        _make_route(
            endpoint_id=deployment.id,
            revision_id=deployment.current_revision_id,
            status=status,
            traffic_status=RouteTrafficStatus.ACTIVE,
            traffic_ratio=1.0,
        )
        for _ in range(count)
    ]


def _green_routes(
    deployment: DeploymentInfo,
    count: int,
    *,
    status: RouteStatus = RouteStatus.HEALTHY,
    traffic_status: RouteTrafficStatus = RouteTrafficStatus.INACTIVE,
    traffic_ratio: float = 0.0,
) -> list[RouteInfo]:
    return [
        _make_route(
            endpoint_id=deployment.id,
            revision_id=deployment.deploying_revision_id,
            status=status,
            traffic_status=traffic_status,
            traffic_ratio=traffic_ratio,
        )
        for _ in range(count)
    ]


# ── Test Classes ──


class TestBlueGreenNoGreenRoutes:
    """When no green routes exist, all should be created as INACTIVE."""

    def test_creates_all_green_inactive(self) -> None:
        deployment = _make_deployment(desired=3)
        blues = _blue_routes(deployment, 3)

        result = blue_green_evaluate(deployment, blues, BlueGreenSpec())

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed
        assert len(result.route_changes.scale_out_specs) == 3
        assert not result.route_changes.scale_in_route_ids
        assert not result.route_changes.promote_route_ids

    def test_creator_spec_has_inactive_traffic(self) -> None:
        deployment = _make_deployment(desired=2)
        blues = _blue_routes(deployment, 2)

        result = blue_green_evaluate(deployment, blues, BlueGreenSpec())

        for creator in result.route_changes.scale_out_specs:
            spec = creator.spec
            assert isinstance(spec, RouteCreatorSpec)
            assert spec.traffic_status == RouteTrafficStatus.INACTIVE
            assert spec.traffic_ratio == 0.0
            assert spec.revision_id == deployment.deploying_revision_id

    def test_no_blue_routes_fresh_deployment(self) -> None:
        """First deployment with no existing routes."""
        deployment = _make_deployment(desired=3)

        result = blue_green_evaluate(deployment, [], BlueGreenSpec())

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert len(result.route_changes.scale_out_specs) == 3


class TestBlueGreenProvisioning:
    """When green routes are still PROVISIONING, the FSM should wait."""

    def test_all_green_provisioning(self) -> None:
        deployment = _make_deployment(desired=3)
        blues = _blue_routes(deployment, 3)
        greens = _green_routes(deployment, 3, status=RouteStatus.PROVISIONING)

        result = blue_green_evaluate(deployment, blues + greens, BlueGreenSpec())

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed
        assert not result.route_changes.scale_out_specs
        assert not result.route_changes.scale_in_route_ids
        assert not result.route_changes.promote_route_ids

    def test_partial_provisioning_partial_healthy(self) -> None:
        deployment = _make_deployment(desired=3)
        blues = _blue_routes(deployment, 3)
        greens = _green_routes(deployment, 1, status=RouteStatus.HEALTHY) + _green_routes(
            deployment, 2, status=RouteStatus.PROVISIONING
        )

        result = blue_green_evaluate(deployment, blues + greens, BlueGreenSpec())

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed


class TestBlueGreenAllGreenFailed:
    """When all green routes have failed, rollback should occur."""

    def test_all_green_failed_rollback(self) -> None:
        deployment = _make_deployment(desired=3)
        blues = _blue_routes(deployment, 3)
        greens = _green_routes(deployment, 3, status=RouteStatus.FAILED_TO_START)

        result = blue_green_evaluate(deployment, blues + greens, BlueGreenSpec())

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK
        assert not result.completed
        green_ids = {r.route_id for r in greens}
        assert set(result.route_changes.scale_in_route_ids) == green_ids
        assert not result.route_changes.promote_route_ids

    def test_all_green_terminated_rollback(self) -> None:
        deployment = _make_deployment(desired=2)
        blues = _blue_routes(deployment, 2)
        greens = _green_routes(deployment, 2, status=RouteStatus.TERMINATED)

        result = blue_green_evaluate(deployment, blues + greens, BlueGreenSpec())

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK
        assert not result.completed


class TestBlueGreenMixedGreen:
    """When green routes are in mixed states (healthy + failed, no provisioning)."""

    def test_healthy_and_failed_mixed(self) -> None:
        deployment = _make_deployment(desired=3)
        blues = _blue_routes(deployment, 3)
        greens = _green_routes(deployment, 1, status=RouteStatus.HEALTHY) + _green_routes(
            deployment, 2, status=RouteStatus.FAILED_TO_START
        )

        result = blue_green_evaluate(deployment, blues + greens, BlueGreenSpec())

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed


class TestBlueGreenPromotion:
    """When all green routes are healthy and promotion should happen."""

    def test_auto_promote_true_delay_zero_completed(self) -> None:
        deployment = _make_deployment(desired=3)
        blues = _blue_routes(deployment, 3)
        greens = _green_routes(deployment, 3, status=RouteStatus.HEALTHY)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, blues + greens, spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert result.completed
        # Green route IDs should be promoted
        green_ids = {r.route_id for r in greens}
        assert set(result.route_changes.promote_route_ids) == green_ids
        # Blue route IDs should be scaled in
        blue_ids = {r.route_id for r in blues}
        assert set(result.route_changes.scale_in_route_ids) == blue_ids
        # No new routes created
        assert not result.route_changes.scale_out_specs

    def test_auto_promote_false_manual_wait(self) -> None:
        deployment = _make_deployment(desired=3)
        blues = _blue_routes(deployment, 3)
        greens = _green_routes(deployment, 3, status=RouteStatus.HEALTHY)
        spec = BlueGreenSpec(auto_promote=False, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, blues + greens, spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed
        assert not result.route_changes.promote_route_ids
        assert not result.route_changes.scale_in_route_ids

    def test_auto_promote_true_delay_positive_wait(self) -> None:
        deployment = _make_deployment(desired=3)
        blues = _blue_routes(deployment, 3)
        greens = _green_routes(deployment, 3, status=RouteStatus.HEALTHY)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=60)

        result = blue_green_evaluate(deployment, blues + greens, spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed
        assert not result.route_changes.promote_route_ids
        assert not result.route_changes.scale_in_route_ids


class TestBlueGreenSingleReplica:
    """Edge case: desired=1 single replica."""

    def test_single_replica_no_green(self) -> None:
        deployment = _make_deployment(desired=1)
        blues = _blue_routes(deployment, 1)

        result = blue_green_evaluate(deployment, blues, BlueGreenSpec())

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert len(result.route_changes.scale_out_specs) == 1

    def test_single_replica_promotion(self) -> None:
        deployment = _make_deployment(desired=1)
        blues = _blue_routes(deployment, 1)
        greens = _green_routes(deployment, 1, status=RouteStatus.HEALTHY)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, blues + greens, spec)

        assert result.completed
        assert len(result.route_changes.promote_route_ids) == 1
        assert len(result.route_changes.scale_in_route_ids) == 1


class TestBlueGreenManyReplicas:
    """Edge case: desired=5 many replicas."""

    def test_many_replicas_creates_all(self) -> None:
        deployment = _make_deployment(desired=5)
        blues = _blue_routes(deployment, 5)

        result = blue_green_evaluate(deployment, blues, BlueGreenSpec())

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert len(result.route_changes.scale_out_specs) == 5

    def test_many_replicas_promotion(self) -> None:
        deployment = _make_deployment(desired=5)
        blues = _blue_routes(deployment, 5)
        greens = _green_routes(deployment, 5, status=RouteStatus.HEALTHY)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, blues + greens, spec)

        assert result.completed
        assert len(result.route_changes.promote_route_ids) == 5
        assert len(result.route_changes.scale_in_route_ids) == 5


class TestBlueGreenNoBlueRoutes:
    """When there are no blue routes (fresh deployment)."""

    def test_promotion_no_blue(self) -> None:
        """Promotion with no blue routes to terminate."""
        deployment = _make_deployment(desired=3)
        greens = _green_routes(deployment, 3, status=RouteStatus.HEALTHY)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, greens, spec)

        assert result.completed
        green_ids = {r.route_id for r in greens}
        assert set(result.route_changes.promote_route_ids) == green_ids
        assert not result.route_changes.scale_in_route_ids


class TestBlueGreenPromotionRouteIdVerification:
    """Verify promote and scale_in route IDs are exact matches."""

    def test_promote_ids_match_green_healthy(self) -> None:
        deployment = _make_deployment(desired=3)
        blues = _blue_routes(deployment, 3)
        greens = _green_routes(deployment, 3, status=RouteStatus.HEALTHY)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, blues + greens, spec)

        expected_promote = [r.route_id for r in greens]
        assert result.route_changes.promote_route_ids == expected_promote

    def test_scale_in_ids_match_blue_active(self) -> None:
        deployment = _make_deployment(desired=3)
        blues = _blue_routes(deployment, 3)
        greens = _green_routes(deployment, 3, status=RouteStatus.HEALTHY)
        spec = BlueGreenSpec(auto_promote=True, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, blues + greens, spec)

        expected_scale_in = [r.route_id for r in blues]
        assert result.route_changes.scale_in_route_ids == expected_scale_in
