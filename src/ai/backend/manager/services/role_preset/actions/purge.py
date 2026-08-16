from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE, RolePresetID
from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.purgers import RolePresetPurger
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow


@dataclass
class PurgeRolePresetAction(PurgeEntityOpsAction[RolePresetRow, RolePresetData]):
    """Remove a preset for good; its permission rows follow by FK cascade."""

    preset_id: RolePresetID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_role_preset"

    @override
    def entity_id(self) -> EntityID:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> RolePresetPurger:
        return RolePresetPurger(preset_id=self.preset_id)
