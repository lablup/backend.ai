from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.types import ClusterMode
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.compute_schedule import (
    ComputeScheduleResult,
)
from ai.backend.manager.data.session.draft import KernelResourceInput


@dataclass(frozen=True)
class ComputeScheduleAction(BaseAction):
    """Compute a session's scheduling against a resource group without provisioning.

    The fields mirror the scheduler's selection criteria so the real selector can
    be driven directly: ``cluster_mode`` decides whether kernel slots are summed
    onto a single node (SINGLE_NODE) or placed individually (MULTI_NODE).

    Each kernel is an unresolved ``KernelResourceInput``; the result list
    corresponds positionally, so callers match results to kernels by index.
    """

    kernels: list[KernelResourceInput]
    cluster_mode: ClusterMode
    resource_group_id: ResourceGroupID
    user_uuid: UUID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.RESOURCE_GROUP

    @override
    def entity_id(self) -> str | None:
        return str(self.resource_group_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass(frozen=True)
class ComputeScheduleActionResult(BaseActionResult):
    result: ComputeScheduleResult

    @override
    def entity_id(self) -> str | None:
        return None
