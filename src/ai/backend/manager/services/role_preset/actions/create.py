from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.role_preset.types import RolePresetData
from ai.backend.manager.repositories.role_preset.creators import (
    RolePermissionPresetDependentCreatorSpec,
    RolePresetCreatorSpec,
)
from ai.backend.manager.services.role_preset.actions.base import RolePresetScopeAction


@dataclass
class CreateRolePresetAction(RolePresetScopeAction):
    creator_spec: RolePresetCreatorSpec
    permission_creator_specs: Sequence[RolePermissionPresetDependentCreatorSpec]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateRolePresetActionResult(BaseActionResult):
    preset: RolePresetData

    @override
    def entity_id(self) -> str | None:
        return str(self.preset.id)
