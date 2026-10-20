from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset.queriers import BulkResourcePresetQuerier
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow


@dataclass
class BulkGetResourcePresetsAction(
    PartialBulkGetEntityOpsAction[ResourcePresetRow, ResourcePresetData]
):
    """Read the resource presets the caller named, one permission check per preset."""

    ids: Sequence[ResourcePresetID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_resource_presets"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkResourcePresetQuerier:
        return BulkResourcePresetQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
