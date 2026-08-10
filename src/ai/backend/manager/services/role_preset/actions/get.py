from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.role_preset import RolePresetID
from ai.backend.manager.actions.v2.ops.base import GetGlobalOpsAction
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.repositories.role_preset.queriers import RolePresetQuerier


@dataclass
class GetRolePresetAction(GetGlobalOpsAction[RolePresetRow, RolePresetData]):
    """Read one role preset."""

    preset_id: RolePresetID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_role_preset"

    @override
    def to_querier(self) -> RolePresetQuerier:
        return RolePresetQuerier(preset_id=self.preset_id)
