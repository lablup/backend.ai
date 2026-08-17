from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE, RolePresetID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import DeletePartialBulkOpsAction
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import (
    RolePresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.updaters import (
    RolePresetSoftDeleteUpdater,
)


@dataclass
class BulkDeleteRolePresetsAction(DeletePartialBulkOpsAction[RolePresetRow, RolePresetData]):
    """Mark the named presets deleted, answering for each one."""

    ids: Sequence[RolePresetID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_delete_role_presets"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, RolePresetSoftDeleteUpdater]:
        return {
            preset_id: RolePresetSoftDeleteUpdater(preset_id=preset_id) for preset_id in self.ids
        }
