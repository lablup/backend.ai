from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.role_preset.types import (
    RolePermissionPresetData,
    RolePresetData,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.role_preset.creators import (
    RolePermissionPresetDependentCreatorSpec,
)
from ai.backend.manager.services.role_preset.actions.base import RolePresetAction


@dataclass
class CreateRolePresetAction(RolePresetAction):
    creator: Creator[RolePresetRow]
    permission_creator_specs: Sequence[RolePermissionPresetDependentCreatorSpec]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateRolePresetActionResult(BaseActionResult):
    preset: RolePresetData
    permissions: list[RolePermissionPresetData]

    @override
    def entity_id(self) -> str | None:
        return str(self.preset.id)
