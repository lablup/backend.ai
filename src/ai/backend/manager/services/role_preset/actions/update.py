from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.rbac_models.role_preset.updaters import RolePresetUpdater


@dataclass
class UpdateRolePresetAction(UpdateSingleEntityOpsAction[RolePresetRow, RolePresetData]):
    """Edit a preset's declaration. The soft-delete state is not reachable here."""

    updater: RolePresetUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_role_preset"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.preset_id

    @override
    def to_updater(self) -> RolePresetUpdater:
        return self.updater
