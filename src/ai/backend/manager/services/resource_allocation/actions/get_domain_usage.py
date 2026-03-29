from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_allocation.types import ScopeUsageData
from ai.backend.manager.services.resource_allocation.actions.base import (
    ResourceAllocationAction,
)


@dataclass
class GetDomainUsageAction(ResourceAllocationAction):
    domain_name: str

    @override
    def entity_id(self) -> str | None:
        return self.domain_name

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetDomainUsageActionResult(BaseActionResult):
    usage: ScopeUsageData

    @override
    def entity_id(self) -> str | None:
        return None
