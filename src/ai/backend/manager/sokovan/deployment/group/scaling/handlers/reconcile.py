"""Group scaling reconcile handler: decide route create/drain counts and per-group result."""

from __future__ import annotations

from typing import override
from uuid import UUID

from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.repositories.replica_group.types import (
    GroupRouteCreateInstruction,
    GroupRouteDrainInstruction,
)
from ai.backend.manager.sokovan.deployment.group.scaling.types import (
    GroupScalingDecision,
    GroupScalingReconcileInfo,
    GroupScalingReconcileResult,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerHandler
from ai.backend.manager.sokovan.recorder.context import RecorderContext


class GroupScalingReconcileHandler(
    ReconcilerHandler[GroupScalingReconcileInfo, GroupScalingReconcileResult]
):
    @override
    async def execute(
        self, reconcile_info: GroupScalingReconcileInfo
    ) -> GroupScalingReconcileResult:
        create_instructions: list[GroupRouteCreateInstruction] = []
        drain_instructions: list[GroupRouteDrainInstruction] = []
        decisions: list[GroupScalingDecision] = []
        pool = RecorderContext[UUID].current_pool()

        for view in reconcile_info.views:
            recorder = pool.recorder(view.group_id)
            with recorder.phase("scaling_reconcile"):
                with recorder.step("evaluate"):
                    if view.current_revision_id is not None:
                        deficit = (
                            view.desired_current_replica_count - view.current_live_replica_count
                        )
                        if deficit > 0:
                            create_instructions.append(
                                GroupRouteCreateInstruction(
                                    replica_group_id=view.group_id,
                                    deployment_id=view.deployment_id,
                                    revision_id=view.current_revision_id,
                                    count=deficit,
                                )
                            )
                        elif deficit < 0:
                            drain_instructions.append(
                                GroupRouteDrainInstruction(
                                    replica_group_id=view.group_id,
                                    revision_id=view.current_revision_id,
                                    count=-deficit,
                                )
                            )
                    if view.target_revision_id is not None:
                        deficit = view.desired_target_replica_count - view.target_live_replica_count
                        if deficit > 0:
                            create_instructions.append(
                                GroupRouteCreateInstruction(
                                    replica_group_id=view.group_id,
                                    deployment_id=view.deployment_id,
                                    revision_id=view.target_revision_id,
                                    count=deficit,
                                )
                            )
                        elif deficit < 0:
                            drain_instructions.append(
                                GroupRouteDrainInstruction(
                                    replica_group_id=view.group_id,
                                    revision_id=view.target_revision_id,
                                    count=-deficit,
                                )
                            )
                    current_matched = (
                        view.current_live_replica_count == view.desired_current_replica_count
                        and view.current_serving_replica_count == view.desired_current_replica_count
                    )
                    target_matched = (
                        view.target_live_replica_count == view.desired_target_replica_count
                        and view.target_serving_replica_count == view.desired_target_replica_count
                    )
                    # Reconciled to desired -> SUCCESS; still converging -> retry next tick.
                    if current_matched and target_matched:
                        result = SchedulingResult.SUCCESS
                        message = "replica counts match desired"
                    else:
                        result = SchedulingResult.NEED_RETRY
                        message = "reconciling replica counts toward desired"
            decisions.append(
                GroupScalingDecision(
                    replica_group_id=view.group_id,
                    deployment_id=view.deployment_id,
                    result=result,
                    message=message,
                )
            )

        return GroupScalingReconcileResult(
            create_instructions=create_instructions,
            drain_instructions=drain_instructions,
            decisions=decisions,
            processed=len(reconcile_info.views),
            failed=0,
        )

    @override
    async def post_process(self, result: GroupScalingReconcileResult) -> None:
        pass
