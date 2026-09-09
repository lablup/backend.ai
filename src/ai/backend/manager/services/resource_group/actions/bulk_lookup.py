from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import (
    ResourceGroupEntityType,
    ResourceGroupID,
    ResourceGroupName,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import BulkLookupEntityOpsAction
from ai.backend.manager.models.resource_group.lookups import ResourceGroupNamesLookup
from ai.backend.manager.services.resource_group.actions.lookup import ResourceGroupNameKey


@dataclass
class BulkLookupResourceGroupsAction(BulkLookupEntityOpsAction[ResourceGroupName, ResourceGroupID]):
    """Resolve several names into the resource groups they refer to.

    Every authenticated caller may resolve the names, as with the single lookup: the
    read that follows is checked against each resource group on its own.
    """

    names: Sequence[ResourceGroupName]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ResourceGroupEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_lookup_resource_groups"

    @override
    def keys(self) -> Sequence[ResourceGroupName]:
        return tuple(self.names)

    @override
    def to_lookup_key(self, key: ResourceGroupName) -> ResourceGroupNameKey:
        return ResourceGroupNameKey(name=key)

    @override
    def to_lookup(self) -> ResourceGroupNamesLookup:
        return ResourceGroupNamesLookup()
