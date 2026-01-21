from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseAction, BaseActionResult
from ai.backend.manager.data.permission.role import RoleDetailData, RolePermissionsUpdateInput


@dataclass
class UpdateRolePermissionsAction(BaseAction):
    input_data: RolePermissionsUpdateInput

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.input_data.role_id)

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "role"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update_permissions"


@dataclass
class UpdateRolePermissionsActionResult(BaseActionResult):
    role: RoleDetailData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.role.id)
