from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.resource_allocation.types import ResourceGroupUsageData


@dataclass(frozen=True)
class GetResourceGroupUsageAction(BaseSingleEntityAction):
    """Read what a resource group is currently using."""

    resource_group_id: ResourceGroupID
    resource_group_name: ResourceGroupName

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.resource_group_id

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_resource_group_usage"


@dataclass(frozen=True)
class GetResourceGroupUsageActionResult:
    usage: ResourceGroupUsageData
