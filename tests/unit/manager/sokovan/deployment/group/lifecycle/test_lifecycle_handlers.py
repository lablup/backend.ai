import uuid
from datetime import UTC, datetime
from uuid import UUID

from ai.backend.common.dto.manager.v2.deployment.types import IntOrPercent
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerOptions,
    ReplicaGroupLifecycle,
    ReplicaGroupRolloutSpec,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.data.reconciler.types import HandlerOutcome
from ai.backend.manager.sokovan.deployment.group.lifecycle.handlers.autoscale import (
    GroupAutoscaleHandler,
)
from ai.backend.manager.sokovan.deployment.group.lifecycle.handlers.draining import (
    GroupDrainingHandler,
)
from ai.backend.manager.sokovan.deployment.group.lifecycle.handlers.rolling import (
    GroupRollingHandler,
)
from ai.backend.manager.sokovan.deployment.group.lifecycle.types import (
    GroupAutoscaleReconcileInfo,
    GroupLifecycleDecision,
    GroupLifecycleReconcileInfo,
)
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.views.replica_group import (
    ReplicaGroupAutoscaleReconcileView,
    ReplicaGroupLifecycleReconcileView,
)


def _view(
    *,
    lifecycle: ReplicaGroupLifecycle,
    goal: int = 4,
    desired_current: int = 4,
    desired_target: int = 0,
    current_revision_id: DeploymentRevisionID | None = None,
    target_revision_id: DeploymentRevisionID | None = None,
) -> ReplicaGroupLifecycleReconcileView:
    # surge 50%, unavailable 0% baseline.
    rollout = ReplicaGroupRolloutSpec(
        max_surge=IntOrPercent(percent=0.5),
        max_unavailable=IntOrPercent(percent=0.0),
    )
    return ReplicaGroupLifecycleReconcileView(
        group_id=ReplicaGroupID(uuid.uuid4()),
        deployment_id=DeploymentID(uuid.uuid4()),
        current_revision_id=current_revision_id,
        target_revision_id=target_revision_id,
        lifecycle=lifecycle,
        scaling_status=ReplicaGroupScalingStatus.STABLE,
        desired_current_replica_count=desired_current,
        desired_target_replica_count=desired_target,
        deployment_desired_replica_count=goal,
        rollout=rollout,
        last_history=None,
        handler_options=DeploymentHandlerOptions(),
    )


def _info(view: ReplicaGroupLifecycleReconcileView) -> GroupLifecycleReconcileInfo:
    return GroupLifecycleReconcileInfo(views=[view], current_time=datetime(2026, 1, 1, tzinfo=UTC))


def _autoscale_view(
    *,
    goal: int = 4,
    desired_current: int = 4,
    current_live: int = 4,
    current_serving: int = 4,
    current_revision_id: DeploymentRevisionID | None = None,
) -> ReplicaGroupAutoscaleReconcileView:
    return ReplicaGroupAutoscaleReconcileView(
        group_id=ReplicaGroupID(uuid.uuid4()),
        deployment_id=DeploymentID(uuid.uuid4()),
        current_revision_id=current_revision_id,
        lifecycle=ReplicaGroupLifecycle.STABLE,
        scaling_status=ReplicaGroupScalingStatus.STABLE,
        desired_current_replica_count=desired_current,
        deployment_desired_replica_count=goal,
        current_live_replica_count=current_live,
        current_serving_replica_count=current_serving,
        last_history=None,
        handler_options=DeploymentHandlerOptions(),
    )


async def _autoscale_decision(view: ReplicaGroupAutoscaleReconcileView) -> GroupLifecycleDecision:
    info = GroupAutoscaleReconcileInfo(views=[view], current_time=datetime(2026, 1, 1, tzinfo=UTC))
    with RecorderContext[UUID].scope("group_autoscale", [view.group_id]):
        result = await GroupAutoscaleHandler().execute(info)
    return result.lifecycle_decisions[0]


async def test_autoscale_steady_state_converged() -> None:
    view = _autoscale_view(current_revision_id=DeploymentRevisionID(uuid.uuid4()))
    decision = await _autoscale_decision(view)
    assert decision.outcome() is HandlerOutcome.SUCCESS
    assert decision.next_desired_current_replica_count == 4
    assert decision.next_desired_target_replica_count == 0


async def test_autoscale_rearms_scaling_when_live_routes_drop() -> None:
    # A route died: desired still matches the goal but only 3 of 4 are actually live.
    view = _autoscale_view(
        current_live=3,
        current_serving=3,
        current_revision_id=DeploymentRevisionID(uuid.uuid4()),
    )
    decision = await _autoscale_decision(view)
    assert decision.outcome() is HandlerOutcome.FAILURE
    assert decision.next_desired_current_replica_count == 4


async def test_autoscale_rearms_scaling_when_serving_short_of_live() -> None:
    # A leftover PROVISIONING route counts as live but not serving yet.
    view = _autoscale_view(
        current_live=4,
        current_serving=3,
        current_revision_id=DeploymentRevisionID(uuid.uuid4()),
    )
    decision = await _autoscale_decision(view)
    assert decision.outcome() is HandlerOutcome.FAILURE


