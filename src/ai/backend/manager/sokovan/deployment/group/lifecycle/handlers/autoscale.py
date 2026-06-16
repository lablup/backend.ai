"""Group autoscale handler: keep a STABLE serving group converged on the deployment's desired
count (steady-state keeper). It syncs the group's desired_current to the deployment goal AND
checks the actual live/serving counts, so a route death (or any drift from desired) re-arms
scaling — this stage is the only trigger that moves a STABLE group back to SCALING."""

from __future__ import annotations

from typing import override
from uuid import UUID

from ai.backend.manager.data.reconciler.types import HandlerOutcome
from ai.backend.manager.sokovan.deployment.group.lifecycle.types import (
    GroupAutoscaleReconcileInfo,
    GroupLifecycleDecision,
    GroupLifecycleReconcileResult,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerHandler
from ai.backend.manager.sokovan.recorder.context import RecorderContext


class GroupAutoscaleHandler(
    ReconcilerHandler[GroupAutoscaleReconcileInfo, GroupLifecycleReconcileResult]
):
    @override
    async def execute(
        self, reconcile_info: GroupAutoscaleReconcileInfo
    ) -> GroupLifecycleReconcileResult:
        decisions: list[GroupLifecycleDecision] = []
        pool = RecorderContext[UUID].current_pool()

        for view in reconcile_info.views:
            recorder = pool.recorder(view.group_id)
            with recorder.phase("group_autoscale"):
                with recorder.step("evaluate"):
                    goal = view.deployment_desired_replica_count
                    # Same convergence criteria as the scaling reconcile; a group with no
                    # current revision has nothing the scaling reconcile could fill.
                    converged = view.current_revision_id is None or (
                        view.current_live_replica_count == goal
                        and view.current_serving_replica_count == goal
                    )
                    # FAILURE re-arms scaling so the scaling reconcile fills/drains routes.
                    if view.desired_current_replica_count != goal:
                        outcome = HandlerOutcome.FAILURE
                        message = "scaling current revision toward desired count"
                    elif not converged:
                        outcome = HandlerOutcome.FAILURE
                        message = "live replicas drifted from desired; re-arming scaling"
                    else:
                        outcome = HandlerOutcome.SUCCESS
                        message = "current revision at desired count"
            decisions.append(
                GroupLifecycleDecision(
                    replica_group_id=view.group_id,
                    deployment_id=view.deployment_id,
                    handler_outcome=outcome,
                    message=message,
                    from_lifecycle=view.lifecycle,
                    next_desired_current_replica_count=goal,
                    next_desired_target_replica_count=0,
                    prior_history=view.last_history,
                    handler_options=view.handler_options,
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
