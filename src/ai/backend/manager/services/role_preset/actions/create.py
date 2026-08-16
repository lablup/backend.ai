from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role_preset import ROLE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalWithFieldsOpsAction
from ai.backend.manager.data.role_preset.types import (
    RolePermissionPresetData,
    RolePresetData,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.creators import (
    RolePermissionPresetCreator,
)
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.creators import RolePresetCreator
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.services.role_preset.actions.base import RoleNameTemplateCarrier


@dataclass
class CreateRolePresetAction(
    CreateGlobalWithFieldsOpsAction[
        RolePresetRow, RolePresetData, RolePermissionPresetRow, RolePermissionPresetData
    ],
    RoleNameTemplateCarrier,
):
    """Register a role preset together with the permissions it grants.

    One action so the preset and its permission rows share a transaction: a preset
    surviving a failed permission row would grant less than it declares.
    """

    creator: RolePresetCreator
    permission_creators: Sequence[RolePermissionPresetCreator]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ROLE_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_role_preset"

    @override
    def role_name_template(self) -> str | None:
        return self.creator.role_name_template

    @override
    def to_creator(self) -> RolePresetCreator:
        return self.creator

    @override
    def to_field_creators(self) -> Sequence[RolePermissionPresetCreator]:
        return self.permission_creators
