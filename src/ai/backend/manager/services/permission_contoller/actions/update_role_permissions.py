from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.role import RoleDetailData, RolePermissionsUpdateInput


@dataclass
class UpdateRolePermissionsAction(BaseAction):
    input_data: RolePermissionsUpdateInput

    @override
    def entity_id(self) -> str | None:
        return str(self.input_data.role_id)

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.ROLE

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateRolePermissionsActionResult(BaseActionResult):
    role: RoleDetailData

    @override
    def entity_id(self) -> str | None:
        return str(self.role.id)
