from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_allocation.types import ScopeUsageData
from ai.backend.manager.services.resource_allocation.actions.base import (
    ResourceAllocationAction,
)


@dataclass
class GetKeypairUsageAction(ResourceAllocationAction):
    access_key: AccessKey
    resource_policy: Mapping[str, Any]

    @override
    def entity_id(self) -> str | None:
        return str(self.access_key)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetKeypairUsageActionResult(BaseActionResult):
    usage: ScopeUsageData

    @override
    def entity_id(self) -> str | None:
        return None
