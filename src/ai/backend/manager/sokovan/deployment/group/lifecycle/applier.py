"""Group lifecycle applier (rolling + draining): write each group's next desired counts +
scaling status and the coordinator-classified lifecycle transition, and record history.
No route create/drain here — the scaling reconcile fills routes to the new desired counts."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.deployment.types import (
    ReplicaGroupHandlerCategory,
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.deployment.updaters.replica_group import (
    ReplicaGroupLifecycleUpdaterSpec,
)
from ai.backend.manager.repositories.replica_group.repository import ReplicaGroupRepository
from ai.backend.manager.repositories.replica_group.types import (
    ReplicaGroupLifecycleReconcileApply,
    ReplicaGroupReconcileTransition,
)
from ai.backend.manager.repositories.scheduling_history.creators import (
    ReplicaGroupHistoryCreatorSpec,
)
from ai.backend.manager.sokovan.deployment.group.categories import GroupReconcileKind
from ai.backend.manager.sokovan.deployment.group.lifecycle.types import (
    GroupLifecycleDecision,
    GroupLifecycleReconcileResult,
    GroupLifecycleTargetStatuses,
    GroupReconcileStatus,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerApplier, ReconcilerApplyInput
from ai.backend.manager.sokovan.recorder.utils import extract_sub_steps_for_entity
from ai.backend.manager.types import OptionalState

_LifecycleApplyInput = ReconcilerApplyInput[
    GroupLifecycleReconcileResult,
    ReplicaGroupHandlerCategory,
    GroupReconcileKind,
    GroupLifecycleTargetStatuses,
    GroupReconcileStatus,
]


class GroupLifecycleApplier(
    ReconcilerApplier[
        GroupLifecycleReconcileResult,
        ReplicaGroupHandlerCategory,
        GroupReconcileKind,
        GroupLifecycleTargetStatuses,
        GroupReconcileStatus,
    ]
):
    _replica_group_repository: ReplicaGroupRepository

    def __init__(self, replica_group_repository: ReplicaGroupRepository) -> None:
        self._replica_group_repository = replica_group_repository

    @override
    async def apply(self, apply_input: _LifecycleApplyInput) -> None:
        transitions = [
            self._build_transition(decision, apply_input)
            for decision in apply_input.result.lifecycle_decisions
        ]
        await self._replica_group_repository.apply_lifecycle_reconcile(
            ReplicaGroupLifecycleReconcileApply(transitions=transitions)
        )

    def _build_transition(
        self,
        decision: GroupLifecycleDecision,
        apply_input: _LifecycleApplyInput,
    ) -> ReplicaGroupReconcileTransition:
        metadata = apply_input.metadata
        result = apply_input.classified[decision.replica_group_id]
        target = metadata.transitions.get(result)
        if target is not None:
            lifecycle_state = OptionalState.update(target.lifecycle)
            scaling_state = OptionalState.update(target.scaling_status)
            to_status = target.lifecycle.value
        else:
            lifecycle_state = OptionalState[ReplicaGroupLifecycle].nop()
            scaling_state = OptionalState[ReplicaGroupScalingStatus].nop()
            to_status = None
        updater = Updater(
            spec=ReplicaGroupLifecycleUpdaterSpec(
                lifecycle=lifecycle_state,
                desired_current_replica_count=OptionalState.update(
                    decision.next_desired_current_replica_count
                ),
                desired_target_replica_count=OptionalState.update(
                    decision.next_desired_target_replica_count
                ),
                scaling_status=scaling_state,
                current_revision_id=decision.next_current_revision_id,
                target_revision_id=decision.next_target_revision_id,
            ),
            pk_value=decision.replica_group_id,
        )
        return ReplicaGroupReconcileTransition(
            history_spec=ReplicaGroupHistoryCreatorSpec(
                replica_group_id=decision.replica_group_id,
                deployment_id=decision.deployment_id,
                category=metadata.category,
                phase=metadata.phase,
                result=result,
                message=decision.message,
                error_code=decision.error_code,
                from_status=decision.from_lifecycle.value,
                to_status=to_status,
                sub_steps=extract_sub_steps_for_entity(
                    decision.replica_group_id, apply_input.records
                ),
            ),
            status_updater=updater,
        )
