"""Group autoscale handler: keep a STABLE serving group's current-revision replica count synced
to the deployment's desired count (steady-state scaling). The autoscaling rule only updates the
deployment desired count; this reflects it onto the serving group's desired_current."""

from __future__ import annotations

from typing import override
from uuid import UUID

from ai.backend.manager.data.reconciler.types import HandlerOutcome
from ai.backend.manager.sokovan.deployment.group.lifecycle.types import (
    GroupLifecycleDecision,
    GroupLifecycleReconcileInfo,
    GroupLifecycleReconcileResult,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerHandler
from ai.backend.manager.sokovan.recorder.context import RecorderContext


class GroupAutoscaleHandler(
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
            with recorder.phase("group_autoscale"):
                with recorder.step("evaluate"):
                    goal = view.deployment_desired_replica_count
                    if view.desired_current_replica_count == goal:
                        outcome = HandlerOutcome.SUCCESS
                        message = "current revision at desired count"
                    else:
                        # Re-arms scaling so the scaling reconcile fills routes to the new count.
                        outcome = HandlerOutcome.FAILURE
                        message = "scaling current revision toward desired count"
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
