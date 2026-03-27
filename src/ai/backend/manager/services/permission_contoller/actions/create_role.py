from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.object_permission import (
    ObjectPermissionCreateInputBeforeRoleCreation,
)
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.permission_contoller.actions.base import RoleAction


@dataclass
class CreateRoleAction(RoleAction):
    creator: Creator[RoleRow]
    object_permissions: Sequence[ObjectPermissionCreateInputBeforeRoleCreation] = field(
        default_factory=tuple
    )

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateRoleActionResult(BaseActionResult):
    data: RoleData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id) if self.data else None
