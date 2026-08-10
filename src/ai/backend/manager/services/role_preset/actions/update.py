from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import UpdateGlobalOpsAction
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.repositories.role_preset.updaters import RolePresetUpdater
from ai.backend.manager.services.role_preset.actions.base import RoleNameTemplateCarrier


@dataclass
class UpdateRolePresetAction(
    UpdateGlobalOpsAction[RolePresetRow, RolePresetData], RoleNameTemplateCarrier
):
    """Edit a preset's declaration. The soft-delete state is not reachable here."""

    updater: RolePresetUpdater

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_role_preset"

    @override
    def role_name_template(self) -> str | None:
        template = self.updater.role_name_template
        return template.value() if template.is_update() else None

    @override
    def to_updater(self) -> RolePresetUpdater:
        return self.updater
