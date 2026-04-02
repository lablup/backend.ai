from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_allocation.types import ScopeUsageData
from ai.backend.manager.services.resource_allocation.actions.base import (
    ResourceAllocationAction,
)


@dataclass
class GetProjectUsageAction(ResourceAllocationAction):
    project_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.project_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetProjectUsageActionResult(BaseActionResult):
    usage: ScopeUsageData

    @override
    def entity_id(self) -> str | None:
        return None
