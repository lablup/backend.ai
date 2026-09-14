import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.role import (
    BulkRoleAssignmentResultData,
)
from ai.backend.manager.services.rbac.actions.role.base import RoleAction


@dataclass
class BulkAssignRoleAction(RoleAction):
    role_id: RoleID
    user_ids: Sequence[UserID]
    granted_by: UserID | None = field(default=None)
    project_id: uuid.UUID | None = field(default=None)

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class BulkAssignRoleActionResult(BaseActionResult):
    data: BulkRoleAssignmentResultData

    @override
    def entity_id(self) -> str | None:
        return None
