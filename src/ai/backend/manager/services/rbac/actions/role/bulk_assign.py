import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction
from ai.backend.manager.data.permission.role import BulkRoleAssignmentResultData


@dataclass(frozen=True)
class BulkAssignRoleAction(BaseRelationAction):
    """Grant one role to several users, each user a pair with that role."""

    role_id: RoleID
    user_ids: Sequence[UserID]
    granted_by: UserID | None = field(default=None)
    project_id: uuid.UUID | None = field(default=None)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_assign_role"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [self.role_id, *self.user_ids]


@dataclass(frozen=True)
class BulkAssignRoleActionResult:
    data: BulkRoleAssignmentResultData
