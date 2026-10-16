from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.resource_group.purgers import ResourceGroupPurger
from ai.backend.manager.models.resource_group.row import ResourceGroupRow


@dataclass(frozen=True)
class PartialBulkPurgeResourceGroupsAction(
    PartialBulkPurgeEntityOpsAction[ResourceGroupRow, ResourceGroupData]
):
    """Remove the named resource groups, answering for each one."""

    ids: Sequence[ResourceGroupID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_resource_groups"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, ResourceGroupPurger]:
        return {
            resource_group_id: ResourceGroupPurger(resource_group_id=resource_group_id)
            for resource_group_id in self.ids
        }

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self,
            ids=[
                resource_group_id for resource_group_id in self.ids if resource_group_id in allowed
            ],
        )
