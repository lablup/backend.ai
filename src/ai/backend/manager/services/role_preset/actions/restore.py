from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import RestoreSingleEntityOpsAction
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.role_preset.updaters import (
    RolePresetRestoreUpdater,
)


@dataclass(frozen=True)
class RestoreRolePresetAction(RestoreSingleEntityOpsAction[RolePresetRow, RolePresetData]):
    """Undo the soft delete on one preset."""

    updater: RolePresetRestoreUpdater

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.preset_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_role_preset"

    @override
    def to_updater(self) -> RolePresetRestoreUpdater:
        return self.updater
