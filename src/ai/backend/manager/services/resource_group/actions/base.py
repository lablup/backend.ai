from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import (
    RESOURCE_GROUP_ENTITY_TYPE,
    ResourceGroupID,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass(frozen=True)
class ResourceGroupAction(BaseSingleEntityAction):
    """Base for an operation on one resource group."""

    resource_group_id: ResourceGroupID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.resource_group_id


@dataclass(frozen=True)
class ResourceGroupGlobalAction(BaseGlobalAction):
    """Base for an operation that names no resource group."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RESOURCE_GROUP_ENTITY_TYPE
