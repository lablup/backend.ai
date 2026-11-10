from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdatePartialBulkOpsAction
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.resource_group.updaters import ResourceGroupUpdater


@dataclass(frozen=True)
class PartialBulkUpdateResourceGroupsAction(
    UpdatePartialBulkOpsAction[ResourceGroupRow, ResourceGroupData]
):
    """Edit the named resource groups, answering for each one."""

    updaters: Sequence[ResourceGroupUpdater]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_resource_groups"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.resource_group_id for updater in self.updaters)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, ResourceGroupUpdater]:
        return {updater.resource_group_id: updater for updater in self.updaters}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self,
            updaters=[updater for updater in self.updaters if updater.resource_group_id in allowed],
        )
