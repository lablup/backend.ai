from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import ClusterMode
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.dry_run import KernelDryRunResult, KernelDryRunSpec


@dataclass(frozen=True)
class DryRunScheduleAction(BaseAction):
    """Dry-run a session's scheduling against a resource group without provisioning.

    The fields mirror the scheduler's selection criteria so the real selector can
    be driven directly: ``cluster_mode`` decides whether kernel slots are summed
    onto a single node (SINGLE_NODE) or placed individually (MULTI_NODE).
    """

    kernels: list[KernelDryRunSpec]
    cluster_mode: ClusterMode
    resource_group_id: ResourceGroupID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.SESSION

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass(frozen=True)
class DryRunScheduleActionResult(BaseActionResult):
    kernel_results: list[KernelDryRunResult]

    @override
    def entity_id(self) -> str | None:
        return None
