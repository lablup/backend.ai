from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.queriers import RolePresetQuerier
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow


@dataclass
class GetRolePresetAction(GetSingleEntityOpsAction[RolePresetRow, RolePresetData]):
    """Read one role preset."""

    preset_id: RolePresetID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_role_preset"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.preset_id

    @override
    def to_querier(self) -> RolePresetQuerier:
        return RolePresetQuerier(preset_id=self.preset_id)
