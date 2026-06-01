from collections.abc import Collection
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.user_role import RoleMappingData
from ai.backend.manager.repositories.permission_controller.role_manager import UserSystemRoleSpec
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class EnsureSystemRoleAction(RoleAction):
    """Ensure the SYSTEM role(s) for the given users exist (superadmin only)."""

    specs: Collection[UserSystemRoleSpec]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class EnsureSystemRoleActionResult(BaseActionResult):
    data: list[RoleMappingData]

    @override
    def entity_id(self) -> str | None:
        return None
