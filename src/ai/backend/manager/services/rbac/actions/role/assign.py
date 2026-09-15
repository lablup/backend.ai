from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction
from ai.backend.manager.data.permission.role import (
    UserRoleAssignmentData,
    UserRoleAssignmentInput,
)


@dataclass(frozen=True)
class AssignRoleAction(BaseRelationAction):
    """Grant a role to a user, and place them on the project's roster with it."""

    input: UserRoleAssignmentInput

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "assign_role"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [RoleID(self.input.role_id), UserID(self.input.user_id)]


@dataclass(frozen=True)
class AssignRoleActionResult:
    data: UserRoleAssignmentData
