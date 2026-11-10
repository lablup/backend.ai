from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.relation.base import BaseRelationAction
from ai.backend.manager.data.permission.role import (
    BulkRoleRevocationResultData,
    BulkUserRoleRevocationInput,
)


@dataclass(frozen=True)
class BulkRevokeRoleAction(BaseRelationAction):
    """Take one role back from several users, each user a pair with that role."""

    input: BulkUserRoleRevocationInput

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_revoke_role"

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return [
            RoleID(self.input.role_id),
            *(UserID(user_id) for user_id in self.input.user_ids),
        ]


@dataclass(frozen=True)
class BulkRevokeRoleActionResult:
    data: BulkRoleRevocationResultData
