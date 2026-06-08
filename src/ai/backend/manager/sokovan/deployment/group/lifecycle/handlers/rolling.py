"""Group rolling handler: step desired counts toward the goal (bounded by the rollout
surge/unavailable) until the target revision is fully up and the old one is drained."""

from __future__ import annotations

from typing import override
from uuid import UUID

from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.manager.data.reconciler.types import HandlerOutcome
from ai.backend.manager.sokovan.deployment.group.lifecycle.types import (
    GroupLifecycleDecision,
    GroupLifecycleReconcileInfo,
    GroupLifecycleReconcileResult,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerHandler
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.types import TriState


class GroupRollingHandler(
    ReconcilerHandler[GroupLifecycleReconcileInfo, GroupLifecycleReconcileResult]
):
    @override
    async def execute(
        self, reconcile_info: GroupLifecycleReconcileInfo
    ) -> GroupLifecycleReconcileResult:
        decisions: list[GroupLifecycleDecision] = []
        pool = RecorderContext[UUID].current_pool()

        for view in reconcile_info.views:
            recorder = pool.recorder(view.group_id)
            with recorder.phase("group_rolling"):
                with recorder.step("evaluate"):
                    # Triggered at scaling STABLE, so the desired counts are already realized.
                    goal = view.deployment_desired_replica_count
                    target_desired = view.desired_target_replica_count
                    next_current_revision: TriState[DeploymentRevisionID] = TriState.nop()
                    next_target_revision: TriState[DeploymentRevisionID] = TriState.nop()
                    # Converged: target reached the goal and the old revision is fully drained.
                    # Promote the target revision to current and flip the counts onto it.
                    if target_desired == goal and view.desired_current_replica_count == 0:
                        outcome = HandlerOutcome.SUCCESS
                        message = "rollout complete; target revision at desired"
                        next_current = goal
                        next_target = 0
                        if view.target_revision_id is not None:
                            next_current_revision = TriState.update(view.target_revision_id)
                            next_target_revision = TriState.nullify()
                    else:
                        surge = view.rollout.resolve_max_surge(goal)
                        unavailable = view.rollout.resolve_max_unavailable(goal)
                        # Grow target by surge above what is up; keep the availability floor on current.
                        next_target = min(goal, target_desired + surge)
                        next_current = max(0, (goal - unavailable) - target_desired)
                        outcome = HandlerOutcome.FAILURE
                        message = "rolling out target revision toward desired"
            decisions.append(
                GroupLifecycleDecision(
                    replica_group_id=view.group_id,
                    deployment_id=view.deployment_id,
                    handler_outcome=outcome,
                    message=message,
                    from_lifecycle=view.lifecycle,
                    next_desired_current_replica_count=next_current,
                    next_desired_target_replica_count=next_target,
                    prior_history=view.last_history,
                    handler_options=view.handler_options,
                    next_current_revision_id=next_current_revision,
                    next_target_revision_id=next_target_revision,
                )
            )

        return GroupLifecycleReconcileResult(
            lifecycle_decisions=decisions,
            processed=len(reconcile_info.views),
            failed=0,
        )

    @override
    async def post_process(self, result: GroupLifecycleReconcileResult) -> None:
        pass
