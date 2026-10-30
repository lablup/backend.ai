from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.role_preset import RolePresetEntityType
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import CreateEntityWithFieldsOpsAction
from ai.backend.manager.data.permission.global_entity import global_entity_id
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


@dataclass
class CreateRolePresetAction(
    CreateEntityWithFieldsOpsAction[
        RolePresetRow, RolePresetData, RolePermissionPresetRow, RolePermissionPresetData
    ]
):
    """Register a role preset together with the permissions it grants, in the global scope.

    One action so the preset and its permission rows share a transaction: a preset
    surviving a failed permission row would grant less than it declares.
    """

    creator: RolePresetCreator
    permission_creators: Sequence[RolePermissionPresetCreator]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RolePresetEntityType()

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (global_entity_id(GlobalEntityName.GLOBAL),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_role_preset"

    @override
    def to_creator(self) -> RolePresetCreator:
        return self.creator

    @override
    def to_field_creators(self) -> Sequence[RolePermissionPresetCreator]:
        return self.permission_creators
