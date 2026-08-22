from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.resource_group import (
    RESOURCE_GROUP_ENTITY_TYPE,
    ResourceGroupID,
    ResourceGroupName,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.models.resource_group.lookups import ResourceGroupNameLookup
from ai.backend.manager.models.resource_group.row import ResourceGroupRow


@dataclass(frozen=True)
class ResourceGroupNameKey(LookupKey):
    """The name a caller passes instead of the resource group's id."""

    name: ResourceGroupName

    @override
    def kind(self) -> str:
        return "resource_group_name"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"name": str(self.name)}


@dataclass
class LookupResourceGroupAction(LookupEntityOpsAction[ResourceGroupRow, ResourceGroupID]):
    """Resolve a resource group's name into the group it names."""

    name: ResourceGroupName

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RESOURCE_GROUP_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_resource_group"

    @override
    def lookup_key(self) -> ResourceGroupNameKey:
        return ResourceGroupNameKey(name=self.name)

    @override
    def to_lookup(self) -> ResourceGroupNameLookup:
        return ResourceGroupNameLookup(name=self.name)
