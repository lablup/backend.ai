"""Group scaling reconcile handler: decide route create/drain counts and per-group result."""

from __future__ import annotations

from typing import override
from uuid import UUID

from ai.backend.manager.data.reconciler.types import HandlerOutcome
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
        scaling_decisions: list[GroupScalingDecision] = []
        pool = RecorderContext[UUID].current_pool()

        for view in reconcile_info.views:
            recorder = pool.recorder(view.group_id)
            with recorder.phase("scaling_reconcile"):
                with recorder.step("evaluate"):
                    if view.current_revision_id is not None:
                        deficit = (
                            view.desired_current_replica_count - view.current_live_replica_count
                        )
                        if deficit > 0 and view.target_revision_id is None:
                            # Steady-state self-heal only. During a rollout the current
                            # revision is never refilled: a replica that died (agent
                            # failure or user termination — indistinguishable) stays
                            # gone and its capacity moves to the target revision as the
                            # rolling step advances. Refilling would re-grab freed
                            # resources and starve the target side (capacity livelock);
                            # a target revision that cannot come up is covered by the
                            # rollout timeout + rollback path instead.
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
                    # The current revision converges on count alone — serving is never
                    # required of it. Replicas that cannot be scheduled stay PENDING (live
                    # but not serving); requiring serving here would livelock the rollout
                    # when old-revision replicas can never become serving. The no-downtime
                    # invariant (new replicas serve before the old side drains) is enforced
                    # by target_matched below, which does require serving.
                    if view.target_revision_id is None:
                        # Steady state: exact count (a deficit is being refilled).
                        current_matched = (
                            view.current_live_replica_count == view.desired_current_replica_count
                        )
                    else:
                        # Rollout in flight: one-sided. The current side is drain-only
                        # (dead replicas are not refilled), so a shortfall is a final
                        # state and must not hold the group out of STABLE — only a
                        # surplus still waiting to drain does.
                        current_matched = (
                            view.current_live_replica_count <= view.desired_current_replica_count
                        )
                    target_matched = (
                        view.target_live_replica_count == view.desired_target_replica_count
                        and view.target_serving_replica_count == view.desired_target_replica_count
                    )
                    # Converged -> SUCCESS; still converging -> FAILURE (the coordinator
                    # turns FAILURE into retry/give-up/expire from history + policy).
                    if current_matched and target_matched:
                        outcome = HandlerOutcome.SUCCESS
                        message = "replica counts match desired"
                    else:
                        outcome = HandlerOutcome.FAILURE
                        message = "reconciling replica counts toward desired"
            scaling_decisions.append(
                GroupScalingDecision(
                    replica_group_id=view.group_id,
                    deployment_id=view.deployment_id,
                    handler_outcome=outcome,
                    message=message,
                    from_status=view.scaling_status,
                    prior_history=view.last_history,
                    handler_options=view.handler_options,
                )
            )

        return GroupScalingReconcileResult(
            create_instructions=create_instructions,
            drain_instructions=drain_instructions,
            scaling_decisions=scaling_decisions,
            processed=len(reconcile_info.views),
            failed=0,
        )

    @override
    async def post_process(self, result: GroupScalingReconcileResult) -> None:
        pass
