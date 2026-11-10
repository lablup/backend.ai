from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.resource_group.queriers import BulkResourceGroupQuerier
from ai.backend.manager.models.resource_group.row import ResourceGroupRow


@dataclass
class BulkGetResourceGroupsAction(
    PartialBulkGetEntityOpsAction[ResourceGroupRow, ResourceGroupData]
):
    """Read the resource groups the caller named, answering for each id."""

    ids: Sequence[ResourceGroupID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_resource_groups"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkResourceGroupQuerier:
        return BulkResourceGroupQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
