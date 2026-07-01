"""Group scaling applier: for each group, read its current status from the view, map the
handler's result to a target status via the stage's ``transitions``, and record the
handler-supplied message in history. All values come from metadata or data — none are
hardcoded here. The merge-vs-insert decision is the ops layer's job."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.deployment.types import (
    ReplicaGroupHandlerCategory,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment.updaters.replica_group import (
    ReplicaGroupScalingUpdaterSpec,
)
from ai.backend.manager.repositories.replica_group.repository import ReplicaGroupRepository
from ai.backend.manager.repositories.replica_group.types import (
    ReplicaGroupReconcileTransition,
    ReplicaGroupScalingReconcileApply,
)
from ai.backend.manager.repositories.scheduling_history.creators import (
    ReplicaGroupHistoryCreatorSpec,
)
from ai.backend.manager.sokovan.deployment.group.categories import GroupReconcileKind
from ai.backend.manager.sokovan.deployment.group.scaling.types import (
    GroupScalingDecision,
    GroupScalingReconcileResult,
    GroupScalingTargetStatuses,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerApplier, ReconcilerApplyInput
from ai.backend.manager.sokovan.recorder.utils import extract_sub_steps_for_entity
from ai.backend.manager.types import OptionalState

_ScalingApplyInput = ReconcilerApplyInput[
    GroupScalingReconcileResult,
    ReplicaGroupHandlerCategory,
    GroupReconcileKind,
    GroupScalingTargetStatuses,
    ReplicaGroupScalingStatus,
]


class GroupScalingApplier(
    ReconcilerApplier[
        GroupScalingReconcileResult,
        ReplicaGroupHandlerCategory,
        GroupReconcileKind,
        GroupScalingTargetStatuses,
        ReplicaGroupScalingStatus,
    ]
):
    _replica_group_repository: ReplicaGroupRepository

    def __init__(self, replica_group_repository: ReplicaGroupRepository) -> None:
        self._replica_group_repository = replica_group_repository

    @override
    async def apply(self, apply_input: _ScalingApplyInput) -> None:
        transitions = [
            self._build_transition(decision, apply_input)
            for decision in apply_input.result.scaling_decisions
        ]
        apply = ReplicaGroupScalingReconcileApply(
            create_instructions=apply_input.result.create_instructions,
            drain_instructions=apply_input.result.drain_instructions,
            transitions=transitions,
        )
        await self._replica_group_repository.apply_scaling_reconcile(apply)

    def _build_transition(
        self,
        decision: GroupScalingDecision,
        apply_input: _ScalingApplyInput,
    ) -> ReplicaGroupReconcileTransition:
        metadata = apply_input.metadata
        # The coordinator already classified the handler outcome into the final result.
        result = apply_input.classified[decision.replica_group_id]
        # No mapped target -> no status change this tick (to_status stays None).
        target_status = metadata.transitions.get(result)
        status_updater: Updater[ReplicaGroupRow] | None = None
        to_status: str | None = None
        if target_status is not None:
            status_updater = Updater(
                spec=ReplicaGroupScalingUpdaterSpec(
                    scaling_status=OptionalState.update(target_status)
                ),
                pk_value=decision.replica_group_id,
            )
            to_status = target_status.value
        return ReplicaGroupReconcileTransition(
            history_spec=ReplicaGroupHistoryCreatorSpec(
                replica_group_id=decision.replica_group_id,
                deployment_id=decision.deployment_id,
                category=metadata.category,
                phase=metadata.phase,
                result=result,
                message=decision.message,
                error_code=decision.error_code,
                from_status=decision.from_status.value,
                to_status=to_status,
                sub_steps=extract_sub_steps_for_entity(
                    decision.replica_group_id, apply_input.records
                ),
            ),
            status_updater=status_updater,
        )
