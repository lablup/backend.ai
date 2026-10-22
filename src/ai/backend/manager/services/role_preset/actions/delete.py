from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import DeleteSingleEntityOpsAction
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.specs.soft_delete import SoftDeleteUpdater


@dataclass(frozen=True)
class DeleteRolePresetAction(DeleteSingleEntityOpsAction[RolePresetRow, RolePresetData]):
    """Mark one preset deleted."""

    updater: SoftDeleteUpdater[RolePresetRow, RolePresetData]

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.target_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_role_preset"

    @override
    def to_updater(self) -> SoftDeleteUpdater[RolePresetRow, RolePresetData]:
        return self.updater
