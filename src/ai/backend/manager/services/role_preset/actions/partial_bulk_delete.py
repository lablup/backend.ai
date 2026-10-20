from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import DeletePartialBulkOpsAction
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import (
    RolePresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.searchable_fields import (
    RolePresetSearchableFields,
)
from ai.backend.manager.models.specs.soft_delete import SoftDeleteUpdater


@dataclass
class PartialBulkDeleteRolePresetsAction(DeletePartialBulkOpsAction[RolePresetRow, RolePresetData]):
    """Mark the named presets deleted, answering for each one."""

    ids: Sequence[RolePresetID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_delete_role_presets"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_updaters(
        self,
    ) -> Mapping[EntityIdentifier, SoftDeleteUpdater[RolePresetRow, RolePresetData]]:
        return {
            preset_id: SoftDeleteUpdater(
                target_row=RolePresetRow,
                target_column=RolePresetRow.id,
                target_id=preset_id,
                converter=RolePresetSearchableFields.own,
            )
            for preset_id in self.ids
        }

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
