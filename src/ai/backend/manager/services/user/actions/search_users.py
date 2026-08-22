from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.user.searchers import UserSearcher

__all__ = ("GlobalSearchUsersAction",)


@dataclass(frozen=True)
class GlobalSearchUsersAction(SearchGlobalOpsAction[UserRow, UserData]):
    """Page through every user in the installation."""

    searcher: UserSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_users"

    @override
    def to_searcher(self) -> UserSearcher:
        return self.searcher
