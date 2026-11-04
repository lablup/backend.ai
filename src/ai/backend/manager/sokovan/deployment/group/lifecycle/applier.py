"""Group lifecycle applier (rolling + draining): write each group's next desired counts +
scaling status and the coordinator-classified lifecycle transition, and record history.
No route create/drain here — the scaling reconcile fills routes to the new desired counts."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupHandlerCategory,
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.models.replica_group.updaters import ReplicaGroupLifecycleUpdater
from ai.backend.manager.models.replica_group_history.creators import (
    ReplicaGroupHistoryCreator,
)
from ai.backend.manager.repositories.replica_group.repository import ReplicaGroupRepository
from ai.backend.manager.repositories.replica_group.types import (
    ReplicaGroupLifecycleReconcileApply,
    ReplicaGroupReconcileTransition,
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
        transitions: list[ReplicaGroupReconcileTransition] = []
        terminal_group_ids: list[ReplicaGroupID] = []
        for decision in apply_input.result.lifecycle_decisions:
            target = apply_input.metadata.transitions.get(
                apply_input.classified[decision.replica_group_id]
            )
            transitions.append(self._build_transition(decision, target, apply_input))
            if target is not None and target.lifecycle in ReplicaGroupLifecycle.terminal_statuses():
                terminal_group_ids.append(decision.replica_group_id)
        await self._replica_group_repository.apply_lifecycle_reconcile(
            ReplicaGroupLifecycleReconcileApply(
                transitions=transitions,
                terminal_group_ids=terminal_group_ids,
            )
        )

    def _build_transition(
        self,
        decision: GroupLifecycleDecision,
        target: GroupReconcileStatus | None,
        apply_input: _LifecycleApplyInput,
    ) -> ReplicaGroupReconcileTransition:
        metadata = apply_input.metadata
        result = apply_input.classified[decision.replica_group_id]
        if target is not None:
            lifecycle_state = OptionalState.update(target.lifecycle)
            scaling_state = OptionalState.update(target.scaling_status)
            to_status = target.lifecycle.value
        else:
            lifecycle_state = OptionalState[ReplicaGroupLifecycle].nop()
            scaling_state = OptionalState[ReplicaGroupScalingStatus].nop()
            to_status = None
        updater = ReplicaGroupLifecycleUpdater(
            replica_group_id=decision.replica_group_id,
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
        )
        return ReplicaGroupReconcileTransition(
            deployment_id=decision.deployment_id,
            history_creator=ReplicaGroupHistoryCreator(
                replica_group_id=decision.replica_group_id,
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
