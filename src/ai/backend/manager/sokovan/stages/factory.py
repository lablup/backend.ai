"""Collect the per-stage registrations into a reconciler coordinator + task specs."""

from __future__ import annotations

from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.repositories.replica_group.repository import ReplicaGroupRepository
from ai.backend.manager.sokovan.reconciler.base import ReconcilerStageRunner, ReconcilerTaskSpec
from ai.backend.manager.sokovan.reconciler.coordinator import ReconcilerCoordinator
from ai.backend.manager.sokovan.reconciler.flag import ValkeyReconcilerFlag
from ai.backend.manager.sokovan.stages.group_autoscale import build_group_autoscale_stage
from ai.backend.manager.sokovan.stages.group_draining import build_group_draining_stage
from ai.backend.manager.sokovan.stages.group_rolling import build_group_rolling_stage
from ai.backend.manager.sokovan.stages.group_scaling import build_group_scaling_stage
from ai.backend.manager.sokovan.stages.idle_check import build_idle_check_stage
from ai.backend.manager.types import DistributedLockFactory


def build_reconciler_coordinator(
    *,
    replica_group_repository: ReplicaGroupRepository,
    valkey_schedule: ValkeyScheduleClient,
    lock_factory: DistributedLockFactory,
    config_provider: ManagerConfigProvider,
) -> tuple[ReconcilerCoordinator, list[ReconcilerTaskSpec]]:
    registrations = [
        build_group_scaling_stage(replica_group_repository),
        build_group_rolling_stage(replica_group_repository),
        build_group_draining_stage(replica_group_repository),
        build_group_autoscale_stage(replica_group_repository),
        build_idle_check_stage(),
    ]
    stages: dict[str, ReconcilerStageRunner] = {}
    task_specs: list[ReconcilerTaskSpec] = []
    for registration in registrations:
        stages[registration.reconcile_type] = registration.stage
        task_specs.append(registration.task_spec)
    coordinator = ReconcilerCoordinator(
        stages=stages,
        lock_factory=lock_factory,
        config_provider=config_provider,
        flags=ValkeyReconcilerFlag(valkey_schedule),
    )
    return coordinator, task_specs
