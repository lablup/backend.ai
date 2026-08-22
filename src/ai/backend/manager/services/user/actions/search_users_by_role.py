from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.user.searchers import UserSearcher

__all__ = ("SearchUsersByRoleAction",)


@dataclass(frozen=True)
class SearchUsersByRoleAction(SearchGlobalOpsAction[UserRow, UserData]):
    """Page through the users a role is assigned to.

    A role is not a scope users sit under, so the assignment is a condition on the
    searcher rather than a scope the read is restricted to.
    """

    role_id: UUID
    searcher: UserSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_users_by_role"

    @override
    def to_searcher(self) -> UserSearcher:
        return self.searcher
