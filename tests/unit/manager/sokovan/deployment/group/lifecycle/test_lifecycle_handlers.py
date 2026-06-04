import uuid
from datetime import UTC, datetime
from uuid import UUID

from ai.backend.common.dto.manager.v2.deployment.types import IntOrPercent
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerOptions,
    ReplicaGroupLifecycle,
    ReplicaGroupRolloutSpec,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.data.reconciler.types import HandlerOutcome
from ai.backend.manager.sokovan.deployment.group.lifecycle.handlers.draining import (
    GroupDrainingHandler,
)
from ai.backend.manager.sokovan.deployment.group.lifecycle.handlers.rolling import (
    GroupRollingHandler,
)
from ai.backend.manager.sokovan.deployment.group.lifecycle.types import (
    GroupLifecycleReconcileInfo,
)
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.views.replica_group import ReplicaGroupLifecycleReconcileView


def _view(
    *,
    lifecycle: ReplicaGroupLifecycle,
    goal: int = 4,
    desired_current: int = 4,
    desired_target: int = 0,
) -> ReplicaGroupLifecycleReconcileView:
    # surge 50%, unavailable 0% baseline.
    rollout = ReplicaGroupRolloutSpec(
        max_surge=IntOrPercent(percent=0.5),
        max_unavailable=IntOrPercent(percent=0.0),
    )
    return ReplicaGroupLifecycleReconcileView(
        group_id=ReplicaGroupID(uuid.uuid4()),
        deployment_id=DeploymentID(uuid.uuid4()),
        current_revision_id=None,
        target_revision_id=None,
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


async def test_rolling_steps_target_up_and_current_down() -> None:
    # goal 4, surge 50% (=2), unavailable 0; 2 of the new revision are already desired/up.
    view = _view(lifecycle=ReplicaGroupLifecycle.ROLLING, desired_current=4, desired_target=2)
    info = _info(view)
    with RecorderContext[UUID].scope("group_rolling", [view.group_id]):
        result = await GroupRollingHandler().execute(info)
    decision = result.lifecycle_decisions[0]
    assert decision.next_desired_target_replica_count == 4  # min(4, 2 + 2)
    assert decision.next_desired_current_replica_count == 2  # max(0, (4 - 0) - 2)
    assert decision.outcome() is HandlerOutcome.FAILURE


async def test_rolling_converges_when_target_full_and_current_drained() -> None:
    view = _view(lifecycle=ReplicaGroupLifecycle.ROLLING, desired_current=0, desired_target=4)
    with RecorderContext[UUID].scope("group_rolling", [view.group_id]):
        result = await GroupRollingHandler().execute(_info(view))
    decision = result.lifecycle_decisions[0]
    assert decision.outcome() is HandlerOutcome.SUCCESS
    assert decision.next_desired_current_replica_count == 0
    assert decision.next_desired_target_replica_count == 4


async def test_draining_in_progress_sets_zero_and_keeps_scaling() -> None:
    view = _view(lifecycle=ReplicaGroupLifecycle.DRAINING, desired_current=2, desired_target=0)
    with RecorderContext[UUID].scope("group_draining", [view.group_id]):
        result = await GroupDrainingHandler().execute(_info(view))
    decision = result.lifecycle_decisions[0]
    assert decision.next_desired_current_replica_count == 0
    assert decision.next_desired_target_replica_count == 0
    assert decision.outcome() is HandlerOutcome.FAILURE


async def test_draining_completes_when_desired_is_zero() -> None:
    view = _view(lifecycle=ReplicaGroupLifecycle.DRAINING, desired_current=0, desired_target=0)
    with RecorderContext[UUID].scope("group_draining", [view.group_id]):
        result = await GroupDrainingHandler().execute(_info(view))
    decision = result.lifecycle_decisions[0]
    assert decision.outcome() is HandlerOutcome.SUCCESS
