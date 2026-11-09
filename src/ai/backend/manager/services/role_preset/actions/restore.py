from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import RestoreSingleEntityOpsAction
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.specs.soft_delete import RestoreUpdater


@dataclass(frozen=True)
class RestoreRolePresetAction(RestoreSingleEntityOpsAction[RolePresetRow, RolePresetData]):
    """Undo the soft delete on one preset."""

    updater: RestoreUpdater[RolePresetRow, RolePresetData]

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.target_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "restore_role_preset"

    @override
    def to_updater(self) -> RestoreUpdater[RolePresetRow, RolePresetData]:
        return self.updater
