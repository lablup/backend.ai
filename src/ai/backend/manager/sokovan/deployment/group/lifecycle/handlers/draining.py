"""Group draining handler: drive the group's desired counts to zero; once no routes
remain, the group is fully retired (DRAINED)."""

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


class GroupDrainingHandler(
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
            with recorder.phase("group_draining"):
                with recorder.step("evaluate"):
                    # Triggered at scaling STABLE, so desired 0 means the routes are gone.
                    drained = (
                        view.desired_current_replica_count == 0
                        and view.desired_target_replica_count == 0
                    )
                    if drained:
                        outcome = HandlerOutcome.SUCCESS
                        message = "drain complete; no routes remain"
                    else:
                        outcome = HandlerOutcome.FAILURE
                        message = "draining routes to zero"
            decisions.append(
                GroupLifecycleDecision(
                    replica_group_id=view.group_id,
                    deployment_id=view.deployment_id,
                    handler_outcome=outcome,
                    message=message,
                    from_lifecycle=view.lifecycle,
                    next_desired_current_replica_count=0,
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
