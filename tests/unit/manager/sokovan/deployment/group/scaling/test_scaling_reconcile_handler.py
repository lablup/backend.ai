import uuid
from datetime import UTC, datetime
from uuid import UUID

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerOptions,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.data.reconciler.types import HandlerOutcome
from ai.backend.manager.sokovan.deployment.group.scaling.handlers.reconcile import (
    GroupScalingReconcileHandler,
)
from ai.backend.manager.sokovan.deployment.group.scaling.types import (
    GroupScalingDecision,
    GroupScalingReconcileInfo,
    GroupScalingReconcileResult,
)
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.views.replica_group import ReplicaGroupScalingReconcileView


def _scaling_view(
    *,
    current_revision_id: DeploymentRevisionID | None = None,
    target_revision_id: DeploymentRevisionID | None = None,
    desired_current: int = 4,
    desired_target: int = 0,
    current_live: int = 4,
    current_serving: int = 4,
    target_live: int = 0,
    target_serving: int = 0,
) -> ReplicaGroupScalingReconcileView:
    return ReplicaGroupScalingReconcileView(
        group_id=ReplicaGroupID(uuid.uuid4()),
        deployment_id=DeploymentID(uuid.uuid4()),
        current_revision_id=current_revision_id,
        target_revision_id=target_revision_id,
        scaling_status=ReplicaGroupScalingStatus.SCALING,
        desired_current_replica_count=desired_current,
        desired_target_replica_count=desired_target,
        current_live_replica_count=current_live,
        current_serving_replica_count=current_serving,
        target_live_replica_count=target_live,
        target_serving_replica_count=target_serving,
        last_history=None,
        handler_options=DeploymentHandlerOptions(),
    )


async def _execute(view: ReplicaGroupScalingReconcileView) -> GroupScalingReconcileResult:
    info = GroupScalingReconcileInfo(views=[view], current_time=datetime(2026, 1, 1, tzinfo=UTC))
    with RecorderContext[UUID].scope("scaling_reconcile", [view.group_id]):
        return await GroupScalingReconcileHandler().execute(info)


async def _decision(view: ReplicaGroupScalingReconcileView) -> GroupScalingDecision:
    return (await _execute(view)).scaling_decisions[0]


async def test_steady_state_converges_on_count_despite_short_serving() -> None:
    # No target revision (steady state): count is met (live == desired) but serving lags
    # because some routes are stuck PENDING. Must converge so the group reaches STABLE.
    view = _scaling_view(
        current_revision_id=DeploymentRevisionID(uuid.uuid4()),
        target_revision_id=None,
        desired_current=6,
        current_live=6,
        current_serving=3,
    )
    decision = await _decision(view)
    assert decision.outcome() is HandlerOutcome.SUCCESS


async def test_steady_state_not_converged_when_count_short() -> None:
    view = _scaling_view(
        current_revision_id=DeploymentRevisionID(uuid.uuid4()),
        target_revision_id=None,
        desired_current=6,
        current_live=4,
        current_serving=4,
    )
    decision = await _decision(view)
    assert decision.outcome() is HandlerOutcome.FAILURE


async def test_steady_state_scale_down_drains_excess() -> None:
    # Goal dropped to 1 while 6 routes (3 serving + 3 PENDING) exist: drain the 5 surplus.
    view = _scaling_view(
        current_revision_id=DeploymentRevisionID(uuid.uuid4()),
        target_revision_id=None,
        desired_current=1,
        current_live=6,
        current_serving=3,
    )
    result = await _execute(view)
    assert len(result.drain_instructions) == 1
    assert result.drain_instructions[0].count == 5


async def test_rollout_still_requires_serving() -> None:
    # A target revision is in flight (rollout): the current side must reach serving, not just
    # count, so the rolling step waits before draining the old revision (no-downtime).
    view = _scaling_view(
        current_revision_id=DeploymentRevisionID(uuid.uuid4()),
        target_revision_id=DeploymentRevisionID(uuid.uuid4()),
        desired_current=3,
        desired_target=3,
        current_live=3,
        current_serving=2,
        target_live=3,
        target_serving=3,
    )
    decision = await _decision(view)
    assert decision.outcome() is HandlerOutcome.FAILURE


async def test_rollout_converges_when_both_sides_serving() -> None:
    view = _scaling_view(
        current_revision_id=DeploymentRevisionID(uuid.uuid4()),
        target_revision_id=DeploymentRevisionID(uuid.uuid4()),
        desired_current=2,
        desired_target=2,
        current_live=2,
        current_serving=2,
        target_live=2,
        target_serving=2,
    )
    decision = await _decision(view)
    assert decision.outcome() is HandlerOutcome.SUCCESS
