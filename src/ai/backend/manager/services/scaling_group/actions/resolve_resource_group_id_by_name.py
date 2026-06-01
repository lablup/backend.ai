from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.identifier.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.scaling_group.actions.base import ScalingGroupAction


@dataclass(frozen=True)
class ResolveResourceGroupIDByNameAction(ScalingGroupAction):
    name: ResourceGroupName

    @override
    def entity_id(self) -> str | None:
        return str(self.name)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass(frozen=True)
class ResolveResourceGroupIDByNameActionResult(BaseActionResult):
    resource_group_id: ResourceGroupID

    @override
    def entity_id(self) -> str | None:
        return str(self.resource_group_id)
