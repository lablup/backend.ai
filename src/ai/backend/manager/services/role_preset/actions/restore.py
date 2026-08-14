from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.actions.v2.ops.base import RestorePartialBulkOpsAction
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import (
    RolePresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.updaters import (
    RolePresetRestoreUpdater,
)


@dataclass
class BulkRestoreRolePresetsAction(RestorePartialBulkOpsAction[RolePresetRow, RolePresetData]):
    """Undo the soft delete on the named presets, answering for each one."""

    ids: Sequence[RolePresetID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_restore_role_presets"

    @override
    def entity_ids(self) -> Sequence[EntityID]:
        return tuple(self.ids)

    @override
    def to_updaters(self) -> Mapping[EntityID, RolePresetRestoreUpdater]:
        return {preset_id: RolePresetRestoreUpdater(preset_id=preset_id) for preset_id in self.ids}
