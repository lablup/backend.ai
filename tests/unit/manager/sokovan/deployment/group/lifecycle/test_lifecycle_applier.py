"""Wiring tests for the group lifecycle applier: which transitions carry a session
group retention boundary into the repository."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from unittest.mock import AsyncMock, MagicMock

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerOptions,
    ReplicaGroupHandlerCategory,
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.data.reconciler.types import HandlerOutcome
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.repositories.replica_group.repository import ReplicaGroupRepository
from ai.backend.manager.sokovan.deployment.group.categories import GroupReconcileKind
from ai.backend.manager.sokovan.deployment.group.lifecycle.applier import GroupLifecycleApplier
from ai.backend.manager.sokovan.deployment.group.lifecycle.types import (
    GroupLifecycleDecision,
    GroupLifecycleReconcileResult,
    GroupLifecycleTargetStatuses,
    GroupReconcileStatus,
)
from ai.backend.manager.sokovan.reconciler.base import (
    ReconcilerApplyInput,
    ReconcilerStageMetadata,
)

_LifecycleApplyInput = ReconcilerApplyInput[
    GroupLifecycleReconcileResult,
    ReplicaGroupHandlerCategory,
    GroupReconcileKind,
    GroupLifecycleTargetStatuses,
    GroupReconcileStatus,
]

_STAGE_TRANSITIONS: Mapping[SchedulingResult, GroupReconcileStatus] = {
    SchedulingResult.SUCCESS: GroupReconcileStatus(
        lifecycle=ReplicaGroupLifecycle.DRAINED,
        scaling_status=ReplicaGroupScalingStatus.STABLE,
    ),
    SchedulingResult.NEED_RETRY: GroupReconcileStatus(
        lifecycle=ReplicaGroupLifecycle.DRAINING,
        scaling_status=ReplicaGroupScalingStatus.SCALING,
    ),
}


def _decision(group_id: ReplicaGroupID) -> GroupLifecycleDecision:
    return GroupLifecycleDecision(
        replica_group_id=group_id,
        deployment_id=DeploymentID(uuid.uuid4()),
        handler_outcome=HandlerOutcome.SUCCESS,
        message="",
        from_lifecycle=ReplicaGroupLifecycle.DRAINING,
        next_desired_current_replica_count=0,
        next_desired_target_replica_count=0,
        prior_history=None,
        handler_options=DeploymentHandlerOptions(),
    )


def _apply_input(
    decisions: Mapping[ReplicaGroupID, SchedulingResult],
    transitions: Mapping[SchedulingResult, GroupReconcileStatus] = _STAGE_TRANSITIONS,
) -> _LifecycleApplyInput:
    return ReconcilerApplyInput(
        result=GroupLifecycleReconcileResult(
            lifecycle_decisions=[_decision(group_id) for group_id in decisions]
        ),
        records={},
        classified={group_id: result for group_id, result in decisions.items()},
        metadata=ReconcilerStageMetadata(
            category=ReplicaGroupHandlerCategory.LIFECYCLE,
            kind=GroupReconcileKind.GROUP,
            target_statuses=GroupLifecycleTargetStatuses(
                lifecycles=frozenset({ReplicaGroupLifecycle.DRAINING}),
                scaling_statuses=frozenset({ReplicaGroupScalingStatus.STABLE}),
            ),
            name="group_draining_reconcile",
            phase="group_draining",
            lock_id=None,
            transitions=transitions,
        ),
    )


async def test_a_drained_transition_carries_the_group_for_a_retention_boundary() -> None:
    group_id = ReplicaGroupID(uuid.uuid4())
    repository = MagicMock(spec=ReplicaGroupRepository)
    repository.apply_lifecycle_reconcile = AsyncMock()

    await GroupLifecycleApplier(repository).apply(
        _apply_input({group_id: SchedulingResult.SUCCESS})
    )

    apply = repository.apply_lifecycle_reconcile.await_args.args[0]
    assert apply.terminal_group_ids == [group_id]


async def test_a_retried_draining_step_carries_no_boundary() -> None:
    group_id = ReplicaGroupID(uuid.uuid4())
    repository = MagicMock(spec=ReplicaGroupRepository)
    repository.apply_lifecycle_reconcile = AsyncMock()

    await GroupLifecycleApplier(repository).apply(
        _apply_input({group_id: SchedulingResult.NEED_RETRY})
    )

    apply = repository.apply_lifecycle_reconcile.await_args.args[0]
    assert apply.terminal_group_ids == []


async def test_a_failed_transition_carries_the_group_for_a_retention_boundary() -> None:
    group_id = ReplicaGroupID(uuid.uuid4())
    repository = MagicMock(spec=ReplicaGroupRepository)
    repository.apply_lifecycle_reconcile = AsyncMock()
    transitions = {
        SchedulingResult.SUCCESS: GroupReconcileStatus(
            lifecycle=ReplicaGroupLifecycle.FAILED,
            scaling_status=ReplicaGroupScalingStatus.STABLE,
        )
    }

    await GroupLifecycleApplier(repository).apply(
        _apply_input({group_id: SchedulingResult.SUCCESS}, transitions)
    )

    apply = repository.apply_lifecycle_reconcile.await_args.args[0]
    assert apply.terminal_group_ids == [group_id]


async def test_only_the_terminal_group_of_a_mixed_tick_carries_a_boundary() -> None:
    drained_id = ReplicaGroupID(uuid.uuid4())
    retried_id = ReplicaGroupID(uuid.uuid4())
    repository = MagicMock(spec=ReplicaGroupRepository)
    repository.apply_lifecycle_reconcile = AsyncMock()

    await GroupLifecycleApplier(repository).apply(
        _apply_input({
            drained_id: SchedulingResult.SUCCESS,
            retried_id: SchedulingResult.NEED_RETRY,
        })
    )

    apply = repository.apply_lifecycle_reconcile.await_args.args[0]
    assert apply.terminal_group_ids == [drained_id]
    by_id = {
        t.status_updater.target_id_value(): t
        for t in apply.transitions
        if t.status_updater is not None
    }
    drained_updater = by_id[drained_id].status_updater
    retried_updater = by_id[retried_id].status_updater
    assert drained_updater is not None and retried_updater is not None
    assert drained_updater.lifecycle.optional_value() is ReplicaGroupLifecycle.DRAINED
    assert retried_updater.lifecycle.optional_value() is ReplicaGroupLifecycle.DRAINING
