from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.data.resource_allocation.types import ResourceGroupUsageData


@dataclass(frozen=True)
class GetResourceGroupUsageAction(BaseGlobalAction):
    """Read what a resource group is currently using.

    Global until a resource group name resolves to its id: naming the group as the
    entity needs that lookup, which does not exist yet.
    """

    rg_name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RESOURCE_GROUP_ENTITY_TYPE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_get_resource_group_usage"


@dataclass(frozen=True)
class GetResourceGroupUsageActionResult:
    usage: ResourceGroupUsageData
