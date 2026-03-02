"""Unit tests for blue-green deployment strategy evaluation (BEP-1049)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

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
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.deployment.creators import RouteCreatorSpec
from ai.backend.manager.sokovan.deployment.strategy.blue_green import blue_green_evaluate

# ── Helpers ──

_ENDPOINT_ID = uuid.uuid4()
_DEPLOYING_REVISION_ID = uuid.uuid4()
_OLD_REVISION_ID = uuid.uuid4()
_SESSION_OWNER = uuid.uuid4()
_PROJECT_ID = uuid.uuid4()
_DOMAIN = "default"


def _make_deployment(
    *,
    desired: int = 3,
    deploying_revision_id: uuid.UUID | None = None,
) -> DeploymentInfo:
    return DeploymentInfo(
        id=_ENDPOINT_ID,
        metadata=DeploymentMetadata(
            name="test-deploy",
            domain=_DOMAIN,
            project=_PROJECT_ID,
            resource_group="default",
            created_user=_SESSION_OWNER,
            session_owner=_SESSION_OWNER,
            created_at=datetime.now(UTC),
            revision_history_limit=5,
        ),
        state=DeploymentState(
            lifecycle="DEPLOYING",  # type: ignore[arg-type]
            retry_count=0,
        ),
        replica_spec=ReplicaSpec(
            replica_count=desired,
            desired_replica_count=desired,
        ),
        network=DeploymentNetworkSpec(open_to_public=False),
        model_revisions=[],
        deploying_revision_id=deploying_revision_id or _DEPLOYING_REVISION_ID,
    )


def _make_route(
    *,
    revision_id: uuid.UUID | None = None,
    status: RouteStatus = RouteStatus.HEALTHY,
    traffic_status: RouteTrafficStatus = RouteTrafficStatus.ACTIVE,
    traffic_ratio: float = 1.0,
    status_updated_at: datetime | None = None,
) -> RouteInfo:
    if status_updated_at is None:
        status_updated_at = datetime.now(UTC)
    return RouteInfo(
        route_id=uuid.uuid4(),
        endpoint_id=_ENDPOINT_ID,
        session_id=None,
        status=status,
        traffic_ratio=traffic_ratio,
        created_at=datetime.now(UTC),
        revision_id=revision_id,
        traffic_status=traffic_status,
        status_updated_at=status_updated_at,
    )


def _blue_routes(
    count: int,
    *,
    status: RouteStatus = RouteStatus.HEALTHY,
) -> list[RouteInfo]:
    return [_make_route(revision_id=_OLD_REVISION_ID, status=status) for _ in range(count)]


def _green_routes(
    count: int,
    *,
    status: RouteStatus = RouteStatus.HEALTHY,
    traffic_status: RouteTrafficStatus = RouteTrafficStatus.INACTIVE,
    traffic_ratio: float = 0.0,
    status_updated_at: datetime | None = None,
) -> list[RouteInfo]:
    return [
        _make_route(
            revision_id=_DEPLOYING_REVISION_ID,
            status=status,
            traffic_status=traffic_status,
            traffic_ratio=traffic_ratio,
            status_updated_at=status_updated_at,
        )
        for _ in range(count)
    ]


def _default_spec(
    *,
    auto_promote: bool = False,
    promote_delay_seconds: int = 0,
) -> BlueGreenSpec:
    return BlueGreenSpec(
        auto_promote=auto_promote,
        promote_delay_seconds=promote_delay_seconds,
    )


# ── Test Classes ──


class TestNoGreenRoutes:
    """Step 2: No green routes → create them (INACTIVE)."""

    def test_creates_green_routes_when_none_exist(self) -> None:
        deployment = _make_deployment(desired=3)
        routes = _blue_routes(3)

        result = blue_green_evaluate(deployment, routes, _default_spec())

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed
        assert len(result.route_changes.scale_out_specs) == 3
        assert not result.route_changes.scale_in_route_ids
        assert not result.route_changes.promote_route_ids

    def test_creator_spec_has_inactive_traffic(self) -> None:
        deployment = _make_deployment(desired=2)
        routes = _blue_routes(2)

        result = blue_green_evaluate(deployment, routes, _default_spec())

        for creator in result.route_changes.scale_out_specs:
            assert isinstance(creator, Creator)
            spec = creator.spec
            assert isinstance(spec, RouteCreatorSpec)
            assert spec.traffic_status == RouteTrafficStatus.INACTIVE
            assert spec.traffic_ratio == 0.0
            assert spec.revision_id == _DEPLOYING_REVISION_ID

    def test_creates_routes_when_no_blue_either(self) -> None:
        deployment = _make_deployment(desired=2)

        result = blue_green_evaluate(deployment, [], _default_spec())

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert len(result.route_changes.scale_out_specs) == 2


class TestGreenProvisioning:
    """Step 3: Green PROVISIONING → wait."""

    def test_waits_when_green_provisioning(self) -> None:
        deployment = _make_deployment(desired=3)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.PROVISIONING)

        result = blue_green_evaluate(deployment, routes, _default_spec())

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed
        assert not result.route_changes.scale_out_specs
        assert not result.route_changes.scale_in_route_ids

    def test_waits_when_mixed_provisioning_and_healthy(self) -> None:
        deployment = _make_deployment(desired=3)
        routes = (
            _blue_routes(3)
            + _green_routes(2, status=RouteStatus.HEALTHY)
            + _green_routes(1, status=RouteStatus.PROVISIONING)
        )

        result = blue_green_evaluate(deployment, routes, _default_spec())

        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert not result.completed


class TestRollback:
    """Step 4: All green failed → rollback."""

    def test_rollback_when_all_green_failed(self) -> None:
        deployment = _make_deployment(desired=3)
        green_failed = _green_routes(3, status=RouteStatus.FAILED_TO_START)
        routes = _blue_routes(3) + green_failed

        result = blue_green_evaluate(deployment, routes, _default_spec())

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK
        assert not result.completed
        assert len(result.route_changes.scale_in_route_ids) == 3
        for gf in green_failed:
            assert gf.route_id in result.route_changes.scale_in_route_ids

    def test_rollback_with_terminated_green(self) -> None:
        deployment = _make_deployment(desired=2)
        routes = _blue_routes(2) + _green_routes(2, status=RouteStatus.TERMINATED)

        result = blue_green_evaluate(deployment, routes, _default_spec())

        assert result.sub_step == DeploymentSubStep.ROLLED_BACK
        assert len(result.route_changes.scale_in_route_ids) == 2

    def test_no_rollback_when_some_green_healthy(self) -> None:
        deployment = _make_deployment(desired=3)
        routes = (
            _blue_routes(3)
            + _green_routes(1, status=RouteStatus.HEALTHY)
            + _green_routes(2, status=RouteStatus.FAILED_TO_START)
        )

        result = blue_green_evaluate(deployment, routes, _default_spec())

        # Mixed: healthy < desired → PROGRESSING (step 5)
        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed


class TestHealthyLessThanDesired:
    """Step 5: Healthy green < desired → PROGRESSING."""

    def test_progressing_when_healthy_less_than_desired(self) -> None:
        deployment = _make_deployment(desired=5)
        routes = _blue_routes(5) + _green_routes(3, status=RouteStatus.HEALTHY)

        result = blue_green_evaluate(deployment, routes, _default_spec())

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed


class TestManualPromotion:
    """Step 6: All green healthy + auto_promote=False → manual wait."""

    def test_waits_for_manual_promotion(self) -> None:
        deployment = _make_deployment(desired=3)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.HEALTHY)
        spec = _default_spec(auto_promote=False)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed
        assert not result.route_changes.promote_route_ids
        assert not result.route_changes.scale_in_route_ids


class TestPromoteDelay:
    """Step 7: auto_promote=True + promote_delay_seconds."""

    def test_waits_when_delay_not_elapsed(self) -> None:
        deployment = _make_deployment(desired=3)
        recent = datetime.now(UTC) - timedelta(seconds=10)
        routes = _blue_routes(3) + _green_routes(
            3, status=RouteStatus.HEALTHY, status_updated_at=recent
        )
        spec = _default_spec(auto_promote=True, promote_delay_seconds=60)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed

    def test_promotes_when_delay_elapsed(self) -> None:
        deployment = _make_deployment(desired=3)
        past = datetime.now(UTC) - timedelta(seconds=120)
        green = _green_routes(3, status=RouteStatus.HEALTHY, status_updated_at=past)
        blue = _blue_routes(3)
        routes = blue + green
        spec = _default_spec(auto_promote=True, promote_delay_seconds=60)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert len(result.route_changes.promote_route_ids) == 3
        assert len(result.route_changes.scale_in_route_ids) == 3

    def test_waits_when_status_updated_at_is_none(self) -> None:
        deployment = _make_deployment(desired=2)
        green = _green_routes(2, status=RouteStatus.HEALTHY, status_updated_at=None)
        # Manually set status_updated_at to None
        for r in green:
            object.__setattr__(r, "status_updated_at", None)
        routes = _blue_routes(2) + green
        spec = _default_spec(auto_promote=True, promote_delay_seconds=30)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed


class TestAutoPromotion:
    """Step 8: auto_promote=True + delay=0 → immediate promotion."""

    def test_promotes_immediately_with_zero_delay(self) -> None:
        deployment = _make_deployment(desired=3)
        green = _green_routes(3, status=RouteStatus.HEALTHY)
        blue = _blue_routes(3)
        routes = blue + green
        spec = _default_spec(auto_promote=True, promote_delay_seconds=0)

        result = blue_green_evaluate(deployment, routes, spec)

        assert result.completed
        assert result.sub_step == DeploymentSubStep.PROGRESSING
        # Green route IDs promoted
        assert len(result.route_changes.promote_route_ids) == 3
        for g in green:
            assert g.route_id in result.route_changes.promote_route_ids
        # Blue route IDs scaled in
        assert len(result.route_changes.scale_in_route_ids) == 3
        for b in blue:
            assert b.route_id in result.route_changes.scale_in_route_ids

    def test_no_blue_to_terminate(self) -> None:
        deployment = _make_deployment(desired=2)
        green = _green_routes(2, status=RouteStatus.HEALTHY)
        spec = _default_spec(auto_promote=True)

        result = blue_green_evaluate(deployment, green, spec)

        assert result.completed
        assert len(result.route_changes.promote_route_ids) == 2
        assert len(result.route_changes.scale_in_route_ids) == 0


class TestSingleReplica:
    """Edge case: desired=1."""

    def test_single_replica_full_cycle(self) -> None:
        deployment = _make_deployment(desired=1)
        green = _green_routes(1, status=RouteStatus.HEALTHY)
        blue = _blue_routes(1)
        spec = _default_spec(auto_promote=True)

        result = blue_green_evaluate(deployment, blue + green, spec)

        assert result.completed
        assert len(result.route_changes.promote_route_ids) == 1
        assert len(result.route_changes.scale_in_route_ids) == 1


class TestLargeReplicaCount:
    """Edge case: desired=10."""

    def test_creates_correct_number_of_green_routes(self) -> None:
        deployment = _make_deployment(desired=10)
        routes = _blue_routes(10)

        result = blue_green_evaluate(deployment, routes, _default_spec())

        assert len(result.route_changes.scale_out_specs) == 10


class TestBlueRouteStatuses:
    """Only active blue routes are terminated during promotion."""

    def test_only_active_blue_terminated(self) -> None:
        deployment = _make_deployment(desired=2)
        blue_active = _blue_routes(2, status=RouteStatus.HEALTHY)
        blue_inactive = [
            _make_route(revision_id=_OLD_REVISION_ID, status=RouteStatus.TERMINATED),
        ]
        green = _green_routes(2, status=RouteStatus.HEALTHY)
        spec = _default_spec(auto_promote=True)

        result = blue_green_evaluate(deployment, blue_active + blue_inactive + green, spec)

        assert result.completed
        # Only active blue routes are terminated
        assert len(result.route_changes.scale_in_route_ids) == 2
        for b in blue_active:
            assert b.route_id in result.route_changes.scale_in_route_ids
        for b in blue_inactive:
            assert b.route_id not in result.route_changes.scale_in_route_ids


class TestCreatorSpecFields:
    """Verify RouteCreatorSpec fields for green routes."""

    def test_creator_fields(self) -> None:
        deployment = _make_deployment(desired=1)

        result = blue_green_evaluate(deployment, [], _default_spec())

        wrapper = result.route_changes.scale_out_specs[0]
        assert isinstance(wrapper, Creator)
        spec = wrapper.spec
        assert isinstance(spec, RouteCreatorSpec)
        assert spec.endpoint_id == _ENDPOINT_ID
        assert spec.session_owner_id == _SESSION_OWNER
        assert spec.domain == _DOMAIN
        assert spec.project_id == _PROJECT_ID
        assert spec.traffic_ratio == 0.0
        assert spec.traffic_status == RouteTrafficStatus.INACTIVE
        assert spec.revision_id == _DEPLOYING_REVISION_ID


class TestMixedGreenStatuses:
    """Mixed green routes: some healthy, some failed, no provisioning."""

    def test_mixed_healthy_and_failed_progresses(self) -> None:
        deployment = _make_deployment(desired=4)
        routes = (
            _blue_routes(4)
            + _green_routes(2, status=RouteStatus.HEALTHY)
            + _green_routes(2, status=RouteStatus.FAILED_TO_START)
        )
        spec = _default_spec(auto_promote=True)

        result = blue_green_evaluate(deployment, routes, spec)

        # 2 healthy < 4 desired → PROGRESSING
        assert result.sub_step == DeploymentSubStep.PROGRESSING
        assert not result.completed


class TestDifferentEndpoints:
    """Routes for different endpoints should still classify correctly."""

    def test_different_deploying_revision(self) -> None:
        other_revision = uuid.uuid4()
        deployment = _make_deployment(desired=2, deploying_revision_id=other_revision)
        # Routes with a different revision_id are classified as blue
        routes = [
            _make_route(revision_id=_DEPLOYING_REVISION_ID, status=RouteStatus.HEALTHY),
            _make_route(revision_id=_DEPLOYING_REVISION_ID, status=RouteStatus.HEALTHY),
        ]

        result = blue_green_evaluate(deployment, routes, _default_spec())

        # These are classified as blue (different revision), so no green → create
        assert result.sub_step == DeploymentSubStep.PROVISIONING
        assert len(result.route_changes.scale_out_specs) == 2


class TestAtomicPromotion:
    """Promotion is atomic: all green promoted + all blue terminated in one cycle."""

    def test_atomic_promotion(self) -> None:
        deployment = _make_deployment(desired=5)
        green = _green_routes(5, status=RouteStatus.HEALTHY)
        blue = _blue_routes(5)
        spec = _default_spec(auto_promote=True)

        result = blue_green_evaluate(deployment, blue + green, spec)

        assert result.completed
        green_ids = {g.route_id for g in green}
        blue_ids = {b.route_id for b in blue}
        assert set(result.route_changes.promote_route_ids) == green_ids
        assert set(result.route_changes.scale_in_route_ids) == blue_ids


class TestNoScaleOutDuringWait:
    """No new routes created when waiting for green to become healthy."""

    def test_no_scale_out_during_provisioning_wait(self) -> None:
        deployment = _make_deployment(desired=3)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.PROVISIONING)

        result = blue_green_evaluate(deployment, routes, _default_spec())

        assert not result.route_changes.scale_out_specs

    def test_no_scale_out_during_progressing(self) -> None:
        deployment = _make_deployment(desired=3)
        routes = _blue_routes(3) + _green_routes(3, status=RouteStatus.HEALTHY)
        spec = _default_spec(auto_promote=False)

        result = blue_green_evaluate(deployment, routes, spec)

        assert not result.route_changes.scale_out_specs