async def test_autoscale_rearms_scaling_when_goal_changes() -> None:
    # The autoscaling rule moved the deployment goal; desired counts lag behind.
    view = _autoscale_view(
        goal=6,
        current_revision_id=DeploymentRevisionID(uuid.uuid4()),
    )
    decision = await _autoscale_decision(view)
    assert decision.outcome() is HandlerOutcome.FAILURE
    assert decision.next_desired_current_replica_count == 6


async def test_autoscale_skips_drift_check_without_current_revision() -> None:
    # No current revision means the scaling reconcile has nothing to fill; do not re-arm.
    view = _autoscale_view(current_live=0, current_serving=0, current_revision_id=None)
    decision = await _autoscale_decision(view)
    assert decision.outcome() is HandlerOutcome.SUCCESS


async def test_rolling_steps_target_up_and_current_down() -> None:
    # goal 4, surge 50% (=2), unavailable 0; 2 of the new revision are already desired/up.
    # A current revision exists, so the availability floor keeps current routes alive.
    view = _view(
        lifecycle=ReplicaGroupLifecycle.ROLLING,
        desired_current=4,
        desired_target=2,
        current_revision_id=DeploymentRevisionID(uuid.uuid4()),
    )
    info = _info(view)
    with RecorderContext[UUID].scope("group_rolling", [view.group_id]):
        result = await GroupRollingHandler().execute(info)
    decision = result.lifecycle_decisions[0]
    assert decision.next_desired_target_replica_count == 4  # min(4, 2 + 2)
    assert decision.next_desired_current_replica_count == 2  # max(0, (4 - 0) - 2)
    assert decision.outcome() is HandlerOutcome.FAILURE


async def test_rolling_initial_deploy_keeps_current_at_zero() -> None:
    # Initial deploy: no current revision to keep serving, so current stays at zero
    # while the target ramps up (no availability floor to maintain).
    view = _view(
        lifecycle=ReplicaGroupLifecycle.ROLLING,
        desired_current=0,
        desired_target=2,
        current_revision_id=None,
    )
    with RecorderContext[UUID].scope("group_rolling", [view.group_id]):
        result = await GroupRollingHandler().execute(_info(view))
    decision = result.lifecycle_decisions[0]
    assert decision.next_desired_target_replica_count == 4  # min(4, 2 + 2)
    assert decision.next_desired_current_replica_count == 0  # no current revision → no floor
    assert decision.outcome() is HandlerOutcome.FAILURE


async def test_rolling_converges_when_target_full_and_current_drained() -> None:
    revision = DeploymentRevisionID(uuid.uuid4())
    view = _view(
        lifecycle=ReplicaGroupLifecycle.ROLLING,
        desired_current=0,
        desired_target=4,
        target_revision_id=revision,
    )
    with RecorderContext[UUID].scope("group_rolling", [view.group_id]):
        result = await GroupRollingHandler().execute(_info(view))
    decision = result.lifecycle_decisions[0]
    assert decision.outcome() is HandlerOutcome.SUCCESS
    # The target revision is promoted to current and the counts flip onto it.
    assert decision.next_desired_current_replica_count == 4
    assert decision.next_desired_target_replica_count == 0
    assert decision.next_current_revision_id.optional_value() == revision
    assert decision.next_target_revision_id.is_nullify()


async def test_draining_in_progress_sets_zero_and_keeps_scaling() -> None:
    view = _view(
        lifecycle=ReplicaGroupLifecycle.DRAINING,
        desired_current=2,
        desired_target=0,
        current_revision_id=DeploymentRevisionID(uuid.uuid4()),
    )
    with RecorderContext[UUID].scope("group_draining", [view.group_id]):
        result = await GroupDrainingHandler().execute(_info(view))
    decision = result.lifecycle_decisions[0]
    assert decision.next_desired_current_replica_count == 0
    assert decision.next_desired_target_replica_count == 0
    assert decision.outcome() is HandlerOutcome.FAILURE
    # Still draining: revision pointers are left untouched until the group is fully retired.
    assert not decision.next_current_revision_id.is_nullify()
    assert not decision.next_target_revision_id.is_nullify()


async def test_draining_completes_when_desired_is_zero() -> None:
    view = _view(
        lifecycle=ReplicaGroupLifecycle.DRAINING,
        desired_current=0,
        desired_target=0,
        current_revision_id=DeploymentRevisionID(uuid.uuid4()),
    )
    with RecorderContext[UUID].scope("group_draining", [view.group_id]):
        result = await GroupDrainingHandler().execute(_info(view))
    decision = result.lifecycle_decisions[0]
    assert decision.outcome() is HandlerOutcome.SUCCESS
    # Retired group: its revision pointers are cleared with the DRAINED transition.
    assert decision.next_current_revision_id.is_nullify()
    assert decision.next_target_revision_id.is_nullify()
