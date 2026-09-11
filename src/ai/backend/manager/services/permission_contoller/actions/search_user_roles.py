from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.permission.role import AssignedUserData
from ai.backend.manager.models.rbac_models.user_role.row import UserRoleRow
from ai.backend.manager.models.rbac_models.user_role.scopes import UserRoleOperationScope
from ai.backend.manager.models.rbac_models.user_role.searchers import UserRoleSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchUserRolesAction(BulkScopedSearchOpsAction[UserRoleRow, AssignedUserData]):
    """Page through the roles the named users hold, combined with OR."""

    user_ids: Sequence[UserID]
    searcher: UserRoleSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_user_roles"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return list(self.user_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [UserRoleOperationScope(user_id=user_id) for user_id in self.user_ids]

    @override
    def to_searcher(self) -> UserRoleSearcher:
        return self.searcher
